from Greenhouse_1 import Greenhouse_1

# 온실 모델 초기화 (시간 단위가 초이므로 time_unit_scaling=1)
greenhouse = Greenhouse_1(time_unit_scaling=1)

print("=== 날씨 데이터 검증 ===")
print("시간(h) | 외기온도(°C) | 상대습도(%) | 일사량(W/m²) | 풍속(m/s) | 하늘온도(°C)")
print("-" * 80)
for test_t in [0, 10800, 21600, 32400, 43200]:  # 0, 3, 6, 9, 12시간 (초 단위)
    weather = greenhouse.TMY_and_control.get_value(test_t, interpolate=True)
    print(f"{test_t/3600:6.1f} | {weather['T_out']:10.1f} | {weather['RH_out']:10.1f} | "
          f"{weather['I_glob']:10.1f} | {weather['u_wind']:8.1f} | {weather['T_sky']:10.1f}")

print("\n=== 설정값 데이터 검증 ===")
print("시간(h) | 온도설정(°C) | CO2설정(ppm)")
print("-" * 50)
for test_t in [0, 10800, 21600, 32400, 43200]:  # 0, 3, 6, 9, 12시간 (초 단위)
    setpoint = greenhouse.SP_new.get_value(test_t, interpolate=True)
    print(f"{test_t/3600:6.1f} | {setpoint['T_sp']:10.1f} | {setpoint['CO2_sp']:10.1f}")

print("\n=== 스크린 사용가능 데이터 검증 ===")
print("시간(h) | 스크린사용가능")
print("-" * 30)
for test_t in [0, 10800, 21600, 32400, 43200]:  # 0, 3, 6, 9, 12시간 (초 단위)
    sc_usable = greenhouse.SC_usable.get_value(test_t, interpolate=True)
    print(f"{test_t/3600:6.1f} | {sc_usable['SC_usable']:10.1f}")
