import numpy as np
import matplotlib.pyplot as plt
from Greenhouse_1 import Greenhouse_1

def simulate_greenhouse():
    # Create greenhouse model (time 컬럼이 '시간(ℎ)' 단위이므로 3600을 넘겨줍니다)
    greenhouse = Greenhouse_1(time_unit_scaling=3600)
    
    # Simulation parameters
    dt = 60                    # Time step [s]
    sim_time = 24 * 60 * 60     # 24 hours simulation → 86400 s
    n_steps = int(sim_time / dt)
    
    # Storage for results
    times = np.linspace(0, sim_time/3600, n_steps)  # Time in hours [0…24]
    results = {
        'T_air':         np.zeros(n_steps),
        'RH_air':        np.zeros(n_steps),
        'T_canopy':      np.zeros(n_steps),
        'T_cover':       np.zeros(n_steps),
        'T_floor':       np.zeros(n_steps),
        'q_tot':         np.zeros(n_steps),
        'E_th_tot_kWhm2':np.zeros(n_steps),
        'E_el_tot_kWhm2':np.zeros(n_steps),
        'CO2_air':       np.zeros(n_steps),
        'SC':            np.zeros(n_steps),
        'vent_opening':  np.zeros(n_steps),
        'DM_Har':        np.zeros(n_steps),
    }
    
    # Simulation loop
    for i in range(n_steps):
        state = greenhouse.step(dt, i)
        
        # Store
        for key, arr in results.items():
            arr[i] = state[key]
        
        # 디버깅 출력 (10 스텝마다)
        if i % 10 == 0:
            print(f"\n=== Step {i} | t={times[i]:.2f} h ===")
            print(f" T_air={state['T_air']:.2f}°C, RH_air={state['RH_air']:.1f}%, CO2={state['CO2_air']:.1f} ppm")
            print(f" q_tot={state['q_tot']:.1f} W/m², E_th={state['E_th_tot_kWhm2']:.2f} kWh/m², "
                  f"E_el={state['E_el_tot_kWhm2']:.2f} kWh/m²")
            print(f" SC={state['SC']:.2f}, vent={state['vent_opening']:.2f}, DM_Har={state['DM_Har']:.2f} mg/m²")
    
    # -- Plotting --
    plt.figure(figsize=(15, 15))
    
    # 1) Temperature
    plt.subplot(4,2,1)
    plt.plot(times, results['T_air'],    label='Air')
    plt.plot(times, results['T_canopy'], label='Canopy')
    plt.plot(times, results['T_cover'],  label='Cover')
    plt.plot(times, results['T_floor'],  label='Floor')
    plt.title('Temperatures'); plt.xlabel('Time [h]'); plt.ylabel('°C')
    plt.legend(); plt.grid(True)
    
    # 2) Humidity
    plt.subplot(4,2,2)
    plt.plot(times, results['RH_air'])
    plt.title('Air RH'); plt.xlabel('Time [h]'); plt.ylabel('%'); plt.grid(True)
    
    # 3) Heat flux
    plt.subplot(4,2,3)
    plt.plot(times, results['q_tot'])
    plt.title('Total Heat Flux'); plt.xlabel('Time [h]'); plt.ylabel('W/m²'); plt.grid(True)
    
    # 4) Energy
    plt.subplot(4,2,4)
    plt.plot(times, results['E_th_tot_kWhm2'], label='Thermal')
    plt.plot(times, results['E_el_tot_kWhm2'],  label='Electrical')
    plt.title('Accumulated Energy'); plt.xlabel('Time [h]'); plt.ylabel('kWh/m²')
    plt.legend(); plt.grid(True)
    
    # 5) CO2
    plt.subplot(4,2,5)
    plt.plot(times, results['CO2_air'])
    plt.title('CO₂ Concentration'); plt.xlabel('Time [h]'); plt.ylabel('ppm'); plt.grid(True)
    
    # 6) Control
    plt.subplot(4,2,6)
    plt.plot(times, results['SC'],           label='Screen')
    plt.plot(times, results['vent_opening'], label='Ventilation')
    plt.title('Control Variables'); plt.xlabel('Time [h]'); plt.ylabel('Opening'); plt.legend(); plt.grid(True)
    
    # 7) Tomato yield
    plt.subplot(4,2,7)
    plt.plot(times, results['DM_Har'])
    plt.title('Tomato Dry Matter'); plt.xlabel('Time [h]'); plt.ylabel('mg/m²'); plt.grid(True)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    simulate_greenhouse()
