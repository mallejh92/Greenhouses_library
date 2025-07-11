import numpy as np
import matplotlib.pyplot as plt
from ControlSystems.PID import PID

# 디버깅: PID 개별 테스트
def test_individual_pid():
    """각 PID 컨트롤러가 제대로 작동하는지 개별 테스트"""
    
    print("🔍 PID 컨트롤러 개별 테스트")
    print("="*50)
    
    # 온도 PID 테스트
    pid_temp = PID(
        Kp=2.0,
        Ti=300,
        Td=0,
        CSstart=0.1,
        CSmin=0.0,
        CSmax=1.0,
        PVmin=10+273.15,
        PVmax=40+273.15
    )
    
    # 테스트 시나리오: 온도 20°C → 30°C, 설정값 22°C
    T_air = 30 + 273.15      # 현재 30°C
    T_air_sp = 20 + 273.15   # 설정값 20°C
    
    pid_temp.PV = T_air
    pid_temp.SP = T_air_sp + 2.0  # 22°C
    
    print(f"온도 PID 테스트:")
    print(f"  현재 온도: {T_air-273.15:.1f}°C")
    print(f"  설정값: {T_air_sp-273.15:.1f}°C")
    print(f"  PID 설정값: {(T_air_sp + 2.0)-273.15:.1f}°C")
    print(f"  오차: {T_air - (T_air_sp + 2.0):.1f}K")
    
    result = pid_temp.step(1.0)
    print(f"  PID 출력: {result:.3f}")
    
    # 습도 PID 테스트
    pid_humidity = PID(
        Kp=1.5,
        Ti=500,
        Td=0,
        CSstart=0.1,
        CSmin=0.0,
        CSmax=1.0,
        PVmin=0.4,
        PVmax=0.9
    )
    
    RH_air = 0.9  # 90% 습도
    pid_humidity.PV = RH_air
    pid_humidity.SP = 0.8     # 80% 설정값
    
    print(f"\n습도 PID 테스트:")
    print(f"  현재 습도: {RH_air*100:.1f}%")
    print(f"  설정값: {0.8*100:.1f}%")
    print(f"  오차: {(RH_air - 0.8)*100:.1f}%")
    
    result = pid_humidity.step(1.0)
    print(f"  PID 출력: {result:.3f}")

def test_scenario_detailed():
    """Scenario 2 상세 분석"""
    
    print(f"\n🔍 Scenario 2 상세 분석")
    print("="*50)
    
    # 온도 PID
    pid_temp = PID(
        Kp=2.0,
        Ti=300,
        Td=0,
        CSstart=0.1,
        CSmin=0.0,
        CSmax=1.0,
        PVmin=10+273.15,
        PVmax=40+273.15
    )
    
    # 습도 PID  
    pid_humidity = PID(
        Kp=1.5,
        Ti=500,
        Td=0,
        CSstart=0.1,
        CSmin=0.0,
        CSmax=1.0,
        PVmin=0.4,
        PVmax=0.9
    )
    
    # 테스트: 15°C, 25°C, 35°C에서의 동작
    temperatures = [15, 25, 35]
    T_air_sp = 20 + 273.15  # 설정값 20°C
    RH_air = 0.7            # 습도 70%
    Mdot = 0.5              # 난방수 유량
    
    for temp in temperatures:
        T_air = temp + 273.15
        
        # 온도 제어
        pid_temp.PV = T_air
        pid_temp.SP = T_air_sp + 2.0  # 22°C
        temp_control = pid_temp.step(1.0)
        
        # 습도 제어
        pid_humidity.PV = RH_air
        pid_humidity.SP = 0.8
        humidity_control = pid_humidity.step(1.0)
        
        # 난방 보정
        heating_factor = max(0.1, 1.0 - Mdot)  # 0.5
        
        # 최종 계산
        ventilation = max(temp_control, humidity_control) * heating_factor
        ventilation = np.clip(ventilation, 0.0, 1.0)
        
        print(f"\n온도 {temp}°C에서:")
        print(f"  온도 오차: {T_air - (T_air_sp + 2.0):.1f}K")
        print(f"  온도 제어: {temp_control:.3f}")
        print(f"  습도 제어: {humidity_control:.3f}")
        print(f"  난방 보정: {heating_factor:.3f}")
        print(f"  최종 환기: {ventilation:.3f}")

def test_corrected_logic():
    """수정된 제어 로직 테스트"""
    
    print(f"\n🔧 수정된 제어 로직 제안")
    print("="*50)
    
    # 더 강력한 PID 파라미터
    pid_temp = PID(
        Kp=5.0,      # 더 강한 비례 제어
        Ti=100,      # 더 빠른 적분 시간
        Td=0,
        CSstart=0.1,
        CSmin=0.0,
        CSmax=1.0,
        PVmin=10+273.15,
        PVmax=40+273.15
    )
    
    pid_humidity = PID(
        Kp=3.0,      # 더 강한 비례 제어
        Ti=200,      # 더 빠른 적분 시간
        Td=0,
        CSstart=0.1,
        CSmin=0.0,
        CSmax=1.0,
        PVmin=0.4,
        PVmax=0.9
    )
    
    # 테스트
    temperatures = [15, 25, 35]
    T_air_sp = 20 + 273.15
    RH_air = 0.7
    Mdot = 0.5
    
    print("수정된 파라미터로 테스트:")
    
    for temp in temperatures:
        T_air = temp + 273.15
        
        # 온도 제어 (설정값 대비 직접 비교)
        pid_temp.PV = T_air
        pid_temp.SP = T_air_sp  # 설정값 그대로 (여유분 제거)
        temp_control = pid_temp.step(1.0)
        
        # 습도 제어
        pid_humidity.PV = RH_air
        pid_humidity.SP = 0.75  # 75% (더 낮은 설정값)
        humidity_control = pid_humidity.step(1.0)
        
        # 간단한 로직: 온도 또는 습도 중 높은 값
        ventilation = max(temp_control, humidity_control)
        
        # 난방 보정 (더 약하게)
        if Mdot > 0.3:  # 난방 중일 때만
            ventilation *= 0.7  # 30% 감소
        
        ventilation = np.clip(ventilation, 0.0, 1.0)
        
        print(f"  온도 {temp}°C: 환기 {ventilation:.3f}")

if __name__ == "__main__":
    test_individual_pid()
    test_scenario_detailed()
    test_corrected_logic() 