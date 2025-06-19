"""
ThermalScreen 클래스 테스트 코드
Modelica 원본과 Python 구현의 동작을 비교합니다.
"""

import numpy as np
from Components.Greenhouse.ThermalScreen import ThermalScreen

def test_thermal_screen_basic():
    """기본 기능 테스트"""
    print("=== ThermalScreen 기본 기능 테스트 ===")
    
    # 스크린 초기화 (더 현실적인 파라미터)
    screen = ThermalScreen(
        A=1.4e4,           # 면적 [m²]
        SC=0.5,            # 스크린 폐쇄율 [0-1]
        rho=0.89e3,         # 밀도 [kg/m³] 
        c_p=1.2e3,         # 비열 [J/(kg·K)] 
        h=0.35e-3,         # 두께 [m]
        tau_FIR=0.15,      # FIR 투과율
        T_start=298.15     # 초기 온도 [K]
    )
    
    # 스크린 질량과 열용량 계산
    mass = screen.rho * screen.h * screen.A
    heat_capacity = mass * screen.c_p
    
    print(f"스크린 파라미터:")
    print(f"  면적: {screen.A:.0f} m²")
    print(f"  밀도: {screen.rho:.0f} kg/m³")
    print(f"  두께: {screen.h*1000:.2f} mm")
    print(f"  비열: {screen.c_p:.0f} J/(kg·K)")
    print(f"  질량: {mass:.6f} kg")
    print(f"  열용량: {heat_capacity:.2f} J/K")
    print(f"  초기 온도: {screen.T - 273.15:.1f}°C")
    
    # View Factor 테스트
    print(f"\nView Factor 테스트:")
    print(f"  SC=0.5일 때 FF_i: {screen.FF_i:.2f}")
    print(f"  SC=0.5일 때 FF_ij: {screen.FF_ij:.2f}")
    
    # 스크린 폐쇄율 변경
    screen.SC = 1.0
    screen.step(0)  # View Factor 업데이트
    print(f"  SC=1.0일 때 FF_i: {screen.FF_i:.2f}")
    print(f"  SC=1.0일 때 FF_ij: {screen.FF_ij:.2f}")
    
    return screen, mass, heat_capacity

def test_thermal_screen_heat_transfer():
    """열전달 테스트"""
    print("\n=== ThermalScreen 열전달 테스트 ===")
    
    screen, mass, heat_capacity = test_thermal_screen_basic()
    
    # 다양한 열유속에 대한 온도 변화 테스트
    dt = 3600  # 1시간
    test_heat_flows = [100, 1000, 10000, 100000]  # W
    
    print(f"\n다양한 열유속에 대한 온도 변화 (dt={dt}초):")
    print(f"{'열유속(W)':<10} {'예상온도변화(K)':<15} {'실제온도변화(K)':<15}")
    print("-" * 45)
    
    for Q_flow in test_heat_flows:
        # 초기화
        screen.T = 298.15
        screen.Q_flow = Q_flow
        
        # 온도 변화 계산
        expected_dT = Q_flow * dt / heat_capacity
        old_T = screen.T
        screen.step(dt)
        actual_dT = screen.T - old_T
        
        print(f"{Q_flow:<10} {expected_dT:<15.2f} {actual_dT:<15.2f}")
    
    return screen

def test_thermal_screen_edge_cases():
    """엣지 케이스 테스트"""
    print("\n=== ThermalScreen 엣지 케이스 테스트 ===")
    
    screen = ThermalScreen(A=1.0, rho=1.2e3, c_p=1.2e3, T_start=298.15)
    
    # 1. 매우 큰 열유속
    print("1. 매우 큰 열유속 테스트:")
    screen.Q_flow = 1e6  # 1MW
    dt = 1  # 1초
    old_T = screen.T
    screen.step(dt)
    dT = screen.T - old_T
    print(f"   열유속: {screen.Q_flow:.0f} W")
    print(f"   온도 변화: {dT:.2f} K")
    print(f"   최종 온도: {screen.T - 273.15:.1f}°C")
    
    # 2. 음수 열유속 (냉각)
    print("\n2. 음수 열유속 테스트:")
    screen.T = 298.15
    screen.Q_flow = -1000  # -1kW
    old_T = screen.T
    screen.step(dt)
    dT = screen.T - old_T
    print(f"   열유속: {screen.Q_flow:.0f} W")
    print(f"   온도 변화: {dT:.2f} K")
    print(f"   최종 온도: {screen.T - 273.15:.1f}°C")
    
    # 3. SC=0 (완전 개방)
    print("\n3. SC=0 (완전 개방) 테스트:")
    screen.SC = 0.0
    screen.step(0)
    print(f"   FF_i: {screen.FF_i:.2f}")
    print(f"   FF_ij: {screen.FF_ij:.2f}")
    
    # 4. SC=1 (완전 폐쇄)
    print("\n4. SC=1 (완전 폐쇄) 테스트:")
    screen.SC = 1.0
    screen.step(0)
    print(f"   FF_i: {screen.FF_i:.2f}")
    print(f"   FF_ij: {screen.FF_ij:.2f}")

def test_thermal_screen_greenhouse_scenario():
    """온실 시나리오 테스트"""
    print("\n=== ThermalScreen 온실 시나리오 테스트 ===")
    
    # 온실 크기에 맞는 스크린 (폴리에스터 재질)
    screen = ThermalScreen(
        A=1.4e4,  # 14,000 m²
        SC=0.8,  # 80% 폐쇄
        rho=0.89e3,  # 890 kg/m³ (폴리에스터)
        c_p=1.2e3,  # 1200 J/(kg·K) (폴리에스터)
        T_start=298.15
    )
    
    mass = screen.rho * screen.h * screen.A
    heat_capacity = mass * screen.c_p
    
    print(f"온실 스크린 파라미터 (폴리에스터 재질):")
    print(f"  면적: {screen.A:.0f} m²")
    print(f"  질량: {mass:.0f} kg")
    print(f"  열용량: {heat_capacity:.0f} J/K")
    print(f"  SC: {screen.SC:.1f}")
    print(f"  FF_i: {screen.FF_i:.2f}")
    print(f"  FF_ij: {screen.FF_ij:.2f}")
    
    # 실제 온실 조건 테스트
    print(f"\n=== 실제 온실 조건 테스트 ===")
    
    # 1. 일반적인 온실 열유속 (10 W/m² - 더 현실적인 값)
    Q_flow_per_m2 = 10  # W/m² (더 현실적인 값)
    Q_flow_total = Q_flow_per_m2 * screen.A
    
    print(f"1. 일반적인 온실 열유속 테스트:")
    print(f"   단위 면적당 열유속: {Q_flow_per_m2} W/m²")
    print(f"   총 열유속: {Q_flow_total:.0f} W")
    
    dt = 3600  # 1시간
    old_T = screen.T
    screen.Q_flow = Q_flow_total
    screen.step(dt)
    dT = screen.T - old_T
    
    print(f"   온도 변화: {dT:.2f} K")
    print(f"   최종 온도: {screen.T - 273.15:.1f}°C")
    
    # 2. 더 큰 열유속 (50 W/m²)
    print(f"\n2. 더 큰 열유속 테스트:")
    Q_flow_per_m2 = 50  # W/m²
    Q_flow_total = Q_flow_per_m2 * screen.A
    
    print(f"   단위 면적당 열유속: {Q_flow_per_m2} W/m²")
    print(f"   총 열유속: {Q_flow_total:.0f} W")
    
    screen.T = 298.15
    old_T = screen.T
    screen.Q_flow = Q_flow_total
    screen.step(dt)
    dT = screen.T - old_T
    
    print(f"   온도 변화: {dT:.2f} K")
    print(f"   최종 온도: {screen.T - 273.15:.1f}°C")
    
    # 3. 단기간 테스트 (1분)
    print(f"\n3. 단기간 테스트 (1분):")
    Q_flow_per_m2 = 100  # W/m²
    Q_flow_total = Q_flow_per_m2 * screen.A
    dt_short = 60  # 1분
    
    print(f"   단위 면적당 열유속: {Q_flow_per_m2} W/m²")
    print(f"   총 열유속: {Q_flow_total:.0f} W")
    print(f"   시간: {dt_short}초")
    
    screen.T = 298.15
    old_T = screen.T
    screen.Q_flow = Q_flow_total
    screen.step(dt_short)
    dT = screen.T - old_T
    
    print(f"   온도 변화: {dT:.2f} K")
    print(f"   최종 온도: {screen.T - 273.15:.1f}°C")
    
    # 4. 문제가 되는 열유속 분석
    print(f"\n4. 문제가 되는 열유속 분석:")
    problem_Q_flow = 740631  # W
    screen.T = 298.15
    old_T = screen.T
    screen.Q_flow = problem_Q_flow
    screen.step(dt)
    dT = screen.T - old_T
    
    print(f"   열유속: {problem_Q_flow:.0f} W")
    print(f"   단위 면적당: {problem_Q_flow/screen.A:.1f} W/m²")
    print(f"   온도 변화: {dT:.2f} K")
    print(f"   최종 온도: {screen.T - 273.15:.1f}°C")
    print(f"   예상 온도 변화: {problem_Q_flow * dt / heat_capacity:.2f} K")
    
    # 5. 현실적인 열유속 테스트
    print(f"\n5. 현실적인 열유속 테스트:")
    realistic_Q_flow = 50000  # 50 kW
    screen.T = 298.15
    old_T = screen.T
    screen.Q_flow = realistic_Q_flow
    screen.step(dt)
    dT = screen.T - old_T
    
    print(f"   열유속: {realistic_Q_flow:.0f} W")
    print(f"   단위 면적당: {realistic_Q_flow/screen.A:.1f} W/m²")
    print(f"   온도 변화: {dT:.2f} K")
    print(f"   최종 온도: {screen.T - 273.15:.1f}°C")

def test_thermal_screen_realistic_scenario():
    """실제 온실 조건에 맞는 현실적인 시나리오 테스트"""
    print("\n=== 실제 온실 조건 시나리오 테스트 ===")
    
    # 온실 크기에 맞는 스크린 (폴리에스터 재질)
    screen = ThermalScreen(
        A=1.4e4,  # 14,000 m²
        SC=0.8,  # 80% 폐쇄
        rho=0.89e3,  # 890 kg/m³ (폴리에스터)
        c_p=1.2e3,  # 1200 J/(kg·K) (폴리에스터)
        T_start=298.15
    )
    
    mass = screen.rho * screen.h * screen.A
    heat_capacity = mass * screen.c_p
    
    print(f"온실 스크린 파라미터 (폴리에스터 재질):")
    print(f"  면적: {screen.A:.0f} m²")
    print(f"  질량: {mass:.0f} kg")
    print(f"  열용량: {heat_capacity:.0f} J/K")
    print(f"  SC: {screen.SC:.1f}")
    
    # 실제 온실 조건 테스트
    print(f"\n=== 실제 온실 열유속 조건 테스트 ===")
    
    # 1. 매우 낮은 열유속 (1 W/m²)
    print(f"1. 매우 낮은 열유속 테스트:")
    Q_flow_per_m2 = 1  # W/m² (매우 낮은 값)
    Q_flow_total = Q_flow_per_m2 * screen.A
    
    print(f"   단위 면적당 열유속: {Q_flow_per_m2} W/m²")
    print(f"   총 열유속: {Q_flow_total:.0f} W")
    
    dt = 3600  # 1시간
    old_T = screen.T
    screen.Q_flow = Q_flow_total
    screen.step(dt)
    dT = screen.T - old_T
    
    print(f"   온도 변화: {dT:.2f} K")
    print(f"   최종 온도: {screen.T - 273.15:.1f}°C")
    
    # 2. 낮은 열유속 (2 W/m²)
    print(f"\n2. 낮은 열유속 테스트:")
    Q_flow_per_m2 = 2  # W/m²
    Q_flow_total = Q_flow_per_m2 * screen.A
    
    print(f"   단위 면적당 열유속: {Q_flow_per_m2} W/m²")
    print(f"   총 열유속: {Q_flow_total:.0f} W")
    
    screen.T = 298.15
    old_T = screen.T
    screen.Q_flow = Q_flow_total
    screen.step(dt)
    dT = screen.T - old_T
    
    print(f"   온도 변화: {dT:.2f} K")
    print(f"   최종 온도: {screen.T - 273.15:.1f}°C")
    
    # 3. 중간 열유속 (5 W/m²)
    print(f"\n3. 중간 열유속 테스트:")
    Q_flow_per_m2 = 5  # W/m²
    Q_flow_total = Q_flow_per_m2 * screen.A
    
    print(f"   단위 면적당 열유속: {Q_flow_per_m2} W/m²")
    print(f"   총 열유속: {Q_flow_total:.0f} W")
    
    screen.T = 298.15
    old_T = screen.T
    screen.Q_flow = Q_flow_total
    screen.step(dt)
    dT = screen.T - old_T
    
    print(f"   온도 변화: {dT:.2f} K")
    print(f"   최종 온도: {screen.T - 273.15:.1f}°C")
    
    # 4. 단기간 테스트 (5분)
    print(f"\n4. 단기간 테스트 (5분):")
    Q_flow_per_m2 = 10  # W/m²
    Q_flow_total = Q_flow_per_m2 * screen.A
    dt_short = 300  # 5분
    
    print(f"   단위 면적당 열유속: {Q_flow_per_m2} W/m²")
    print(f"   총 열유속: {Q_flow_total:.0f} W")
    print(f"   시간: {dt_short}초")
    
    screen.T = 298.15
    old_T = screen.T
    screen.Q_flow = Q_flow_total
    screen.step(dt_short)
    dT = screen.T - old_T
    
    print(f"   온도 변화: {dT:.2f} K")
    print(f"   최종 온도: {screen.T - 273.15:.1f}°C")
    
    # 5. 매우 단기간 테스트 (1분)
    print(f"\n5. 매우 단기간 테스트 (1분):")
    Q_flow_per_m2 = 20  # W/m²
    Q_flow_total = Q_flow_per_m2 * screen.A
    dt_very_short = 60  # 1분
    
    print(f"   단위 면적당 열유속: {Q_flow_per_m2} W/m²")
    print(f"   총 열유속: {Q_flow_total:.0f} W")
    print(f"   시간: {dt_very_short}초")
    
    screen.T = 298.15
    old_T = screen.T
    screen.Q_flow = Q_flow_total
    screen.step(dt_very_short)
    dT = screen.T - old_T
    
    print(f"   온도 변화: {dT:.2f} K")
    print(f"   최종 온도: {screen.T - 273.15:.1f}°C")
    
    # 6. 문제가 되는 열유속 재분석
    print(f"\n6. 문제가 되는 열유속 재분석:")
    problem_Q_flow = 740631  # W
    screen.T = 298.15
    old_T = screen.T
    screen.Q_flow = problem_Q_flow
    
    # 1분씩 나누어서 계산
    dt_step = 60  # 1분
    total_time = 3600  # 1시간
    steps = total_time // dt_step
    
    print(f"   열유속: {problem_Q_flow:.0f} W")
    print(f"   단위 면적당: {problem_Q_flow/screen.A:.1f} W/m²")
    print(f"   시간 스텝: {dt_step}초씩 {steps}회 계산")
    
    for i in range(steps):
        screen.step(dt_step)
    
    dT = screen.T - old_T
    print(f"   총 온도 변화: {dT:.2f} K")
    print(f"   최종 온도: {screen.T - 273.15:.1f}°C")
    print(f"   예상 온도 변화: {problem_Q_flow * total_time / heat_capacity:.2f} K")

def test_thermal_screen_integrated():
    """원본 Greenhouse_1 모델과 동일한 구조의 통합 테스트 (간소화 버전)"""
    print("\n=== ThermalScreen 통합 테스트 (원본 모델 구조) ===")
    
    # 온실 크기에 맞는 스크린 (폴리에스터 재질)
    screen = ThermalScreen(
        A=1.4e4,  # 14,000 m²
        SC=0.8,  # 80% 폐쇄
        rho=0.89e3,  # 890 kg/m³ (폴리에스터)
        c_p=1.2e3,  # 1200 J/(kg·K) (폴리에스터)
        T_start=298.15
    )
    
    print(f"통합 테스트 구성 요소:")
    print(f"  스크린: {screen.A:.0f} m², SC={screen.SC:.1f}")
    print(f"  스크린 질량: {screen.rho * screen.h * screen.A:.0f} kg")
    print(f"  스크린 열용량: {screen.rho * screen.c_p * screen.h * screen.A:.0f} J/K")
    
    # 시뮬레이션 조건 설정
    # 온실 내부 온도들 (실제 온실 조건)
    T_air = 298.15      # 25°C (실내 공기)
    T_air_top = 297.15  # 24°C (상부 공기)
    T_cover = 283.15    # 10°C (외피)
    T_canopy = 298.15   # 25°C (작물)
    T_floor = 288.15    # 15°C (바닥)
    T_pipe_low = 323.15 # 50°C (하부 파이프)
    T_pipe_up = 318.15  # 45°C (상부 파이프)
    
    # 열전달 계수들 (실제 온실 조건에서의 대략적인 값)
    # 복사 열전달 계수 (Stefan-Boltzmann 상수 × 방사율 × 면적)
    sigma = 5.67e-8  # Stefan-Boltzmann 상수 [W/(m²·K⁴)]
    
    # 복사 열전달 계산 (간소화)
    def calculate_radiation_heat_transfer():
        # 실제 온실에서는 복사 열전달이 더 작음
        # Stefan-Boltzmann 상수
        sigma = 5.67e-8  # [W/(m²·K⁴)]
        
        # 작물 ↔ 스크린 복사 (T⁴ 법칙, View Factor 적용)
        # 실제로는 작물과 스크린 사이의 복사는 상대적으로 작음
        Q_rad_CanScr = sigma * 1.0 * 1.0 * screen.A * screen.FF_i * 0.1 * (
            T_canopy**4 - screen.T**4
        )
        
        # 하부 파이프 ↔ 스크린 복사 (실제 온실에서는 파이프 면적이 제한적)
        # 파이프는 전체 면적의 일부만 차지하므로 View Factor를 더 작게 적용
        pipe_area_factor = 0.05  # 파이프가 차지하는 면적 비율 (5%)
        Q_rad_LowScr = sigma * 0.88 * 1.0 * screen.A * screen.FF_i * pipe_area_factor * (
            T_pipe_low**4 - screen.T**4
        )
        
        # 상부 파이프 ↔ 스크린 복사
        Q_rad_UpScr = sigma * 0.88 * 1.0 * screen.A * screen.FF_i * pipe_area_factor * (
            T_pipe_up**4 - screen.T**4
        )
        
        # 바닥 ↔ 스크린 복사 (바닥은 스크린보다 차갑아서 열을 빼앗김)
        Q_rad_FlrScr = sigma * 0.89 * 1.0 * screen.A * screen.FF_i * 0.3 * (
            T_floor**4 - screen.T**4
        )
        
        # 스크린 ↔ 외피 복사 (외피는 더 차가워서 열을 빼앗김)
        Q_rad_ScrCov = sigma * 1.0 * 0.84 * screen.A * screen.FF_i * 0.2 * (
            screen.T**4 - T_cover**4
        )
        
        return {
            'Q_rad_CanScr': Q_rad_CanScr,
            'Q_rad_LowScr': Q_rad_LowScr,
            'Q_rad_UpScr': Q_rad_UpScr,
            'Q_rad_FlrScr': Q_rad_FlrScr,
            'Q_rad_ScrCov': Q_rad_ScrCov
        }
    
    # 대류 열전달 계산 (간소화)
    def calculate_convection_heat_transfer():
        # 대류 열전달 계수 (실제 온실 조건에서의 대략적인 값)
        h_conv = 3.0  # 대류 열전달 계수 [W/(m²·K)] - 더 현실적인 값
        
        # 공기 ↔ 스크린 대류
        Q_cnv_AirScr = h_conv * screen.A * screen.FF_i * (T_air - screen.T)
        
        # 스크린 ↔ 상부 공기 대류
        Q_cnv_ScrTop = h_conv * screen.A * screen.FF_i * (screen.T - T_air_top)
        
        return {
            'Q_cnv_AirScr': Q_cnv_AirScr,
            'Q_cnv_ScrTop': Q_cnv_ScrTop
        }
    
    # 환기 열전달 계산 (간소화)
    def calculate_ventilation_heat_transfer():
        # 스크린을 통한 공기 흐름에 의한 열전달
        # 실제 온실에서는 복잡하지만, 여기서는 간단히 계산
        air_density = 1.2  # 공기 밀도 [kg/m³]
        c_p_air = 1005    # 공기 비열 [J/(kg·K)]
        
        # 스크린을 통한 공기 유량 (간소화, 더 현실적인 값)
        air_flow_rate = 0.01 * screen.A * screen.FF_i  # m³/s (더 작은 값)
        
        Q_ven_AirTop = air_density * c_p_air * air_flow_rate * (T_air - T_air_top)
        
        return {
            'Q_ven_AirTop': Q_ven_AirTop
        }
    
    # 열전달 계산
    def calculate_total_heat_transfer():
        radiation = calculate_radiation_heat_transfer()
        convection = calculate_convection_heat_transfer()
        ventilation = calculate_ventilation_heat_transfer()
        
        # 스크린 열 균형 계산 (원본 모델과 동일한 구조)
        total_Q_flow = (
            radiation['Q_rad_CanScr'] +      # 작물 ↔ 스크린 복사
            radiation['Q_rad_LowScr'] +      # 하부 파이프 ↔ 스크린 복사
            radiation['Q_rad_UpScr'] +       # 상부 파이프 ↔ 스크린 복사
            radiation['Q_rad_FlrScr'] +      # 바닥 ↔ 스크린 복사
            radiation['Q_rad_ScrCov'] +      # 스크린 ↔ 외피 복사
            convection['Q_cnv_AirScr'] +     # 공기 ↔ 스크린 대류
            convection['Q_cnv_ScrTop'] +     # 스크린 ↔ 상부 공기 대류
            ventilation['Q_ven_AirTop']      # 스크린을 통한 환기
        )
        
        return total_Q_flow, {**radiation, **convection, **ventilation}
    
    # 테스트 시나리오
    print(f"\n=== 통합 테스트 시나리오 ===")
    
    # 1. 초기 상태
    print(f"1. 초기 상태:")
    print(f"   스크린 온도: {screen.T - 273.15:.1f}°C")
    print(f"   공기 온도: {T_air - 273.15:.1f}°C")
    print(f"   상부 공기 온도: {T_air_top - 273.15:.1f}°C")
    print(f"   하부 파이프 온도: {T_pipe_low - 273.15:.1f}°C")
    print(f"   상부 파이프 온도: {T_pipe_up - 273.15:.1f}°C")
    
    # 2. 열전달 계산
    dt = 60  # 1분
    print(f"\n2. 열전달 계산 (dt={dt}초):")
    
    total_Q_flow, heat_flows = calculate_total_heat_transfer()
    
    print(f"   스크린 열 균형 구성요소:")
    for name, value in heat_flows.items():
        print(f"     {name}: {value:.2f} W")
    
    print(f"   총 스크린 열유속: {total_Q_flow:.2f} W")
    
    # 3. 스크린 온도 업데이트
    screen.Q_flow = total_Q_flow
    old_screen_temp = screen.T
    screen.step(dt)
    temp_change = screen.T - old_screen_temp
    
    print(f"\n3. 스크린 온도 변화:")
    print(f"   이전 온도: {old_screen_temp - 273.15:.1f}°C")
    print(f"   현재 온도: {screen.T - 273.15:.1f}°C")
    print(f"   온도 변화: {temp_change:.2f} K")
    
    # 4. 장시간 시뮬레이션
    print(f"\n4. 장시간 시뮬레이션 (10분):")
    total_time = 600  # 10분
    steps = total_time // dt
    
    screen.T = 298.15  # 초기화
    
    for i in range(steps):
        total_Q_flow, _ = calculate_total_heat_transfer()
        screen.Q_flow = total_Q_flow
        screen.step(dt)
        
        if i % 5 == 0:  # 5분마다 출력
            print(f"   {i*dt/60:.0f}분: {screen.T - 273.15:.1f}°C, 열유속: {screen.Q_flow:.0f} W")
    
    print(f"   최종 온도: {screen.T - 273.15:.1f}°C")
    
    # 5. 스크린 폐쇄율 변화 테스트
    print(f"\n5. 스크린 폐쇄율 변화 테스트:")
    screen.T = 298.15
    
    for sc_value in [0.0, 0.5, 1.0]:
        screen.set_screen_closure(sc_value)
        total_Q_flow, _ = calculate_total_heat_transfer()
        screen.Q_flow = total_Q_flow
        screen.step(dt)
        
        print(f"   SC={sc_value:.1f}: 온도 {screen.T - 273.15:.1f}°C, 열유속 {screen.Q_flow:.0f} W")
    
    # 6. 열 균형 분석
    print(f"\n6. 열 균형 분석:")
    screen.T = 298.15
    total_Q_flow, heat_flows = calculate_total_heat_transfer()
    
    print(f"   스크린 열 균형 상세 분석:")
    print(f"     복사 열전달:")
    for name, value in heat_flows.items():
        if 'rad' in name:
            print(f"       {name}: {value:.2f} W")
    
    print(f"     대류 열전달:")
    for name, value in heat_flows.items():
        if 'cnv' in name:
            print(f"       {name}: {value:.2f} W")
    
    print(f"     환기 열전달:")
    for name, value in heat_flows.items():
        if 'ven' in name:
            print(f"       {name}: {value:.2f} W")
    
    print(f"     총 열유속: {total_Q_flow:.2f} W")
    
    # 열 균형 방향 분석
    positive_heat = sum(value for value in heat_flows.values() if value > 0)
    negative_heat = sum(value for value in heat_flows.values() if value < 0)
    
    print(f"     스크린으로 들어오는 열: {positive_heat:.2f} W")
    print(f"     스크린에서 나가는 열: {abs(negative_heat):.2f} W")
    print(f"     순 열유속: {positive_heat + negative_heat:.2f} W")
    
    return screen, heat_flows

if __name__ == "__main__":
    print("ThermalScreen 클래스 테스트 시작\n")
    
    try:
        # 기본 기능 테스트
        test_thermal_screen_basic()
        
        # 열전달 테스트
        test_thermal_screen_heat_transfer()
        
        # 엣지 케이스 테스트
        test_thermal_screen_edge_cases()
        
        # 온실 시나리오 테스트
        test_thermal_screen_greenhouse_scenario()
        
        # 실제 온실 조건 시나리오 테스트
        test_thermal_screen_realistic_scenario()
        
        # 통합 테스트 (원본 모델 구조)
        test_thermal_screen_integrated()
        
        print("\n=== 모든 테스트 완료 ===")
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc() 