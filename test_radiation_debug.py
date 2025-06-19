"""
복사 열전달 계산 디버깅 테스트
Q_flow가 비정상적으로 큰 값이 나오는 원인을 찾기 위한 테스트
"""

import numpy as np
from Flows.HeatTransfer.Radiation_T4 import Radiation_T4
from Flows.HeatTransfer.Radiation_N import Radiation_N

def test_radiation_calculation():
    """복사 열전달 계산 테스트"""
    print("=== 복사 열전달 계산 디버깅 ===")
    
    # 테스트 파라미터
    A = 1.0  # 1 m² (작은 면적으로 테스트)
    epsilon_a = 0.88  # 파이프 방사율
    epsilon_b = 1.0   # 스크린 방사율
    FFa = 0.1         # 파이프 View Factor
    FFb = 0.8         # 스크린 View Factor
    
    # 온도 설정
    T_a = 353.15  # 80°C (파이프)
    T_b = 298.15  # 25°C (스크린)
    
    print(f"테스트 파라미터:")
    print(f"  면적: {A} m²")
    print(f"  방사율 A: {epsilon_a}")
    print(f"  방사율 B: {epsilon_b}")
    print(f"  View Factor A: {FFa}")
    print(f"  View Factor B: {FFb}")
    print(f"  온도 A: {T_a} K ({T_a-273.15:.1f}°C)")
    print(f"  온도 B: {T_b} K ({T_b-273.15:.1f}°C)")
    
    # Radiation_T4 테스트
    print(f"\n=== Radiation_T4 테스트 ===")
    rad_T4 = Radiation_T4(
        A=A,
        epsilon_a=epsilon_a,
        epsilon_b=epsilon_b,
        FFa=FFa,
        FFb=FFb
    )
    
    # 포트 온도 설정
    rad_T4.port_a.T = T_a
    rad_T4.port_b.T = T_b
    
    # 복사 열전달 계산
    Q_flow_T4 = rad_T4.step()
    
    print(f"Radiation_T4 결과:")
    print(f"  Q_flow: {Q_flow_T4:.2f} W")
    print(f"  단위 면적당: {Q_flow_T4/A:.2f} W/m²")
    
    # Radiation_N 테스트
    print(f"\n=== Radiation_N 테스트 ===")
    rad_N = Radiation_N(
        A=A,
        epsilon_a=epsilon_a,
        epsilon_b=epsilon_b,
        N=1
    )
    
    # View Factor 설정
    rad_N.FFa = FFa
    rad_N.FFb = FFb
    
    # 포트 온도 설정
    rad_N.heatPorts_a[0].T = T_a
    rad_N.port_b.T = T_b
    
    # 복사 열전달 계산
    Q_flow_N = rad_N.step()
    
    print(f"Radiation_N 결과:")
    print(f"  Q_flow: {Q_flow_N:.2f} W")
    print(f"  단위 면적당: {Q_flow_N/A:.2f} W/m²")
    
    # 온실 크기로 확장
    print(f"\n=== 온실 크기로 확장 ===")
    A_greenhouse = 14000  # m²
    
    Q_flow_greenhouse = Q_flow_T4 * A_greenhouse
    print(f"온실 크기 ({A_greenhouse} m²)에서의 열전달:")
    print(f"  Q_flow: {Q_flow_greenhouse:.2f} W")
    print(f"  Q_flow: {Q_flow_greenhouse/1000:.2f} kW")
    
    # 다양한 온도 차이에 대한 테스트
    print(f"\n=== 다양한 온도 차이 테스트 ===")
    temp_diffs = [10, 20, 30, 50, 100]  # K
    
    for dT in temp_diffs:
        T_hot = 298.15 + dT
        T_cold = 298.15
        
        rad_T4.port_a.T = T_hot
        rad_T4.port_b.T = T_cold
        
        Q_flow = rad_T4.step() * A_greenhouse
        
        print(f"  온도차 {dT}K: {Q_flow:.0f} W ({Q_flow/1000:.1f} kW)")
    
    # View Factor 영향 테스트
    print(f"\n=== View Factor 영향 테스트 ===")
    view_factors = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0]
    
    for ff in view_factors:
        rad_T4.FFa = ff
        rad_T4.FFb = ff
        
        rad_T4.port_a.T = T_a
        rad_T4.port_b.T = T_b
        
        Q_flow = rad_T4.step() * A_greenhouse
        
        print(f"  View Factor {ff:.2f}: {Q_flow:.0f} W ({Q_flow/1000:.1f} kW)")

def test_realistic_scenario():
    """현실적인 온실 시나리오 테스트"""
    print(f"\n=== 현실적인 온실 시나리오 테스트 ===")
    
    # 현실적인 파라미터
    A = 1000  # 1000 m² (더 현실적인 온실 크기)
    epsilon_pipe = 0.88
    epsilon_screen = 1.0
    FF_pipe = 0.05  # 파이프가 스크린을 보는 View Factor (작은 값)
    FF_screen = 0.8  # 스크린이 파이프를 보는 View Factor
    
    # 현실적인 온도
    T_pipe = 333.15  # 60°C (난방 파이프)
    T_screen = 293.15  # 20°C (스크린)
    
    print(f"현실적인 파라미터:")
    print(f"  면적: {A} m²")
    print(f"  파이프 View Factor: {FF_pipe}")
    print(f"  스크린 View Factor: {FF_screen}")
    print(f"  파이프 온도: {T_pipe} K ({T_pipe-273.15:.1f}°C)")
    print(f"  스크린 온도: {T_screen} K ({T_screen-273.15:.1f}°C)")
    
    # 복사 열전달 계산
    rad = Radiation_T4(
        A=A,
        epsilon_a=epsilon_pipe,
        epsilon_b=epsilon_screen,
        FFa=FF_pipe,
        FFb=FF_screen
    )
    
    rad.port_a.T = T_pipe
    rad.port_b.T = T_screen
    
    Q_flow = rad.step()
    
    print(f"결과:")
    print(f"  Q_flow: {Q_flow:.2f} W")
    print(f"  Q_flow: {Q_flow/1000:.2f} kW")
    print(f"  단위 면적당: {Q_flow/A:.2f} W/m²")

if __name__ == "__main__":
    test_radiation_calculation()
    test_realistic_scenario() 