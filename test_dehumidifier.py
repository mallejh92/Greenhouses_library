from ControlSystems.HVAC.Control_Dehumidifier import Control_Dehumidifier
import time
import numpy as np

def simulate_air_temperature(t):
    """Simulate air temperature with a sine wave"""
    return 293.15 - 2 + 1 * np.sin(t/100)  # 18°C ± 1°C

def simulate_air_humidity(t):
    """Simulate air humidity with a sine wave"""
    return 0.8 + 0.1 * np.sin(t/50)  # 80% ± 10%

def simulate_air_temperature_setpoint():
    """Simulate constant temperature setpoint"""
    return 283.15  # 20°C

def control_dehumidifier(dehum):
    """Simulate dehumidifier control"""
    print(f"Dehumidifier: {'ON' if dehum else 'OFF'}")

def control_humidity(cs):
    """Simulate humidity control signal"""
    print(f"Humidity control signal: {cs:.2f}")

def main():
    # 컨트롤러 인스턴스 생성
    controller = Control_Dehumidifier()
    
    print("Starting dehumidifier control test...")
    print("Press Ctrl+C to stop")
    
    try:
        t = 0
        while True:
            # 입력값 시뮬레이션
            T_air = simulate_air_temperature(t)
            air_RH = simulate_air_humidity(t)
            T_air_sp = simulate_air_temperature_setpoint()
            
            # 컨트롤러 업데이트
            dehum, cs = controller.update(T_air, air_RH, T_air_sp, dt=0.1)
            
            # 현재 상태 출력
            print(f"\nTime: {t:.1f}s")
            print(f"Air Temperature: {T_air-273.15:.1f}°C")
            print(f"Air Humidity: {air_RH*100:.1f}%")
            print(f"Target Humidity: {controller.RH_setpoint*100:.1f}%")
            
            # 제어 신호 적용
            control_dehumidifier(dehum)
            control_humidity(cs)
            
            # 시간 업데이트 및 지연
            t += 0.1
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")

if __name__ == "__main__":
    main() 