import numpy as np
import matplotlib.pyplot as plt
from Components.Greenhouse.Unit.Greenhouse import Greenhouse

def test_greenhouse():
    """
    Test the greenhouse model by simulating for 30 days with 1-minute time steps
    """
    # Initialize greenhouse
    greenhouse = Greenhouse()
    
    # Simulation parameters
    dt = 60  # Time step in seconds (1 minute)
    n_steps = 30 * 24 * 60  # Number of steps for 30 days
    
    # Arrays to store results
    time = np.zeros(n_steps)
    air_temp = np.zeros(n_steps)
    co2_level = np.zeros(n_steps)
    heat_flux = np.zeros(n_steps)
    energy_consumption = np.zeros(n_steps)
    outside_temp = np.zeros(n_steps)
    setpoint_temp = np.zeros(n_steps)
    global_radiation = np.zeros(n_steps)
    crop_dm = np.zeros(n_steps)
    
    # Simulation loop
    for i in range(n_steps):
        # Update time
        time[i] = i * dt / 3600  # Convert to hours
        
        # Store current weather data
        current_weather = greenhouse.weather_df.iloc[i % len(greenhouse.weather_df)]
        current_sp = greenhouse.sp_df.iloc[i % len(greenhouse.sp_df)]
        outside_temp[i] = current_weather["T_out"] - 273.15  # Convert from Kelvin to Celsius
        setpoint_temp[i] = current_sp["T_sp"] - 273.15  # Convert from Kelvin to Celsius
        global_radiation[i] = current_weather["I_glob"]
        
        # Step the greenhouse model
        greenhouse.step(dt)
        
        # Store results
        air_temp[i] = greenhouse.air.T - 273.15  # Convert from Kelvin to Celsius
        co2_level[i] = greenhouse.CO2_air.CO2_ppm
        heat_flux[i] = greenhouse.q_tot
        energy_consumption[i] = greenhouse.E_th_tot_kWhm2
        crop_dm[i] = greenhouse.DM_Har
    
    # Plot results
    plt.figure(figsize=(15, 15))
    
    # Air temperature plot
    plt.subplot(3, 2, 1)
    plt.plot(time, air_temp, label='Greenhouse Air')
    plt.plot(time, outside_temp, label='Outside Air')
    plt.plot(time, setpoint_temp, label='Setpoint', linestyle='--')
    plt.xlabel('Time (hours)')
    plt.ylabel('Temperature (°C)')
    plt.title('Temperature Comparison')
    plt.legend()
    plt.grid(True)
    
    # CO2 level plot
    plt.subplot(3, 2, 2)
    plt.plot(time, co2_level)
    plt.xlabel('Time (hours)')
    plt.ylabel('CO2 Level (ppm)')
    plt.title('Greenhouse CO2 Level')
    plt.grid(True)
    
    # Heat flux plot
    plt.subplot(3, 2, 3)
    plt.plot(time, heat_flux)
    plt.xlabel('Time (hours)')
    plt.ylabel('Heat Flux (W/m²)')
    plt.title('Total Heat Flux')
    plt.grid(True)
    
    # Energy consumption plot
    plt.subplot(3, 2, 4)
    plt.plot(time, energy_consumption)
    plt.xlabel('Time (hours)')
    plt.ylabel('Energy Consumption (kWh/m²)')
    plt.title('Cumulative Energy Consumption')
    plt.grid(True)
    
    # Global radiation plot
    plt.subplot(3, 2, 5)
    plt.plot(time, global_radiation)
    plt.xlabel('Time (hours)')
    plt.ylabel('Global Radiation (W/m²)')
    plt.title('Global Solar Radiation')
    plt.grid(True)
    
    # Crop dry matter plot
    plt.subplot(3, 2, 6)
    plt.plot(time, crop_dm)
    plt.xlabel('Time (hours)')
    plt.ylabel('Dry Matter (mg/m²)')
    plt.title('Crop Dry Matter Accumulation')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    # Print final results
    print("\n시뮬레이션 결과:")
    print(f"최종 온실 내부 온도: {air_temp[-1]:.2f}°C")
    print(f"최종 외부 온도: {outside_temp[-1]:.2f}°C")
    print(f"최종 CO2 농도: {co2_level[-1]:.2f} ppm")
    print(f"총 에너지 소비량: {energy_consumption[-1]:.2f} kWh/m²")
    print(f"총 수확 건물중: {crop_dm[-1]:.2f} mg/m²")
    
    # Print daily averages
    days = int(n_steps / (24 * 60))
    print("\n일별 평균값:")
    for day in range(days):
        start_idx = day * 24 * 60
        end_idx = (day + 1) * 24 * 60
        print(f"\nDay {day + 1}:")
        print(f"평균 온실 온도: {np.mean(air_temp[start_idx:end_idx]):.2f}°C")
        print(f"평균 CO2 농도: {np.mean(co2_level[start_idx:end_idx]):.2f} ppm")
        print(f"일일 에너지 소비량: {energy_consumption[end_idx-1] - energy_consumption[start_idx]:.2f} kWh/m²")
        print(f"일일 건물중 증가량: {crop_dm[end_idx-1] - crop_dm[start_idx]:.2f} mg/m²")

if __name__ == "__main__":
    test_greenhouse() 