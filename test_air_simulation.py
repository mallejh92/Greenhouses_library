import numpy as np
import matplotlib.pyplot as plt
from Components.Greenhouse.Air import Air

# 시뮬레이션 파라미터 설정
# ======================
dt = 60.0  # 시간 간격 [초] (1분)
sim_time = 24 * 3600  # 총 시뮬레이션 시간 [초] (24시간)
n_steps = int(sim_time / dt)

# Air 컴포넌트 생성 (면적 100m², 초기 온도 20°C, 초기 RH 50%)
air = Air(A=14000.0, T_start=293.15, h_Air=4.0)

# 결과 저장용 배열
times = np.arange(n_steps) * dt / 3600  # 시간 [h]
temps = np.zeros(n_steps)
rhs = np.zeros(n_steps)

# 외부 조건 시나리오 (예시)
Q_flow_profile = np.zeros(n_steps)  # 열유입 [W]
Q_flow_profile[200:600] = 5000      # 200~600분 구간에 5kW 열유입
VP_out_profile = np.full(n_steps, 1000.0)  # 외부 수증기압 [Pa]
VP_out_profile[400:800] = 2000.0           # 400~800분 구간에 외부 습도 증가

# 시뮬레이션 루프
for i in range(n_steps):
    # 외부 조건 적용 (난방, 환기 등)
    air.set_inputs(Q_flow=Q_flow_profile[i])
    air.massPort_VP = VP_out_profile[i]  # 외부 수증기압을 내부로 강제 주입(환기 효과)
    # 1스텝 진행
    T, RH = air.step(dt)
    temps[i] = T - 273.15  # [°C]
    rhs[i] = RH * 100      # [%]

# 결과 시각화
plt.figure(figsize=(10, 5))
plt.subplot(2, 1, 1)
plt.plot(times, temps, label='Air Temperature [°C]')
plt.ylabel('Temperature [°C]')
plt.legend()
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(times, rhs, label='Relative Humidity [%]')
plt.xlabel('Time [h]')
plt.ylabel('RH [%]')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show() 