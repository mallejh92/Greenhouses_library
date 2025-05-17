import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from Components.Greenhouse.Air import Air

# Air 클래스에 외부 조건 입력 메서드가 없으면 아래처럼 임시로 추가
def set_outside_conditions(self, T_out=None, RH_out=None):
    self.T_out = T_out
    self.RH_out = RH_out
Air.set_outside_conditions = set_outside_conditions

# Air 클래스에 외기와의 열교환을 반영하는 간단한 예시
def compute_derivatives_with_outside(self):
    if self.steadystate:
        dTdt = 0.0
    else:
        P_Air = self.compute_power_input()
        # 외기와의 열교환 추가 (임의의 열전달계수 10 W/m2K)
        Q_out = self.A * 10 * (self.T_out - self.T) if hasattr(self, 'T_out') and self.T_out is not None else 0.0
        dTdt = (self.Q_flow + P_Air + Q_out) / (self.rho * self.c_p * self.V)
    return dTdt
Air.compute_derivatives = compute_derivatives_with_outside

# 데이터 파일 읽기
df = pd.read_csv("10Dec-22Nov.txt", delimiter="\t", skiprows=2, header=None)
df.columns = ["time", "T_out", "RH_out", "P_out", "I_glob", "u_wind", "T_sky", "T_air_sp", "CO2_air_sp", "ilu_sp"]

# 온도 단위 변환 (섭씨 → 켈빈)
df["T_out"] = df["T_out"] + 273.15

# 시뮬레이션 파라미터
dt = 60  # 1분
n_steps = min(len(df), 24 * 60)  # 데이터 길이와 24시간 중 작은 값

# Air 객체 생성
air = Air(A=1000, h_Air=4.0, T_start=293.15)  # 초기 20도

# 결과 저장
T_in = np.zeros(n_steps)
RH_in = np.zeros(n_steps)
T_out = np.zeros(n_steps)
RH_out = np.zeros(n_steps)
time = np.zeros(n_steps)

for i in range(n_steps):
    T_out_K = df.loc[i, "T_out"]
    RH_out_val = df.loc[i, "RH_out"]
    T_out_C = T_out_K - 273.15
    Psat_out = 610.78 * np.exp(T_out_C / (T_out_C + 238.3) * 17.2694)
    VP_out = RH_out_val * Psat_out
    print(f"VP_out: {VP_out}")
    air.set_inputs(Q_flow=0, R_Air_Glob=None, massPort_VP=VP_out)
    air.step(dt)
    print(f"AirVP.VP: {air.airVP.VP}, T_in: {air.T-273.15}, Psat: {610.78 * np.exp((air.T-273.15) / ((air.T-273.15) + 238.3) * 17.2694)}, Psat_out: {Psat_out}, RH_in: {air.RH}")

    air.set_outside_conditions(T_out=T_out_K, RH_out=RH_out_val)
    air.set_inputs(Q_flow=0, R_Air_Glob=None, massPort_VP=VP_out)  # VP 입력!
    air.step(dt)
    T_out[i] = T_out_C
    RH_out[i] = RH_out_val
    time[i] = i * dt / 3600  # 시간(시)
    T_in[i] = air.T - 273.15
    RH_in[i] = air.RH
    # print(RH_in[i])

# 그래프 출력
plt.figure(figsize=(12, 6))
plt.subplot(2, 1, 1)
plt.plot(time, T_in, label='Greenhouse Air Temperature')
plt.plot(time, T_out, label='Outside Air Temperature', linestyle='--')
plt.ylabel('Temperature (°C)')
plt.legend()
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(time, RH_in, label='Greenhouse Air RH')
plt.plot(time, RH_out, label='Outside Air RH', linestyle='--')
plt.ylabel('Relative Humidity (%)')
plt.xlabel('Time (h)')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()