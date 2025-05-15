from ControlSystems.HVAC.Control_Dehumidifier import Control_Dehumidifier
import time


# 컨트롤러 인스턴스 생성
controller = Control_Dehumidifier()

# 시뮬레이션 루프
while True:
    # 입력값 읽기
    T_air = read_air_temperature()
    air_RH = read_air_humidity()
    T_air_sp = read_air_temperature_setpoint()
    
    # 컨트롤러 업데이트
    dehum, cs = controller.update(T_air, air_RH, T_air_sp, dt=0.1)
    
    # 제어 신호 적용
    control_dehumidifier(dehum)
    control_humidity(cs)
    
    # 시간 지연
    time.sleep(0.1)