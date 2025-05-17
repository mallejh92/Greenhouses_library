import numpy as np
import matplotlib.pyplot as plt
from Greenhouse_1 import Greenhouse_1

def simulate_greenhouse():
    # Create greenhouse model
    greenhouse = Greenhouse_1()
    
    # Simulation parameters
    dt = 60  # Time step [s]
    sim_time = 24 * 3600  # 24 hours simulation
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
        'vent_opening': np.zeros(n_steps)
    }
    
    # Simulation loop
    for i in range(n_steps):
        # Step simulation
        state = greenhouse.step(dt, i)
        
        # Store results
        for key in results:
            results[key][i] = state[key]
    
    # Create figure with subplots
    plt.figure(figsize=(15, 12))
    
    # Temperature plot
    plt.subplot(3, 2, 1)
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
    plt.subplot(3, 2, 2)
    plt.plot(times, results['RH_air'])
    plt.grid(True)
    plt.xlabel('Time [hours]')
    plt.ylabel('Relative Humidity [%]')
    plt.title('Greenhouse Air Humidity')
    
    # Heat flux plot
    plt.subplot(3, 2, 3)
    plt.plot(times, results['q_tot'])
    plt.grid(True)
    plt.xlabel('Time [hours]')
    plt.ylabel('Heat Flux [W/m²]')
    plt.title('Total Heat Flux')
    
    # Energy plot
    plt.subplot(3, 2, 4)
    plt.plot(times, results['E_th_tot_kWhm2'], label='Thermal')
    plt.plot(times, results['E_el_tot_kWhm2'], label='Electrical')
    plt.grid(True)
    plt.xlabel('Time [hours]')
    plt.ylabel('Energy [kW·h/m²]')
    plt.title('Accumulated Energy')
    plt.legend()
    
    # CO2 concentration plot
    plt.subplot(3, 2, 5)
    plt.plot(times, results['CO2_air'])
    plt.grid(True)
    plt.xlabel('Time [hours]')
    plt.ylabel('CO2 [ppm]')
    plt.title('CO2 Concentration')
    
    # Control variables plot
    plt.subplot(3, 2, 6)
    plt.plot(times, results['SC'], label='Screen')
    plt.plot(times, results['vent_opening'], label='Ventilation')
    plt.grid(True)
    plt.xlabel('Time [hours]')
    plt.ylabel('Opening [-]')
    plt.title('Control Variables')
    plt.legend()
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    simulate_greenhouse() 