#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Illumination 클래스 테스트 파일
HPS 램프의 인공 조명 복사 계산 검증
"""

import numpy as np
import matplotlib.pyplot as plt
from Components.Greenhouse.Illumination import Illumination

class TestIllumination:
    def __init__(self):
        # 테스트용 기본 매개변수
        self.A = 1000.0  # 온실 면적 [m²]
        self.p_el = 55.0  # 전력 밀도 [W/m²]
        self.LAI = 2.0    # 엽면적 지수
        
    def test_basic_initialization(self):
        """기본 초기화 테스트"""
        print("=== 기본 초기화 테스트 ===")
        
        illu = Illumination(
            power_input=True,  # 전력 밀도 직접 사용
            P_el=0.0,
            A=self.A,
            p_el=self.p_el,
            LAI=self.LAI
        )
        
        # 초기값 확인
        print(f"초기 전력: {illu.W_el:.2f} W")
        print(f"초기 PAR: {illu.R_PAR:.2f} W/m²")
        print(f"초기 NIR: {illu.R_NIR:.2f} W/m²")
        print(f"초기 공기 흡수: {illu.R_IluAir_Glob.value:.2f} W/m²")
        
        assert illu.W_el == 0.0, "초기 전력은 0이어야 함"
        assert illu.R_PAR == 0.0, "초기 PAR은 0이어야 함"
        assert illu.R_NIR == 0.0, "초기 NIR은 0이어야 함"
        
        print("✓ 초기화 테스트 통과\n")
        return illu
    
    def test_switch_on_off(self):
        """스위치 on/off 테스트"""
        print("=== 스위치 on/off 테스트 ===")
        
        illu = Illumination(
            power_input=True,  # 전력 밀도 직접 사용
            P_el=0.0,
            A=self.A,
            p_el=self.p_el,
            LAI=self.LAI
        )
        
        # 스위치 OFF 테스트
        illu.switch = 0.0
        result_off = illu.step(dt=1.0)
        print(f"스위치 OFF - 전력: {result_off['W_el']:.2f} W")
        print(f"스위치 OFF - PAR: {result_off['R_PAR']:.2f} W/m²")
        print(f"스위치 OFF - 공기 흡수: {result_off['R_IluAir_Glob']:.2f} W/m²")
        
        # 스위치 ON 테스트
        illu.switch = 1.0
        result_on = illu.step(dt=1.0)
        print(f"스위치 ON - 전력: {result_on['W_el']:.2f} W")
        print(f"스위치 ON - PAR: {result_on['R_PAR']:.2f} W/m²")
        print(f"스위치 ON - 공기 흡수: {result_on['R_IluAir_Glob']:.2f} W/m²")
        
        # 검증: 스위치 ON시 계산값이 올바른지 확인
        expected_power = self.p_el * self.A  # 55 * 1000 = 55000 W
        expected_PAR = 0.25 * self.p_el      # 0.25 * 55 = 13.75 W/m²
        expected_NIR = 0.17 * self.p_el      # 0.17 * 55 = 9.35 W/m²
        expected_air = 0.58 * self.p_el      # 0.58 * 55 = 31.9 W/m²
        
        assert abs(result_on['W_el'] - expected_power) < 0.01, f"전력 계산 오류: {result_on['W_el']} vs {expected_power}"
        assert abs(result_on['R_PAR'] - expected_PAR) < 0.01, f"PAR 계산 오류: {result_on['R_PAR']} vs {expected_PAR}"
        assert abs(result_on['R_NIR'] - expected_NIR) < 0.01, f"NIR 계산 오류: {result_on['R_NIR']} vs {expected_NIR}"
        assert abs(result_on['R_IluAir_Glob'] - expected_air) < 0.01, f"공기 흡수 계산 오류: {result_on['R_IluAir_Glob']} vs {expected_air}"
        
        print("✓ 스위치 테스트 통과\n")
        return illu
    
    def test_radiation_components(self):
        """복사 성분 계산 테스트"""
        print("=== 복사 성분 계산 테스트 ===")
        
        illu = Illumination(
            power_input=True,  # 전력 밀도 직접 사용
            P_el=0.0,
            A=self.A,
            p_el=self.p_el,
            LAI=self.LAI
        )
        
        illu.switch = 1.0
        result = illu.step(dt=1.0)
        
        # 복사 성분 비율 검증 (원본 Modelica 코드 기준)
        total_radiation = result['R_PAR'] + result['R_NIR'] + result['R_IluAir_Glob']
        expected_total = self.p_el * (0.25 + 0.17 + 0.58)  # 100% 확인
        
        print(f"PAR 복사: {result['R_PAR']:.2f} W/m² ({result['R_PAR']/self.p_el*100:.1f}%)")
        print(f"NIR 복사: {result['R_NIR']:.2f} W/m² ({result['R_NIR']/self.p_el*100:.1f}%)")
        print(f"공기 흡수: {result['R_IluAir_Glob']:.2f} W/m² ({result['R_IluAir_Glob']/self.p_el*100:.1f}%)")
        print(f"총 복사: {total_radiation:.2f} W/m² ({total_radiation/self.p_el*100:.1f}%)")
        
        assert abs(total_radiation - expected_total) < 0.01, f"총 복사 비율 오류: {total_radiation} vs {expected_total}"
        assert abs(total_radiation/self.p_el - 1.0) < 0.01, "복사 성분 합이 100%가 아님"
        
        print("✓ 복사 성분 계산 테스트 통과\n")
        return result
    
    def test_canopy_absorption(self):
        """작물 흡수 계산 테스트"""
        print("=== 작물 흡수 계산 테스트 ===")
        
        # 다양한 LAI 값으로 테스트
        LAI_values = [0.5, 1.0, 2.0, 3.0, 4.0]
        results = []
        
        for LAI in LAI_values:
            illu = Illumination(
                power_input=True,  # 전력 밀도 직접 사용
                P_el=0.0,
                A=self.A,
                p_el=self.p_el,
                LAI=LAI
            )
            
            illu.switch = 1.0
            result = illu.step(dt=1.0)
            results.append(result)
            
            print(f"LAI={LAI:.1f}: 작물 흡수={result['R_IluCan_Glob']:.2f} W/m², "
                  f"PAR 광합성={result['R_PAR_Can_umol']:.1f} μmol/m²/s")
        
        # LAI가 증가하면 작물 흡수도 증가해야 함
        for i in range(1, len(results)):
            assert results[i]['R_IluCan_Glob'] > results[i-1]['R_IluCan_Glob'], \
                f"LAI 증가 시 작물 흡수도 증가해야 함: {results[i]['R_IluCan_Glob']} vs {results[i-1]['R_IluCan_Glob']}"
        
        print("✓ 작물 흡수 계산 테스트 통과\n")
        return results
    
    def test_floor_absorption(self):
        """바닥 흡수 계산 테스트"""
        print("=== 바닥 흡수 계산 테스트 ===")
        
        # 다양한 LAI와 바닥 반사율로 테스트
        LAI_values = [1.0, 2.0, 3.0]
        rho_FlrPAR_values = [0.05, 0.10, 0.15]
        
        for LAI in LAI_values:
            for rho_FlrPAR in rho_FlrPAR_values:
                illu = Illumination(
                    power_input=True,  # 전력 밀도 직접 사용
                    P_el=0.0,
                    A=self.A,
                    p_el=self.p_el,
                    LAI=LAI,
                    rho_FlrPAR=rho_FlrPAR
                )
                
                illu.switch = 1.0
                result = illu.step(dt=1.0)
                
                print(f"LAI={LAI:.1f}, 바닥반사율={rho_FlrPAR:.2f}: "
                      f"바닥 흡수={result['R_IluFlr_Glob']:.2f} W/m²")
        
        print("✓ 바닥 흡수 계산 테스트 통과\n")
    
    def test_multilayer_model(self):
        """멀티레이어 타우-로 모델 테스트"""
        print("=== 멀티레이어 모델 테스트 ===")
        
        illu = Illumination(
            power_input=True,  # 전력 밀도 직접 사용
            P_el=0.0,
            A=self.A,
            p_el=self.p_el,
            LAI=self.LAI
        )
        
        # 다양한 투과율/반사율 조합 테스트
        test_cases = [
            (0.8, 0.7, 0.1, 0.2),  # (tau_Can, tau_Flr, rho_Can, rho_Flr)
            (0.6, 0.5, 0.2, 0.3),
            (0.4, 0.3, 0.3, 0.4),
        ]
        
        for tau_Can, tau_Flr, rho_Can, rho_Flr in test_cases:
            tau, rho = illu.multilayer_tau_rho(tau_Can, tau_Flr, rho_Can, rho_Flr)
            
            print(f"입력: τ_Can={tau_Can:.2f}, τ_Flr={tau_Flr:.2f}, ρ_Can={rho_Can:.2f}, ρ_Flr={rho_Flr:.2f}")
            print(f"출력: τ_total={tau:.3f}, ρ_total={rho:.3f}")
            
            # 에너지 보존 법칙 확인 (τ + ρ + α = 1, 여기서 α는 흡수율)
            alpha = 1 - tau - rho
            assert alpha >= 0, f"흡수율이 음수: {alpha}"
            assert tau >= 0 and rho >= 0, f"투과율/반사율이 음수: τ={tau}, ρ={rho}"
            
            print(f"흡수율: α={alpha:.3f}")
            print()
        
        print("✓ 멀티레이어 모델 테스트 통과\n")
    
    def test_power_input_modes(self):
        """전력 입력 모드 테스트"""
        print("=== 전력 입력 모드 테스트 ===")
        
        # 모드 1: 전력 밀도 입력 (power_input=True)
        illu1 = Illumination(
            power_input=True,
            P_el=0.0,
            A=self.A,
            p_el=self.p_el,
            LAI=self.LAI
        )
        
        illu1.switch = 1.0
        result1 = illu1.step(dt=1.0)
        
        print(f"모드 1 (전력밀도): {result1['W_el']:.0f} W")
        
        # 모드 2: 총 전력 입력 (power_input=False)
        total_power = self.p_el * self.A
        illu2 = Illumination(
            power_input=False,
            P_el=total_power,
            A=self.A,
            p_el=self.p_el,
            LAI=self.LAI
        )
        
        illu2.switch = 1.0
        result2 = illu2.step(dt=1.0)
        
        print(f"모드 2 (총전력): {result2['W_el']:.0f} W")
        
        # 두 모드의 결과가 같아야 함
        assert abs(result1['W_el'] - result2['W_el']) < 0.01, \
            f"전력 입력 모드 결과 불일치: {result1['W_el']} vs {result2['W_el']}"
        
        print("✓ 전력 입력 모드 테스트 통과\n")
    
    def visualize_results(self):
        """결과 시각화"""
        print("=== 결과 시각화 ===")
        
        # LAI 변화에 따른 복사 흡수 변화 그래프
        LAI_range = np.linspace(0.5, 5.0, 20)
        canopy_absorption = []
        floor_absorption = []
        air_absorption = []
        
        for LAI in LAI_range:
            illu = Illumination(
                power_input=True,  # 전력 밀도 직접 사용
                P_el=0.0,
                A=self.A,
                p_el=self.p_el,
                LAI=LAI
            )
            
            illu.switch = 1.0
            result = illu.step(dt=1.0)
            
            canopy_absorption.append(result['R_IluCan_Glob'])
            floor_absorption.append(result['R_IluFlr_Glob'])
            air_absorption.append(result['R_IluAir_Glob'])
        
        plt.figure(figsize=(12, 8))
        
        # 서브플롯 1: LAI에 따른 복사 흡수
        plt.subplot(2, 2, 1)
        plt.plot(LAI_range, canopy_absorption, 'g-', label='Canopy', linewidth=2)
        plt.plot(LAI_range, floor_absorption, 'brown', label='Floor', linewidth=2)
        plt.plot(LAI_range, air_absorption, 'b--', label='Air', linewidth=2)
        plt.xlabel('LAI')
        plt.ylabel('Radiation Absorption (W/m²)')
        plt.title('LAI Effect on Radiation Absorption')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 서브플롯 2: 복사 성분 비율
        plt.subplot(2, 2, 2)
        illu = Illumination(power_input=True, P_el=0.0, A=self.A, p_el=self.p_el, LAI=2.0)
        illu.switch = 1.0
        result = illu.step(dt=1.0)
        
        components = ['PAR\n(25%)', 'NIR\n(17%)', 'Air Absorption\n(58%)']
        values = [result['R_PAR'], result['R_NIR'], result['R_IluAir_Glob']]
        colors = ['green', 'red', 'blue']
        
        plt.pie(values, labels=components, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('Radiation Components Distribution')
        
        # 서브플롯 3: 시간에 따른 조명 제어
        plt.subplot(2, 2, 3)
        time_hours = np.arange(0, 24, 0.5)
        switch_schedule = np.where((time_hours >= 6) & (time_hours <= 18), 0.0, 1.0)  # 야간 조명
        power_schedule = []
        
        illu = Illumination(power_input=True, P_el=0.0, A=self.A, p_el=self.p_el, LAI=2.0)
        
        for switch_state in switch_schedule:
            illu.switch = switch_state
            result = illu.step(dt=1.0)
            power_schedule.append(result['W_el'] / 1000)  # kW 단위
        
        plt.plot(time_hours, power_schedule, 'r-', linewidth=2)
        plt.xlabel('Time (hours)')
        plt.ylabel('Power (kW)')
        plt.title('Daily Lighting Schedule')
        plt.grid(True, alpha=0.3)
        plt.xlim(0, 24)
        
        # 서브플롯 4: PAR 광합성 유효 복사
        plt.subplot(2, 2, 4)
        LAI_test = np.linspace(0.5, 4.0, 15)
        PAR_umol = []
        
        for LAI in LAI_test:
            illu = Illumination(power_input=True, P_el=0.0, A=self.A, p_el=self.p_el, LAI=LAI)
            illu.switch = 1.0
            result = illu.step(dt=1.0)
            PAR_umol.append(result['R_PAR_Can_umol'])
        
        plt.plot(LAI_test, PAR_umol, 'g-', marker='o', linewidth=2)
        plt.xlabel('LAI')
        plt.ylabel('PAR Absorption (μmol/m²/s)')
        plt.title('PAR for Photosynthesis')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('illumination_test_results.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("✓ 시각화 완료: illumination_test_results.png 저장됨\n")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🌱 Illumination 클래스 종합 테스트 시작 🌱\n")
        
        try:
            # 기본 테스트들
            self.test_basic_initialization()
            self.test_switch_on_off()
            self.test_radiation_components()
            self.test_canopy_absorption()
            self.test_floor_absorption()
            self.test_multilayer_model()
            self.test_power_input_modes()
            
            # 시각화
            self.visualize_results()
            
            print("🎉 모든 테스트 통과! Illumination 클래스가 올바르게 작동합니다.")
            
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            raise

if __name__ == "__main__":
    tester = TestIllumination()
    tester.run_all_tests() 