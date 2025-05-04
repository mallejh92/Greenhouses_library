import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1. 외부 환경 및 세트포인트 데이터 로드
weather_df = pd.read_csv("./10Dec-22Nov.txt", delimiter="\t", skiprows=2, header=None)
weather_df.columns = ["time", "T_air", "P_air", "RH", "I_glob", "wind", "T_sky", "VP", "lighting_on", "unused"]

sp_df = pd.read_csv("./SP_10Dec-22Nov.txt", delimiter="\t", skiprows=2, header=None)
sp_df.columns = ["time", "T_set", "CO2_set"]

# time을 기준으로 데이터프레임 병합
merged_df = pd.merge(weather_df, sp_df, on='time', how='inner')

# 2. 시뮬레이션 파라미터 및 초기값 설정
time_step = 3600  # 1시간 간격 (초)
E_th_tot_kWhm2 = 0
E_el_tot_kWhm2 = 0
DM_Har = 0

T_air = 293.15  # 초기 온도 (K)
CO2_air = 800 * 1.94  # 초기 CO2 농도 (mg/m3)

# 3. 메인 시뮬레이션 루프
for i in range(len(weather_df)):
    # 입력값
    T_out = weather_df.loc[i, "T_air"] + 273.15
    I_glob = weather_df.loc[i, "I_glob"]
    wind = weather_df.loc[i, "wind"]
    VP_out = weather_df.loc[i, "VP"]
    T_sky = weather_df.loc[i, "T_sky"] + 273.15
    lighting_on = weather_df.loc[i, "lighting_on"]

    T_set = sp_df.loc[i, "T_set"] + 273.15
    CO2_set = sp_df.loc[i, "CO2_set"] * 1.94

    # PI 제어로 유량 결정
    error_T = T_set - T_air
    mdot = np.clip(0.7 * error_T, 0, 86.75)  # kg/h

    # 난방 열량 계산 (kWh)
    Cp = 4.18  # kJ/kg·K
    Q_dot = mdot * Cp * (363.15 - T_air)  # kJ/h
    Q_kWh = Q_dot / 3600
    E_th_tot_kWhm2 += max(Q_kWh, 0) / 14000  # 면적 14000 m2로 나눔

    # 조명 에너지
    if lighting_on:
        W_el = 500 / 1000  # 0.5 kW/m2
    else:
        W_el = 0
    E_el_tot_kWhm2 += W_el

    # 작물 생육 모델 (선형 간이 모델)
    PAR = I_glob * 0.48 + (500 if lighting_on else 0)
    DM_Har += 0.01 * PAR * 1  # mg/m2

    # 온도 업데이트 (간단한 열평형 가정)
    T_air += (Q_kWh * 3600 / (1.2 * 1005 * 14000))

# 4. 결과 출력 및 시각화
print(f"총 난방 에너지: {E_th_tot_kWhm2:.2f} kWh/m2")
print(f"총 조명 에너지: {E_el_tot_kWhm2:.2f} kWh/m2")
print(f"총 건물 수확량: {DM_Har:.2f} mg/m2")

plt.plot(merged_df["time"], merged_df["T_set"], label="Set Temp (°C)")
plt.plot(merged_df["time"], [T_air - 273.15]*len(merged_df), label="Final Indoor Temp (°C)")
plt.legend()
plt.xlabel("Time")
plt.ylabel("Temperature (°C)")
plt.title("Indoor Temperature vs Set Point")
plt.grid()
plt.show()
