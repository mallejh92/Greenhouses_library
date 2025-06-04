import numpy as np
import matplotlib.pyplot as plt
from Flows.HeatTransfer.SoilConduction import SoilConduction

def test_soil_conduction():
    # 시뮬레이션 파라미터
    A = 1.4e4  # 바닥 면적 [m²]
    dt = 300  # 시간 간격 [s] (5분)
    simulation_time = 3600 * 24  # 24시간
    steps = int(simulation_time / dt)

    # 테스트 케이스
    soil1 = SoilConduction(A=A, N_c=1, N_s=5, lambda_c=1.7, lambda_s=0.85)
    soil2 = SoilConduction(A=A, N_c=2, N_s=5, lambda_c=1.7, lambda_s=0.85)
    soil3 = SoilConduction(A=A, N_c=0, N_s=5, lambda_c=1.7, lambda_s=0.85)

    # 결과 저장용 배열
    time = np.linspace(0, simulation_time, steps)
    Q_flow1 = np.zeros(steps)
    Q_flow2 = np.zeros(steps)
    Q_flow3 = np.zeros(steps)
    T_layers1 = np.zeros((steps, soil1.N_s + (soil1.N_c if soil1.N_c > 1 else 1)))
    T_layers2 = np.zeros((steps, (soil2.N_c-1) + soil2.N_s))
    T_layers3 = np.zeros((steps, soil3.N_s))

    for i in range(steps):
        # 상단 경계 조건 (온실 바닥 온도)
        T_top = 293.15 + 0.6 * np.sin(2 * np.pi * time[i] / (24 * 3600))
        soil1.port_a.T = T_top
        soil2.port_a.T = T_top
        soil3.port_a.T = T_top

        # 하단 경계 조건 (심토양 온도)
        soil1.soil.T = 283.15
        soil2.soil.T = 283.15
        soil3.soil.T = 283.15

        # 열전달 계산
        Q_flow1[i] = soil1.calculate()
        Q_flow2[i] = soil2.calculate()
        Q_flow3[i] = soil3.calculate()

        # 레이어 온도 저장
        # Case 1 (N_c=1)
        if soil1.N_c > 0:
            if soil1.N_c == 1:
                T_layers1[i, 0] = soil1.TC_cc.port_b.T
            else:
                for j in range(len(soil1.Layer_c)):
                    T_layers1[i, j] = soil1.Layer_c[j].heatPort.T
        for j in range(soil1.N_s):
            T_layers1[i, soil1.N_c + j] = soil1.Layer_s[j].heatPort.T

        # Case 2 (N_c=2)
        for j in range(soil2.N_c-1):
            T_layers2[i, j] = soil2.Layer_c[j].heatPort.T
        for j in range(soil2.N_s):
            T_layers2[i, (soil2.N_c-1) + j] = soil2.Layer_s[j].heatPort.T

        # Case 3 (N_c=0)
        for j in range(soil3.N_s):
            T_layers3[i, j] = soil3.Layer_s[j].heatPort.T

        # 6시간(21600초)마다 각 레이어 온도 프린트
        if i % int(21600/dt) == 0:
            hour = int(time[i] // 3600)
            print(f"\n[{hour}시간 경과]")
            print("Case 1 (N_c=1):", [f"{T_layers1[i, j]-273.15:.2f}°C" for j in range(T_layers1.shape[1])])
            print("Case 2 (N_c=2):", [f"{T_layers2[i, j]-273.15:.2f}°C" for j in range(T_layers2.shape[1])])
            print("Case 3 (N_c=0):", [f"{T_layers3[i, j]-273.15:.2f}°C" for j in range(T_layers3.shape[1])])

        # 시간 진행
        soil1.step(dt)
        soil2.step(dt)
        soil3.step(dt)

    # 결과 시각화
    plt.figure(figsize=(15, 10))

    # 열전달량 플롯
    plt.subplot(2, 1, 1)
    plt.plot(time/3600, Q_flow1, label='N_c=1')
    plt.plot(time/3600, Q_flow2, label='N_c=2')
    plt.plot(time/3600, Q_flow3, label='N_c=0')
    plt.xlabel('Time [h]')
    plt.ylabel('Heat Flow [W]')
    plt.title('Heat Flow Rate')
    plt.legend()
    plt.grid(True)

    # 레이어 온도 플롯
    plt.subplot(2, 1, 2)
    for j in range(T_layers1.shape[1]):
        plt.plot(time/3600, T_layers1[:, j] - 273.15, label=f'Case 1 Layer {j+1}', linestyle='--')
    for j in range(T_layers2.shape[1]):
        plt.plot(time/3600, T_layers2[:, j] - 273.15, label=f'Case 2 Layer {j+1}', linestyle=':')
    for j in range(T_layers3.shape[1]):
        plt.plot(time/3600, T_layers3[:, j] - 273.15, label=f'Case 3 Layer {j+1}', linestyle='-.')
    plt.xlabel('Time [h]')
    plt.ylabel('Temperature [°C]')
    plt.title('Layer Temperatures')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('soil_conduction_test_results.png')
    plt.show()

    # 최종 온도 출력
    print("\n최종 레이어 온도:")
    print("Case 1 (N_c=1):")
    for j in range(T_layers1.shape[1]):
        print(f"Layer {j+1}: {T_layers1[-1, j] - 273.15:.2f}°C")
    print("\nCase 2 (N_c=2):")
    for j in range(T_layers2.shape[1]):
        print(f"Layer {j+1}: {T_layers2[-1, j] - 273.15:.2f}°C")
    print("\nCase 3 (N_c=0):")
    for j in range(T_layers3.shape[1]):
        print(f"Layer {j+1}: {T_layers3[-1, j] - 273.15:.2f}°C")

if __name__ == "__main__":
    test_soil_conduction()