# main.py

import numpy as np
import matplotlib.pyplot as plt

from components.greenhouse import GreenhouseClimateModel
from inputs.schedule import greenhouse_inputs  # 외부 입력 함수 (일사량 등)

def main():
    # 1. 시뮬레이션 설정 -------------------------
    params = {
        "A_glass": 100.0,      # m²
        "C_air": 1.0e5,        # J/K (열용량)
        "Q_loss": 500.0,       # W (열 손실)
        "V_air": 100.0         # m³ (공기 부피)
    }

    initial_state = [20.0, 1000.0, 600.0]  # [T_air (°C), Pv_air (Pa), CO2_air (ppm)]
    t_start, t_end = 0, 24  # 시간 범위: 0시 ~ 24시
    t_span = (t_start, t_end)

    # 2. 모델 생성 ------------------------------
    model = GreenhouseClimateModel(params)

    # 3. 시뮬레이션 실행 ------------------------
    t, results = model.simulate(t_span=t_span, y0=initial_state, inputs_fn=greenhouse_inputs)

    # 4. 결과 시각화 ----------------------------
    plot_results(t, results)

def plot_results(t, results):
    T_air, Pv_air, CO2_air = results

    plt.figure(figsize=(10, 6))

    plt.subplot(3, 1, 1)
    plt.plot(t, T_air, label="Air Temperature [°C]")
    plt.ylabel("T_air [°C]")
    plt.grid()

    plt.subplot(3, 1, 2)
    plt.plot(t, Pv_air, label="Vapor Pressure [Pa]", color="blue")
    plt.ylabel("Pv_air [Pa]")
    plt.grid()

    plt.subplot(3, 1, 3)
    plt.plot(t, CO2_air, label="CO2 Concentration [ppm]", color="green")
    plt.xlabel("Time [h]")
    plt.ylabel("CO2_air [ppm]")
    plt.grid()

    plt.tight_layout()
    plt.show()

# 진입점
if __name__ == "__main__":
    main()
