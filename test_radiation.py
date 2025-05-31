import numpy as np
import matplotlib.pyplot as plt
from Flows.HeatTransfer.Radiation_T4 import Radiation_T4
from Flows.HeatTransfer.Radiation_N import Radiation_N
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_b import HeatPort_b

class SimpleComponent:
    """간단한 컴포넌트 클래스 (열용량을 가진 물체)"""
    def __init__(self, T_init, c_p=1000, m=0.1):
        self.heatPort = HeatPort_a()
        self.heatPort.T = T_init  # 초기 온도 [K]
        self.c_p = c_p  # 비열 [J/(kg·K)]
        self.m = m      # 질량 [kg]
        self.Q_flow = 0.0  # 열 수지 [W]
        
    def step(self, dt):
        """한 스텝 진행"""
        # Q = m*c_p*dT/dt 에서 dT = Q*dt/(m*c_p)
        dT = self.Q_flow * dt / (self.m * self.c_p)
        self.heatPort.T += dT
        self.Q_flow = 0.0  # 매 스텝마다 열 수지 초기화

def test_radiation():
    # 시뮬레이션 파라미터
    dt = 1  # 시간 간격 [s] (더 작은 시간 간격으로 변경)
    sim_time = 3600 * 24  # 시뮬레이션 시간 [s] (24시간)
    n_steps = int(sim_time / dt)
    
    # 컴포넌트 초기화 (온도 차이를 줄임)
    screen = SimpleComponent(293.15, c_p=1000, m=1.0)     # 스크린 (20°C, 질량 증가)
    canopy = SimpleComponent(295.15, c_p=1000, m=1.0)     # 캔오피 (22°C)
    cover = SimpleComponent(291.15, c_p=840, m=1.0)       # 덮개 (18°C)
    floor = SimpleComponent(297.15, c_p=1000, m=10.0)     # 바닥 (24°C)
    
    # 복사열 교환 컴포넌트 초기화 (면적을 줄임)
    rad_CanScr = Radiation_T4(A=0.1, epsilon_a=1.0, epsilon_b=1.0)  # 캔오피-스크린
    rad_FlrScr = Radiation_T4(A=0.1, epsilon_a=0.89, epsilon_b=1.0) # 바닥-스크린
    rad_ScrCov = Radiation_T4(A=0.1, epsilon_a=1.0, epsilon_b=0.84) # 스크린-덮개
    
    # 결과 저장용 배열
    times = np.linspace(0, sim_time/3600, n_steps)  # 시간 [h]
    results = {
        'T_screen': np.zeros(n_steps),
        'T_canopy': np.zeros(n_steps),
        'T_cover': np.zeros(n_steps),
        'T_floor': np.zeros(n_steps),
        'Q_CanScr': np.zeros(n_steps),
        'Q_FlrScr': np.zeros(n_steps),
        'Q_ScrCov': np.zeros(n_steps)
    }
    
    # 초기 상태 출력
    print("\n=== 초기 상태 ===")
    print(f"Screen: {screen.heatPort.T-273.15:.2f}°C")
    print(f"Canopy: {canopy.heatPort.T-273.15:.2f}°C")
    print(f"Cover:  {cover.heatPort.T-273.15:.2f}°C")
    print(f"Floor:  {floor.heatPort.T-273.15:.2f}°C")
    
    # 시뮬레이션 루프
    for i in range(n_steps):
        # 1. 포트 연결
        # 캔오피-스크린
        rad_CanScr.port_a = canopy.heatPort
        rad_CanScr.port_b = screen.heatPort
        
        # 바닥-스크린
        rad_FlrScr.port_a = floor.heatPort
        rad_FlrScr.port_b = screen.heatPort
        
        # 스크린-덮개
        rad_ScrCov.port_a = screen.heatPort
        rad_ScrCov.port_b = cover.heatPort
        
        # 2. 복사열 계산
        Q_CanScr = rad_CanScr.step(dt)  # 캔오피 → 스크린
        Q_FlrScr = rad_FlrScr.step(dt)  # 바닥 → 스크린
        Q_ScrCov = rad_ScrCov.step(dt)  # 스크린 → 덮개
        
        # 3. 열 수지 반영
        # 캔오피-스크린
        canopy.Q_flow -= Q_CanScr  # 캔오피는 열을 잃음
        screen.Q_flow += Q_CanScr  # 스크린은 열을 얻음
        
        # 바닥-스크린
        floor.Q_flow -= Q_FlrScr   # 바닥은 열을 잃음
        screen.Q_flow += Q_FlrScr  # 스크린은 열을 얻음
        
        # 스크린-덮개
        screen.Q_flow -= Q_ScrCov  # 스크린은 열을 잃음
        cover.Q_flow += Q_ScrCov   # 덮개는 열을 얻음
        
        # 4. 상태 업데이트
        screen.step(dt)
        canopy.step(dt)
        cover.step(dt)
        floor.step(dt)
        
        # 5. 결과 저장
        results['T_screen'][i] = screen.heatPort.T - 273.15  # °C로 변환
        results['T_canopy'][i] = canopy.heatPort.T - 273.15
        results['T_cover'][i] = cover.heatPort.T - 273.15
        results['T_floor'][i] = floor.heatPort.T - 273.15
        results['Q_CanScr'][i] = Q_CanScr
        results['Q_FlrScr'][i] = Q_FlrScr
        results['Q_ScrCov'][i] = Q_ScrCov
        
        # 디버깅 출력 (1시간마다)
        if i % 3600 == 0:  # 1시간마다 출력 (dt=1s이므로 3600 스텝마다)
            print(f"\n=== Step {i} | t={times[i]:.2f}h ===")
            print(f"Screen: {results['T_screen'][i]:.2f}°C")
            print(f"Canopy: {results['T_canopy'][i]:.2f}°C")
            print(f"Cover:  {results['T_cover'][i]:.2f}°C")
            print(f"Floor:  {results['T_floor'][i]:.2f}°C")
            print(f"Q_CanScr: {Q_CanScr:.1f}W")
            print(f"Q_FlrScr: {Q_FlrScr:.1f}W")
            print(f"Q_ScrCov: {Q_ScrCov:.1f}W")
            
            # 온도 차이 출력 (디버깅용)
            print("\n온도 차이:")
            print(f"Canopy-Screen: {canopy.heatPort.T - screen.heatPort.T:.2f}K")
            print(f"Floor-Screen:  {floor.heatPort.T - screen.heatPort.T:.2f}K")
            print(f"Screen-Cover:  {screen.heatPort.T - cover.heatPort.T:.2f}K")
    
    # 결과 플롯
    plt.figure(figsize=(15, 10))
    
    # 1) 온도
    plt.subplot(2,1,1)
    plt.plot(times, results['T_screen'], label='Screen')
    plt.plot(times, results['T_canopy'], label='Canopy')
    plt.plot(times, results['T_cover'], label='Cover')
    plt.plot(times, results['T_floor'], label='Floor')
    plt.title('Component Temperatures')
    plt.xlabel('Time [h]')
    plt.ylabel('Temperature [°C]')
    plt.legend()
    plt.grid(True)
    
    # 2) 열량
    plt.subplot(2,1,2)
    plt.plot(times, results['Q_CanScr'], label='Canopy→Screen')
    plt.plot(times, results['Q_FlrScr'], label='Floor→Screen')
    plt.plot(times, results['Q_ScrCov'], label='Screen→Cover')
    plt.title('Heat Flows')
    plt.xlabel('Time [h]')
    plt.ylabel('Heat Flow [W]')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    test_radiation() 