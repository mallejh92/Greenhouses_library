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
weather_df = pd.read_csv("10Dec-22Nov.txt", delimiter="\t", header=None)
weather_df.columns = ["hour", "T_air", "P_air", "RH", "I_glob", "wind", "T_sky", "VP", "lighting_on", "unused"]

# 온도/CO2 세트포인트 (Set-points)
sp_df = pd.read_csv("SP_10Dec-22Nov.txt", delimiter="\t", header=None)
sp_df.columns = ["hour", "T_set", "CO2_set"]

# 시뮬레이션 시간 설정
dt = 60                      # 60초 간격 (1분)
T_total = 3600 * 24 * 30         # 24시간
steps = T_total // dt
time = np.arange(0, T_total, dt) / 3600  # 단위: 시간

# 대한민국 5월 평균 조건 초기화
T_init = 288.15  # 15도C in Kelvin
VP_init = 1500   # 대기 수증기압 약 50% 상대습도

# 구성요소 초기화
air_vp = AirVP(V_air=1000, VP_start=VP_init)
surface_vp = SurfaceVP(T=T_init)
thermal_screen = ThermalScreen(A=1000, T_start=T_init)
cover = Cover(A=1000, T_start=T_init, phi=np.radians(30))
canopy = Canopy(A=1000, T_start=T_init)
floor = Floor(rho=1800, c_p=800, V=2, A=1000, T_start=T_init)

# 결과 저장 리스트
T_cover, T_canopy, T_floor, VP_air, I_sun = [], [], [], [], []

# 시뮬레이션 루프
for step in range(steps):
    hour = step * dt / 3600
    # 외부 일사량 (6시~18시만 작동), 최대 600 W/m²
    I = 600 * np.sin(np.pi * (hour - 6) / 12) if 6 <= hour <= 18 else 0

    # 단순 모델: 일사 에너지 일부가 각 구성요소로 전달 (예: 25%씩)
    cover.Q_flow = 0.25 * I * cover.A
    canopy.Q_flow = 0.25 * I * canopy.A
    floor.Q_flow = 0.25 * I * floor.A

    # 에너지 축적 계산 (단순 열에너지 적분)
    cover.T += dt * cover.Q_flow / (cover.rho * cover.c_p * cover.V)
    canopy.T += dt * canopy.Q_flow / (1200 * 3000 * 1)  # 임의의 열용량 적용
    floor.T += dt * floor.Q_flow / (floor.rho * floor.c_p * floor.V)

    # 수증기압 계산
    air_vp.T = canopy.T
    air_vp.MV_flow = 0.0001  # 증발량 (단순 모델)
    air_vp.update()

    # Surface VP, ThermalScreen 업데이트
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

# -------------------
# 결과 시각화
# -------------------
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
