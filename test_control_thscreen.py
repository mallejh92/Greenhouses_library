import numpy as np
import matplotlib.pyplot as plt
from ControlSystems.Climate.Control_ThScreen import Control_ThScreen

# 시뮬레이션 파라미터
sim_time = 6 * 3600  # 6 hours (seconds)
dt = 60              # 1초 간격 (초)
n_steps = int(sim_time // dt)
times = np.arange(0, sim_time, dt) / 3600  # 시간(h)

# 입력 시나리오 생성 (간단한 온실 환경)
T_air_sp = np.full(n_steps, 20 + 273.15)  # Setpoint 20°C
Tout_Kelvin = np.linspace(10 + 273.15, 18 + 273.15, n_steps)  # 외부 온도 10→18°C
RH_air = np.concatenate([
    np.full(n_steps//3, 0.7),
    np.full(n_steps//3, 0.9),
    np.full(n_steps - 2*(n_steps//3), 0.6)
])  # 습도: 0.7→0.9→0.6
R_Glob_can = np.concatenate([
    np.zeros(n_steps//4),
    np.full(n_steps//2, 100),
    np.zeros(n_steps - (n_steps//4 + n_steps//2))
])  # 일사량: 밤-낮-밤
SC_usable = np.ones(n_steps)  # 항상 사용 가능

# 제어기 인스턴스 생성
controller = Control_ThScreen()

# 결과 저장용 배열
SC_values = np.zeros(n_steps)
state_names = []

# 시뮬레이션 루프
for i in range(n_steps):
    controller.T_air_sp = T_air_sp[i]
    controller.Tout_Kelvin = Tout_Kelvin[i]
    controller.RH_air = RH_air[i]
    controller.R_Glob_can = R_Glob_can[i]
    controller.SC_usable = SC_usable[i]
    SC_values[i] = controller.step(dt)
    state_names.append(controller.state)

# 상태별 색상 매핑
unique_states = list(set(state_names))
state_colors = {s: plt.cm.tab10(i) for i, s in enumerate(unique_states)}
state_color_arr = [state_colors[s] for s in state_names]

# 결과 시각화 (영어)
fig, axs = plt.subplots(4, 1, figsize=(10, 12), sharex=True)

axs[0].plot(times, T_air_sp - 273.15, label='Setpoint Temp (°C)')
axs[0].plot(times, Tout_Kelvin - 273.15, label='Outdoor Temp (°C)')
axs[0].set_ylabel('Temperature (°C)')
axs[0].legend()
axs[0].set_title('Greenhouse Temperature Scenario')

axs[1].plot(times, RH_air * 100, label='Relative Humidity (%)')
axs[1].set_ylabel('RH (%)')
axs[1].legend()
axs[1].set_title('Greenhouse Humidity Scenario')

axs[2].plot(times, R_Glob_can, label='Global Radiation (W/m²)')
axs[2].set_ylabel('Radiation (W/m²)')
axs[2].legend()
axs[2].set_title('Global Radiation Scenario')

axs[3].plot(times, SC_values, label='Thermal Screen Closure (SC)')
# 상태별 색상으로 배경 표시
for i in range(n_steps-1):
    axs[3].axvspan(times[i], times[i+1], color=state_color_arr[i], alpha=0.5)
axs[3].set_ylabel('SC (0=open, 1=closed)')
axs[3].set_xlabel('Time (h)')
axs[3].legend()
axs[3].set_title('Thermal Screen Control Output & State')

# 범례에 상태별 색상 추가
from matplotlib.patches import Patch
handles = [Patch(color=state_colors[s], label=s) for s in unique_states]
axs[3].legend(handles=handles + [axs[3].lines[0]], loc='upper right')

plt.tight_layout()
plt.show() 