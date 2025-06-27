"""
CO2 질량 전달 컴포넌트 테스트 파일
- CO2_Air: CO2 농도 계산 테스트
- MC_ventilation2: 환기 CO2 전달 테스트  
- MC_AirCan: 작물 CO2 흡수 테스트
- PrescribedCO2Flow: 외부 CO2 주입 테스트
- PrescribedConcentration: 외부 CO2 농도 테스트
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib import font_manager, rc

# 한글 폰트 설정 (matplotlib에서 한글 표시를 위해)
plt.rcParams['font.family'] = 'Malgun Gothic'  # 윈도우 기본 한글 폰트
plt.rcParams['axes.unicode_minus'] = False     # 마이너스 기호 깨짐 방지

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# CO2 관련 컴포넌트들 import
from Flows.CO2MassTransfer.CO2_Air import CO2_Air
from Flows.CO2MassTransfer.MC_ventilation2 import MC_ventilation2
from Flows.CO2MassTransfer.MC_AirCan import MC_AirCan
from Flows.Sources.CO2.PrescribedCO2Flow import PrescribedCO2Flow
from Flows.Sources.CO2.PrescribedConcentration import PrescribedConcentration

class CO2MassTransferTester:
    """CO2 질량 전달 컴포넌트 테스트 클래스"""
    
    def __init__(self):
        """테스트 초기화"""
        self.test_results = {}
        self.dt = 60.0  # 60초 시간 간격
        self.simulation_time = 3600.0  # 1시간 시뮬레이션
        
    def test_co2_air(self):
        """CO2_Air 컴포넌트 테스트"""
        print("\n=== CO2_Air 컴포넌트 테스트 ===")
        
        # 테스트 케이스 1: 기본 초기화
        co2_air = CO2_Air(cap_CO2=3.8, CO2_start=800.0, steadystate=False)
        print(f"초기 CO2 농도: {co2_air.CO2:.1f} mg/m³ ({co2_air.CO2_ppm:.1f} ppm)")
        print(f"CO2 저장 용량: {co2_air.cap_CO2:.1f} m")
        
        # 테스트 케이스 2: CO2 주입 시뮬레이션
        print("\n--- CO2 주입 시뮬레이션 (7.5 mg/(m²·s)) ---")
        co2_air.MC_flow = 7.5  # 외부 CO2 주입
        
        co2_history = []
        time_history = []
        
        for i in range(int(self.simulation_time / self.dt)):
            time = i * self.dt
            co2_air.step(self.dt)
            
            if i % 10 == 0:  # 10분마다 기록
                co2_history.append(co2_air.CO2)
                time_history.append(time / 60)  # 분 단위
                print(f"시간: {time/60:.0f}분, CO2: {co2_air.CO2:.1f} mg/m³ ({co2_air.CO2_ppm:.1f} ppm)")
        
        # 결과 저장
        self.test_results['CO2_Air'] = {
            'initial_co2': 800.0,
            'final_co2': co2_air.CO2,
            'co2_increase': co2_air.CO2 - 800.0,
            'time_history': time_history,
            'co2_history': co2_history
        }
        
        print(f"\n결과: CO2 농도 증가량 = {co2_air.CO2 - 800.0:.1f} mg/m³")
        
    def test_mc_ventilation2(self):
        """MC_ventilation2 컴포넌트 테스트"""
        print("\n=== MC_ventilation2 컴포넌트 테스트 ===")
        
        # 테스트 케이스: 환기로 인한 CO2 전달
        mc_vent = MC_ventilation2(f_vent=0.01)  # 0.01 m³/(m²·s) 환기량
        
        # 포트 연결 설정
        mc_vent.port_a.CO2 = 1000.0  # 내부 CO2 농도 (mg/m³)
        mc_vent.port_b.CO2 = 430.0   # 외부 CO2 농도 (mg/m³)
        
        print(f"내부 CO2 농도: {mc_vent.port_a.CO2:.1f} mg/m³")
        print(f"외부 CO2 농도: {mc_vent.port_b.CO2:.1f} mg/m³")
        print(f"환기량: {mc_vent.f_vent:.3f} m³/(m²·s)")
        
        # CO2 전달 계산
        mc_flow = mc_vent.step()
        
        print(f"CO2 농도차 (dC): {mc_vent.dC:.1f} mg/m³")
        print(f"CO2 질량유량: {mc_flow:.3f} mg/(m²·s)")
        print(f"Port A MC_flow: {mc_vent.port_a.MC_flow:.3f} mg/(m²·s)")
        print(f"Port B MC_flow: {mc_vent.port_b.MC_flow:.3f} mg/(m²·s)")
        
        # 결과 저장
        self.test_results['MC_ventilation2'] = {
            'dC': mc_vent.dC,
            'mc_flow': mc_flow,
            'port_a_flow': mc_vent.port_a.MC_flow,
            'port_b_flow': mc_vent.port_b.MC_flow
        }
        
    def test_mc_aircan(self):
        """MC_AirCan 컴포넌트 테스트"""
        print("\n=== MC_AirCan 컴포넌트 테스트 ===")
        
        # 테스트 케이스: 작물 CO2 흡수
        mc_aircan = MC_AirCan(MC_AirCan=0.02)  # 0.02 mg/(m²·s) 작물 흡수
        
        print(f"작물 CO2 흡수량: {mc_aircan.MC_AirCan:.3f} mg/(m²·s)")
        
        # 포트 연결 및 계산
        mc_aircan.port.CO2 = 800.0  # 공기 CO2 농도
        mc_flow = mc_aircan.step()
        
        print(f"공기 CO2 농도: {mc_aircan.port.CO2:.1f} mg/m³")
        print(f"포트 MC_flow: {mc_flow:.3f} mg/(m²·s)")
        
        # 결과 저장
        self.test_results['MC_AirCan'] = {
            'mc_aircan': mc_aircan.MC_AirCan,
            'port_flow': mc_flow,
            'air_co2': mc_aircan.port.CO2
        }
        
    def test_prescribed_co2_flow(self):
        """PrescribedCO2Flow 컴포넌트 테스트"""
        print("\n=== PrescribedCO2Flow 컴포넌트 테스트 ===")
        
        # 테스트 케이스: 외부 CO2 주입
        co2_flow = PrescribedCO2Flow(phi_ExtCO2=27.0)  # 27 g/(m²·h)
        
        print(f"외부 CO2 소스 용량: {co2_flow.phi_ExtCO2:.1f} g/(m²·h)")
        
        # 제어 밸브 설정 (0.5 = 50% 개도)
        co2_flow.U_MCext = 0.5
        co2_flow.calculate()
        
        print(f"제어 밸브 개도: {co2_flow.U_MCext:.1f}")
        print(f"계산된 CO2 유량: {co2_flow.MC_flow:.3f} mg/(m²·s)")
        print(f"포트 MC_flow: {co2_flow.port.MC_flow:.3f} mg/(m²·s)")
        
        # 시간에 따른 변화 시뮬레이션
        print("\n--- 시간에 따른 CO2 주입 시뮬레이션 ---")
        flow_history = []
        time_history = []
        
        for i in range(int(self.simulation_time / self.dt)):
            time = i * self.dt
            co2_flow.step(self.dt)
            
            if i % 10 == 0:  # 10분마다 기록
                flow_history.append(co2_flow.MC_flow)
                time_history.append(time / 60)  # 분 단위
                print(f"시간: {time/60:.0f}분, CO2 유량: {co2_flow.MC_flow:.3f} mg/(m²·s)")
        
        # 결과 저장
        self.test_results['PrescribedCO2Flow'] = {
            'phi_ext_co2': co2_flow.phi_ExtCO2,
            'u_mcext': co2_flow.U_MCext,
            'mc_flow': co2_flow.MC_flow,
            'port_flow': co2_flow.port.MC_flow,
            'time_history': time_history,
            'flow_history': flow_history
        }
        
    def test_prescribed_concentration(self):
        """PrescribedConcentration 컴포넌트 테스트"""
        print("\n=== PrescribedConcentration 컴포넌트 테스트 ===")
        
        # 테스트 케이스: 외부 CO2 농도 설정
        co2_conc = PrescribedConcentration()
        
        # 외부 CO2 농도 설정 (430 ppm = 834.2 mg/m³)
        external_co2_ppm = 430.0
        external_co2_mgm3 = external_co2_ppm * 1.94
        
        co2_conc.CO2 = external_co2_mgm3
        co2_conc.calculate()
        
        print(f"외부 CO2 농도: {external_co2_ppm:.1f} ppm ({external_co2_mgm3:.1f} mg/m³)")
        print(f"설정된 CO2 농도: {co2_conc.CO2:.1f} mg/m³")
        
        # 포트 연결 테스트
        from Interfaces.CO2.CO2Port_b import CO2Port_b
        test_port = CO2Port_b()
        co2_conc.connect_port(test_port)
        co2_conc.calculate()
        
        print(f"포트 CO2 농도: {test_port.CO2:.1f} mg/m³")
        
        # 결과 저장
        self.test_results['PrescribedConcentration'] = {
            'external_co2_ppm': external_co2_ppm,
            'external_co2_mgm3': external_co2_mgm3,
            'port_co2': test_port.CO2
        }
        
    def test_integrated_system(self):
        """통합 시스템 테스트"""
        print("\n=== 통합 CO2 시스템 테스트 ===")
        
        # 컴포넌트 초기화
        co2_air = CO2_Air(cap_CO2=3.8, CO2_start=800.0, steadystate=False)
        mc_vent = MC_ventilation2(f_vent=0.01)
        mc_aircan = MC_AirCan(MC_AirCan=0.02)
        co2_flow = PrescribedCO2Flow(phi_ExtCO2=27.0)
        co2_conc = PrescribedConcentration()
        
        # 외부 CO2 농도 설정
        co2_conc.CO2 = 430.0 * 1.94  # 430 ppm
        co2_conc.calculate()
        
        # 포트 연결
        mc_vent.port_b.CO2 = co2_conc.CO2  # 외부 CO2 농도
        mc_aircan.port.CO2 = co2_air.CO2  # 공기 CO2 농도
        
        print("초기 상태:")
        print(f"  공기 CO2: {co2_air.CO2:.1f} mg/m³")
        print(f"  외부 CO2: {co2_conc.CO2:.1f} mg/m³")
        
        # 시뮬레이션
        co2_history = []
        time_history = []
        
        for i in range(int(self.simulation_time / self.dt)):
            time = i * self.dt
            
            # 1. 외부 CO2 주입
            co2_flow.U_MCext = 0.5
            co2_flow.calculate()
            
            # 2. 환기 CO2 전달
            mc_vent.port_a.CO2 = co2_air.CO2
            mc_vent.step()
            
            # 3. 작물 CO2 흡수
            mc_aircan.port.CO2 = co2_air.CO2
            mc_aircan.step()
            
            # 4. 공기 CO2 질량 균형
            co2_air.MC_flow = (
                + co2_flow.port.MC_flow      # 외부 주입
                + mc_vent.port_a.MC_flow     # 환기 배출
                + mc_aircan.port.MC_flow     # 작물 흡수
            )
            
            # 5. CO2 농도 업데이트
            co2_air.step(self.dt)
            
            if i % 10 == 0:  # 10분마다 기록
                co2_history.append(co2_air.CO2)
                time_history.append(time / 60)
                print(f"시간: {time/60:.0f}분, CO2: {co2_air.CO2:.1f} mg/m³")
        
        # 결과 저장
        self.test_results['IntegratedSystem'] = {
            'initial_co2': 800.0,
            'final_co2': co2_air.CO2,
            'co2_change': co2_air.CO2 - 800.0,
            'time_history': time_history,
            'co2_history': co2_history
        }
        
        print(f"\n결과: 최종 CO2 농도 = {co2_air.CO2:.1f} mg/m³ (변화량: {co2_air.CO2 - 800.0:.1f} mg/m³)")
        
    def plot_results(self):
        """테스트 결과 시각화"""
        print("\n=== 테스트 결과 시각화 ===")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('CO2 Mass Transfer Component Test Results', fontsize=16)
        
        # 1. CO2_Air 시뮬레이션 결과
        if 'CO2_Air' in self.test_results:
            ax1 = axes[0, 0]
            time_history = self.test_results['CO2_Air']['time_history']
            co2_history = self.test_results['CO2_Air']['co2_history']
            ax1.plot(time_history, co2_history, 'b-', linewidth=2)
            ax1.set_xlabel('Time (minutes)')
            ax1.set_ylabel('CO2 Concentration (mg/m³)')
            ax1.set_title('CO2_Air: CO2 Concentration Change')
            ax1.grid(True)
        
        # 2. PrescribedCO2Flow 시뮬레이션 결과
        if 'PrescribedCO2Flow' in self.test_results:
            ax2 = axes[0, 1]
            time_history = self.test_results['PrescribedCO2Flow']['time_history']
            flow_history = self.test_results['PrescribedCO2Flow']['flow_history']
            ax2.plot(time_history, flow_history, 'r-', linewidth=2)
            ax2.set_xlabel('Time (minutes)')
            ax2.set_ylabel('CO2 Injection Flow (mg/(m²·s))')
            ax2.set_title('PrescribedCO2Flow: CO2 Injection Flow')
            ax2.grid(True)
        
        # 3. 통합 시스템 결과
        if 'IntegratedSystem' in self.test_results:
            ax3 = axes[1, 0]
            time_history = self.test_results['IntegratedSystem']['time_history']
            co2_history = self.test_results['IntegratedSystem']['co2_history']
            ax3.plot(time_history, co2_history, 'g-', linewidth=2)
            ax3.set_xlabel('Time (minutes)')
            ax3.set_ylabel('CO2 Concentration (mg/m³)')
            ax3.set_title('Integrated System: CO2 Concentration Change')
            ax3.grid(True)
        
        # 4. 컴포넌트별 결과 요약
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        summary_text = "Test Results Summary:\n\n"
        
        if 'MC_ventilation2' in self.test_results:
            result = self.test_results['MC_ventilation2']
            summary_text += f"MC_ventilation2:\n"
            summary_text += f"  CO2 Concentration Change: {result['dC']:.1f} mg/m³\n"
            summary_text += f"  질량유량: {result['mc_flow']:.3f} mg/(m²·s)\n\n"
        
        if 'MC_AirCan' in self.test_results:
            result = self.test_results['MC_AirCan']
            summary_text += f"MC_AirCan:\n"
            summary_text += f"  작물 흡수량: {result['mc_aircan']:.3f} mg/(m²·s)\n\n"
        
        if 'PrescribedCO2Flow' in self.test_results:
            result = self.test_results['PrescribedCO2Flow']
            summary_text += f"PrescribedCO2Flow:\n"
            summary_text += f"  외부 주입량: {result['mc_flow']:.3f} mg/(m²·s)\n\n"
        
        if 'IntegratedSystem' in self.test_results:
            result = self.test_results['IntegratedSystem']
            summary_text += f"통합 시스템:\n"
            summary_text += f"  최종 CO2: {result['final_co2']:.1f} mg/m³\n"
            summary_text += f"  변화량: {result['co2_change']:.1f} mg/m³"
        
        ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace')
        
        plt.tight_layout()
        plt.savefig('co2_mass_transfer_test_results.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("Test results have been saved to 'co2_mass_transfer_test_results.png' file.")
        
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("CO2 Mass Transfer Component Test Start")
        print("=" * 50)
        
        try:
            self.test_co2_air()
            self.test_mc_ventilation2()
            self.test_mc_aircan()
            self.test_prescribed_co2_flow()
            self.test_prescribed_concentration()
            self.test_integrated_system()
            
            print("\n" + "=" * 50)
            print("All tests completed!")
            
            # 결과 시각화
            self.plot_results()
            
        except Exception as e:
            print(f"\nTest error: {str(e)}")
            import traceback
            traceback.print_exc()

def main():
    """메인 함수"""
    tester = CO2MassTransferTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 