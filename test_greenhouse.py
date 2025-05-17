import numpy as np
import matplotlib.pyplot as plt
from Components.Greenhouse.Unit.Greenhouse import Greenhouse

def test_greenhouse():
    """
    Test the greenhouse model by simulating for 24 hours with 1-minute time steps
    """
    # Initialize greenhouse
    greenhouse = Greenhouse()
    
    # Simulation parameters
    dt = 60  # Time step in seconds (1 minute)
    n_steps = 24 * 60  # Number of steps for 24 hours
    
    # Arrays to store results
    time = np.zeros(n_steps)
    air_temp = np.zeros(n_steps)
    co2_level = np.zeros(n_steps)
    heat_flux = np.zeros(n_steps)
    energy_consumption = np.zeros(n_steps)
    
    # Simulation loop
    for i in range(n_steps):
        # Update time
        time[i] = i * dt / 3600  # Convert to hours
        
        # Step the greenhouse model
        greenhouse.step(dt)
        
        # Store results
        air_temp[i] = greenhouse.air.T - 273.15  # Convert to Celsius
        co2_level[i] = greenhouse.air.CO2_ppm
        heat_flux[i] = greenhouse.q_tot
        energy_consumption[i] = greenhouse.E_th_tot_kWhm2
    
    # Plot results
    plt.figure(figsize=(15, 10))
    
    # Air temperature plot
    plt.subplot(2, 2, 1)
    plt.plot(time, air_temp)
    plt.xlabel('Time (hours)')
    plt.ylabel('Air Temperature (°C)')
    plt.title('Greenhouse Air Temperature')
    plt.grid(True)
    
    # CO2 level plot
    plt.subplot(2, 2, 2)
    plt.plot(time, co2_level)
    plt.xlabel('Time (hours)')
    plt.ylabel('CO2 Level (ppm)')
    plt.title('Greenhouse CO2 Level')
    plt.grid(True)
    
    # Heat flux plot
    plt.subplot(2, 2, 3)
    plt.plot(time, heat_flux)
    plt.xlabel('Time (hours)')
    plt.ylabel('Heat Flux (W/m²)')
    plt.title('Total Heat Flux')
    plt.grid(True)
    
    # Energy consumption plot
    plt.subplot(2, 2, 4)
    plt.plot(time, energy_consumption)
    plt.xlabel('Time (hours)')
    plt.ylabel('Energy Consumption (kWh/m²)')
    plt.title('Cumulative Energy Consumption')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    # Print final results
    print("\nSimulation Results:")
    print(f"Final Air Temperature: {air_temp[-1]:.2f}°C")
    print(f"Final CO2 Level: {co2_level[-1]:.2f} ppm")
    print(f"Total Energy Consumption: {energy_consumption[-1]:.2f} kWh/m²")
    print(f"Total Dry Matter Harvest: {greenhouse.DM_Har:.2f} mg/m²")

if __name__ == "__main__":
    test_greenhouse() 