import numpy as np
import matplotlib.pyplot as plt
from ControlSystems.Climate.Uvents_RH_T_Mdot import Uvents_RH_T_Mdot

# =====================
# 테스트 목적: 난방수 유량(Mdot, Heating Water Mass Flow Rate)이 환기 개폐율(U_vents)에 미치는 영향 분석
# 실제 온실 코드와 의미를 일치시킴
# =====================

sim_time = 6 * 3600  # 6시간 [초]
dt = 1.0            # 1분 간격 [초]
n_steps = int(sim_time / dt)
times = np.arange(n_steps) * dt / 3600  # time [h]

# Scenario 1: Heating water flow change (temperature, setpoint fixed)
T_air_profile1 = np.full(n_steps, 25+273.15)                # 25°C fixed
T_air_sp_profile1 = np.full(n_steps, 20+273.15)             # Setpoint 20°C fixed
Mdot_profile1 = np.linspace(0, 1.0, n_steps)                # Heating water flow 0~1 kg/s

# Scenario 2: Temperature change (heating water flow, setpoint fixed)
T_air_profile2 = np.linspace(15+273.15, 35+273.15, n_steps) # 15°C→35°C
T_air_sp_profile2 = np.full(n_steps, 20+273.15)             # Setpoint 20°C fixed
Mdot_profile2 = np.full(n_steps, 0.5)                       # Heating water flow 0.5 kg/s fixed

# Scenario 3: Setpoint change (temperature, heating water flow fixed)
T_air_profile3 = np.full(n_steps, 25+273.15)                # 25°C fixed
T_air_sp_profile3 = np.linspace(35+273.15, 10+273.15, n_steps)  # 35°C→10°C
Mdot_profile3 = np.full(n_steps, 0.5)                       # Heating water flow 0.5 kg/s fixed

# Results
y1 = np.zeros(n_steps)
y2 = np.zeros(n_steps)
y3 = np.zeros(n_steps)

# Scenario 1: Heating water flow change
uvent1 = Uvents_RH_T_Mdot()
for i in range(n_steps):
    uvent1.T_air = T_air_profile1[i]
    uvent1.T_air_sp = T_air_sp_profile1[i]
    uvent1.Mdot = Mdot_profile1[i]
    uvent1.RH_air = 0.7  # Relative humidity 70% fixed
    y1[i] = uvent1.step(dt)

# Scenario 2: Temperature change
uvent2 = Uvents_RH_T_Mdot()
for i in range(n_steps):
    uvent2.T_air = T_air_profile2[i]
    uvent2.T_air_sp = T_air_sp_profile2[i]
    uvent2.Mdot = Mdot_profile2[i]
    uvent2.RH_air = 0.7
    y2[i] = uvent2.step(dt)

# Scenario 3: Setpoint change
uvent3 = Uvents_RH_T_Mdot()
for i in range(n_steps):
    uvent3.T_air = T_air_profile3[i]
    uvent3.T_air_sp = T_air_sp_profile3[i]
    uvent3.Mdot = Mdot_profile3[i]
    uvent3.RH_air = 0.7
    y3[i] = uvent3.step(dt)

# Plot graphs
plt.figure(figsize=(15, 10))

plt.subplot(3, 1, 1)
plt.plot(times, y1, label='U_vents (Heating Water Flow Change)')
plt.plot(times, Mdot_profile1, label='Heating Water Flow (kg/s)', linestyle='--')
plt.ylabel('U_vents (0~1)')
plt.title('Scenario 1: Heating Water Flow Change (Temp 25°C, Setpoint 20°C)')
plt.legend()

plt.subplot(3, 1, 2)
plt.plot(times, y2, label='U_vents (Temperature Change)')
plt.plot(times, T_air_profile2-273.15, label='Temperature (°C)', linestyle='--')
plt.ylabel('U_vents (0~1)')
plt.title('Scenario 2: Temperature Change (Heating Water Flow 0.5kg/s, Setpoint 20°C)')
plt.legend()

plt.subplot(3, 1, 3)
plt.plot(times, y3, label='U_vents (Setpoint Change)')
plt.plot(times, T_air_sp_profile3-273.15, label='Setpoint (°C)', linestyle='--')
plt.ylabel('U_vents (0~1)')
plt.xlabel('Time [h]')
plt.title('Scenario 3: Setpoint Change (Temp 25°C, Heating Water Flow 0.5kg/s)')
plt.legend()

plt.tight_layout()
plt.show()

# =====================
# Difficulty: Mid
# Keywords: Heating Water Flow, Mass Flow Rate, PID, Ventilation Control, Scenario Test, Greenhouse
# ===================== 