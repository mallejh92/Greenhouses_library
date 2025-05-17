import numpy as np
import matplotlib.pyplot as plt
from Greenhouse_2 import Greenhouse_2

def simulate_greenhouse():
    try:
        greenhouse = Greenhouse_2()
        dt = 300  # Time step [s] (5분)
        sim_time = 24 * 3600  # 24 hours
        n_steps = int(sim_time / dt)

        times = np.linspace(0, sim_time/3600, n_steps)
        results = {
            'time': np.zeros(n_steps),
            'T_air': np.zeros(n_steps),
            'RH_air': np.zeros(n_steps),
            'T_canopy': np.zeros(n_steps),
            # 'LAI': np.zeros(n_steps),
            # 'R_SunCov_Glob': np.zeros(n_steps),
            # 'R_PAR_Can_umol': np.zeros(n_steps),
            # 'q_low': np.zeros(n_steps),
            # 'q_up': np.zeros(n_steps),
            'q_tot': np.zeros(n_steps),
            'E_th_tot_kWhm2': np.zeros(n_steps),
            'E_th_tot': np.zeros(n_steps),
            # 'W_el_illu': np.zeros(n_steps),
            # 'E_el_tot_kWhm2': np.zeros(n_steps),
            # 'E_el_tot': np.zeros(n_steps),
            # 'DM_Har': np.zeros(n_steps),
            # 'CO2_air': np.zeros(n_steps),
            # 'SC': np.zeros(n_steps),
            'vent_opening': np.zeros(n_steps)
        }

        print("시뮬레이션을 시작합니다. 중지하려면 Ctrl+C를 누르세요.")
        print(f"총 {n_steps} 스텝 (5분 간격)을 시뮬레이션합니다.")
        for i in range(n_steps):
            state = greenhouse.step(dt, i)
            for key in results:
                results[key][i] = state[key]
            if i % 12 == 0:  # 1시간마다 진행상황 출력 (12 * 5분 = 1시간)
                print(f"진행률: {i/n_steps*100:.1f}%")

        plt.figure(figsize=(15, 12))
        plt.subplot(3, 2, 1)
        plt.plot(times, results['T_air'], label='Air')
        plt.plot(times, results['T_canopy'], label='Canopy')
        plt.grid(True)
        plt.xlabel('Time [hours]')
        plt.ylabel('Temperature [°C]')
        plt.title('Greenhouse Temperatures')
        plt.legend()

        plt.subplot(3, 2, 2)
        plt.plot(times, results['RH_air'])
        plt.grid(True)
        plt.xlabel('Time [hours]')
        plt.ylabel('Relative Humidity [%]')
        plt.title('Greenhouse Air Humidity')

        plt.subplot(3, 2, 3)
        plt.plot(times, results['q_tot'])
        plt.grid(True)
        plt.xlabel('Time [hours]')
        plt.ylabel('Heat Flux [W/m²]')
        plt.title('Total Heat Flux')

        plt.subplot(3, 2, 4)
        plt.plot(times, results['E_th_tot_kWhm2'], label='Thermal')
        plt.grid(True)
        plt.xlabel('Time [hours]')
        plt.ylabel('Energy [kW·h/m²]')
        plt.title('Accumulated Energy')
        plt.legend()

        plt.subplot(3, 2, 5)
        plt.plot(times, results['vent_opening'])
        plt.grid(True)
        plt.xlabel('Time [hours]')
        plt.ylabel('Opening [-]')
        plt.title('Ventilation Opening')

        plt.tight_layout()
        plt.show()

    except KeyboardInterrupt:
        print("\n시뮬레이션이 사용자에 의해 중단되었습니다.")
        plt.close('all')  # 열려있는 모든 그래프 창을 닫습니다
    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")
        plt.close('all')

if __name__ == "__main__":
    simulate_greenhouse()