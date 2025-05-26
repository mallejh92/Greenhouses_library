import numpy as np
import matplotlib.pyplot as plt
from Greenhouse_1 import Greenhouse_1

def simulate_greenhouse():
    # Create greenhouse model
    greenhouse = Greenhouse_1()
    
    # Simulation parameters
    dt = 60  # Time step [s]
    sim_time = 24 * 100  # 24 hours simulation
    n_steps = int(sim_time / dt)
    
    # Storage for results
    times = np.linspace(0, sim_time/3600, n_steps)  # Time in hours
    results = {
        'T_air': np.zeros(n_steps),
        'RH_air': np.zeros(n_steps),
        'T_canopy': np.zeros(n_steps),
        'T_cover': np.zeros(n_steps),
        'T_floor': np.zeros(n_steps),
        'q_tot': np.zeros(n_steps),
        'E_th_tot_kWhm2': np.zeros(n_steps),
        'E_el_tot_kWhm2': np.zeros(n_steps),
        'CO2_air': np.zeros(n_steps),
        'SC': np.zeros(n_steps),
        'vent_opening': np.zeros(n_steps),
        'DM_Har': np.zeros(n_steps)  # 토마토 건물질 생산량 추가
    }
    
    # Simulation loop
    for i in range(n_steps):
        # Step simulation
        state = greenhouse.step(dt, i)
        
        # Store results
        for key in results:
            results[key][i] = state[key]
        
        # Print current state every 10 steps
        if i % 10 == 0:
            print(f"\n=== Step {i} ===")
            print(f"시간: {times[i]:.1f} 시간")
            print("\n[온도 (°C)]")
            print(f"공기: {state['T_air']:.2f}")
            print(f"캐노피: {state['T_canopy']:.2f}")
            print(f"커버: {state['T_cover']:.2f}")
            print(f"바닥: {state['T_floor']:.2f}")
            
            print("\n[습도 및 CO2]")
            print(f"상대습도: {state['RH_air']:.1f}%")
            print(f"CO2 농도: {state['CO2_air']:.1f} ppm")
            
            print("\n[에너지]")
            print(f"총 열유속: {state['q_tot']:.2f} W/m²")
            print(f"누적 열에너지: {state['E_th_tot_kWhm2']:.2f} kWh/m²")
            print(f"누적 전기에너지: {state['E_el_tot_kWhm2']:.2f} kWh/m²")
            
            print("\n[제어 변수]")
            print(f"스크린: {state['SC']:.2f}")
            print(f"환기 개도: {state['vent_opening']:.2f}")
            
            print("\n[작물 생장]")
            print(f"누적 건물중: {state['DM_Har']:.2f} mg/m²")
            print("=" * 50)
    
    # Create figure with subplots
    plt.figure(figsize=(15, 15))  # 그래프 크기 증가
    
    # Temperature plot
    plt.subplot(4, 2, 1)
    plt.plot(times, results['T_air'], label='Air')
    plt.plot(times, results['T_canopy'], label='Canopy')
    plt.plot(times, results['T_cover'], label='Cover')
    plt.plot(times, results['T_floor'], label='Floor')
    plt.grid(True)
    plt.xlabel('Time [hours]')
    plt.ylabel('Temperature [°C]')
    plt.title('Greenhouse Temperatures')
    plt.legend()
    
    # Humidity plot
    plt.subplot(4, 2, 2)
    plt.plot(times, results['RH_air'])
    plt.grid(True)
    plt.xlabel('Time [hours]')
    plt.ylabel('Relative Humidity [%]')
    plt.title('Greenhouse Air Humidity')
    
    # Heat flux plot
    plt.subplot(4, 2, 3)
    plt.plot(times, results['q_tot'])
    plt.grid(True)
    plt.xlabel('Time [hours]')
    plt.ylabel('Heat Flux [W/m²]')
    plt.title('Total Heat Flux')
    
    # Energy plot
    plt.subplot(4, 2, 4)
    plt.plot(times, results['E_th_tot_kWhm2'], label='Thermal')
    plt.plot(times, results['E_el_tot_kWhm2'], label='Electrical')
    plt.grid(True)
    plt.xlabel('Time [hours]')
    plt.ylabel('Energy [kW·h/m²]')
    plt.title('Accumulated Energy')
    plt.legend()
    
    # CO2 concentration plot
    plt.subplot(4, 2, 5)
    plt.plot(times, results['CO2_air'])
    plt.grid(True)
    plt.xlabel('Time [hours]')
    plt.ylabel('CO2 [ppm]')
    plt.title('CO2 Concentration')
    
    # Control variables plot
    plt.subplot(4, 2, 6)
    plt.plot(times, results['SC'], label='Screen')
    plt.plot(times, results['vent_opening'], label='Ventilation')
    plt.grid(True)
    plt.xlabel('Time [hours]')
    plt.ylabel('Opening [-]')
    plt.title('Control Variables')
    plt.legend()
    
    # Tomato yield plot
    plt.subplot(4, 2, 7)
    plt.plot(times, results['DM_Har'])
    plt.grid(True)
    plt.xlabel('Time [hours]')
    plt.ylabel('Dry Matter [mg/m²]')
    plt.title('Accumulated Tomato Dry Matter')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    simulate_greenhouse() 