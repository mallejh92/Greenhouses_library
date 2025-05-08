import numpy as np
import matplotlib.pyplot as plt

from Components.Greenhouse.BasicComponents.AirVP import AirVP
from Components.Greenhouse.BasicComponents.SurfaceVP import SurfaceVP
from Components.Greenhouse.BasicComponents.Layer import Layer
from Components.Greenhouse.ThermalScreen import ThermalScreen
from Components.Greenhouse.Cover import Cover
from Components.Greenhouse.Canopy import Canopy
from Components.Greenhouse.Floor import Floor
import pandas as pd

# 외부 기상 데이터 (TMY)
weather_df = pd.read_csv("./10Dec-22Nov.txt", delimiter="\t", skiprows=2, header=None)
weather_df.columns = ["time", "T_air", "P_air", "RH", "I_glob", "wind", "T_sky", "VP", "lighting_on", "unused"]

# 온도/CO2 세트포인트 (Set-points)
sp_df = pd.read_csv("./SP_10Dec-22Nov.txt", delimiter="\t", skiprows=2, header=None)
sp_df.columns = ["time", "T_set", "CO2_set"]

# 시뮬레이션 시간 설정
dt = 60                      # 60초 간격 (1분)
T_total = 3600 * 24 * 30     # 30일 시뮬레이션
steps = T_total // dt
time = np.arange(0, T_total, dt) / 3600  # 단위: 시간

# 초기 조건
T_init = 288.15  # 15도C in Kelvin
VP_init = 1500   # 대기 수증기압 약 50% 상대습도

# 구성요소 초기화
air_vp = AirVP(V_air=14000, VP_start=VP_init)                     # 공기 체적 [m^3]
surface_vp = SurfaceVP(T=T_init)                                  # 표면 온도 [K]
thermal_screen = ThermalScreen(A=14000, T_start=T_init)           # 열화벽 면적 [m^2]    
cover = Cover(A=14000, rho=2600, c_p=840, T_start=T_init, phi=0.43633231299858)        # 덮개
canopy = Canopy(A=14000, T_start=T_init)                          # 작물층
floor = Floor(rho=1, c_p=2e6, V=140, A=14000, T_start=T_init)      # 바닥

# 결과 저장 리스트
T_cover, T_canopy, T_floor, VP_air, I_sun = [], [], [], [], []

# 시뮬레이션 루프
for step in range(steps):
    hour = step * dt / 3600
    data_idx = int(hour) % len(weather_df)

    # 현재 외부 기상 데이터
    T_out = weather_df.iloc[data_idx]["T_air"]
    RH_out = weather_df.iloc[data_idx]["RH"]
    I = weather_df.iloc[data_idx]["I_glob"]
    wind_speed = weather_df.iloc[data_idx]["wind"]
    T_sky = weather_df.iloc[data_idx]["T_sky"]

    # 세트포인트
    T_set = sp_df.iloc[data_idx]["T_set"]
    CO2_set = sp_df.iloc[data_idx]["CO2_set"]

    # 외부조건 기반 열전달
    cover.Q_flow = 0.3 * I * cover.A
    canopy.Q_flow = 0.4 * I * canopy.A
    floor.Q_flow = 0.3 * I * floor.A

    # 대류 열전달
    h_conv = 5.7 + 3.8 * wind_speed
    cover.Q_flow += h_conv * cover.A * (T_out - cover.T)

    # 복사 열전달
    sigma = 5.67e-8
    # 온도 차이를 이용한 선형화된 복사 열전달 계산
    T_avg = (T_sky + cover.T) / 2
    h_rad = 4 * sigma * T_avg**3  # 복사 열전달 계수
    cover.Q_flow += h_rad * cover.A * (T_sky - cover.T)

    # 에너지 축적
    cover.T += dt * cover.Q_flow / (cover.rho * cover.c_p * 1)
    canopy.T += dt * canopy.Q_flow / (1200 * 3000 * 1)  # 가정: 작물 밀도 및 비열
    floor.T += dt * floor.Q_flow / (floor.rho * floor.c_p * floor.V)

    # 수증기압 업데이트
    air_vp.T = canopy.T
    air_vp.MV_flow = 0.0001 * (1 - RH_out / 100) * (canopy.T - T_out)
    air_vp.update()

    surface_vp.T = canopy.T
    surface_vp.update()
    thermal_screen.T = canopy.T
    thermal_screen.update(Q_flow_input=0)

    # 결과 저장
    T_cover.append(cover.T)
    T_canopy.append(canopy.T)
    T_floor.append(floor.T)
    VP_air.append(air_vp.VP)
    I_sun.append(I)

# 시각화
plt.figure(figsize=(10, 5))
plt.plot(time, T_cover, label="Cover Temp (K)")
plt.plot(time, T_canopy, label="Canopy Temp (K)")
plt.plot(time, T_floor, label="Floor Temp (K)")
plt.xlabel("Time (hours)")
plt.ylabel("Temperature (K)")
plt.title("Greenhouse Component Temperatures")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 4))
plt.plot(time, VP_air, label="Air Vapor Pressure (Pa)", color='green')
plt.xlabel("Time (hours)")
plt.ylabel("Vapor Pressure (Pa)")
plt.title("Air Vapor Pressure")
plt.grid(True)
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 3))
plt.plot(time, I_sun, label="Incoming Solar Radiation (W/m²)", color='orange')
plt.xlabel("Time (hours)")
plt.ylabel("Irradiance (W/m²)")
plt.title("External Solar Irradiance")
plt.grid(True)
plt.tight_layout()
plt.show()