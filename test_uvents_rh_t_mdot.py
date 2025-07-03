import numpy as np
import matplotlib.pyplot as plt
from ControlSystems.Climate.Uvents_RH_T_Mdot import Uvents_RH_T_Mdot

# 테스트 시나리오 설정
# =====================
sim_time = 6 * 3600  # 6시간 [초]
dt = 60.0            # 1분 간격 [초]
n_steps = int(sim_time / dt)
times = np.arange(n_steps) * dt / 3600  # 시간 [h]

# 시나리오 1: 온도 변화 (습도, 유량 고정)
T_air_profile = np.linspace(15+273.15, 35+273.15, n_steps)  # 15°C → 35°C
RH_air_profile = np.full(n_steps, 0.7)                      # 70% 고정
Mdot_profile = np.full(n_steps, 0.5)                        # 0.5 kg/s 고정

# 시나리오 2: 습도 변화 (온도, 유량 고정)
T_air_profile2 = np.full(n_steps, 25+273.15)                # 25°C 고정
RH_air_profile2 = np.linspace(0.4, 0.95, n_steps)           # 40% → 95%
Mdot_profile2 = np.full(n_steps, 0.5)                       # 0.5 kg/s 고정

# 시나리오 3: 질량유량 변화 (온도, 습도 고정)
T_air_profile3 = np.full(n_steps, 25+273.15)                # 25°C 고정
RH_air_profile3 = np.full(n_steps, 0.7)                     # 70% 고정
Mdot_profile3 = np.linspace(0.01, 1.0, n_steps)             # 0.01 → 1.0 kg/s

# 결과 저장용 배열
y1 = np.zeros(n_steps)
y2 = np.zeros(n_steps)
y3 = np.zeros(n_steps)

# 시나리오 1 실행
uvent1 = Uvents_RH_T_Mdot()
for i in range(n_steps):
    uvent1.T_air = T_air_profile[i]
    uvent1.T_air_sp = 25+273.15
    uvent1.Mdot = Mdot_profile[i]
    uvent1.RH_air = RH_air_profile[i]
    y1[i] = uvent1.step(dt)

# 시나리오 2 실행
uvent2 = Uvents_RH_T_Mdot()
for i in range(n_steps):
    uvent2.T_air = T_air_profile2[i]
    uvent2.T_air_sp = 25+273.15
    uvent2.Mdot = Mdot_profile2[i]
    uvent2.RH_air = RH_air_profile2[i]
    y2[i] = uvent2.step(dt)

# 시나리오 3 실행
uvent3 = Uvents_RH_T_Mdot()
for i in range(n_steps):
    uvent3.T_air = T_air_profile3[i]
    uvent3.T_air_sp = 25+273.15
    uvent3.Mdot = Mdot_profile3[i]
    uvent3.RH_air = RH_air_profile3[i]
    y3[i] = uvent3.step(dt)

# 그래프 출력
plt.figure(figsize=(12, 8))

plt.subplot(3, 1, 1)
plt.plot(times, y1, label='Ventilation (온도 변화)')
plt.ylabel('U_vents (0~1)')
plt.title('시나리오 1: 온도 변화 (습도 70%, 유량 0.5kg/s)')
plt.legend()

plt.subplot(3, 1, 2)
plt.plot(times, y2, label='Ventilation (습도 변화)', color='orange')
plt.ylabel('U_vents (0~1)')
plt.title('시나리오 2: 습도 변화 (온도 25°C, 유량 0.5kg/s)')
plt.legend()

plt.subplot(3, 1, 3)
plt.plot(times, y3, label='Ventilation (유량 변화)', color='green')
plt.xlabel('시간 [h]')
plt.ylabel('U_vents (0~1)')
plt.title('시나리오 3: 질량유량 변화 (온도 25°C, 습도 70%)')
plt.legend()

plt.tight_layout()
plt.show()

# =====================
# 난이도: Easy
# 주요 키워드: Ventilation Control, PID, Scenario Test, Greenhouse
# ===================== 