import numpy as np
import matplotlib.pyplot as plt
from Components.CropYield.TomatoYieldModel import TomatoYieldModel

def plot_simulation_results(simulation_data, duration_days):
    """Plot simulation results over time"""
    # Create time array in days
    time = np.linspace(0, duration_days, len(simulation_data))
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    fig.suptitle('Tomato Growth Simulation Results', fontsize=16)
    
    # Plot LAI and DM_Har on first subplot
    ax1.plot(time, simulation_data[:, 1] * 2.67e-5, 'g-', label='LAI')  # Convert C_Leaf to LAI
    # ax1.plot(time, simulation_data[:, -1], 'r-', label='DM_Har')
    ax1.set_xlabel('Time (days)')
    ax1.set_ylabel('Value')
    ax1.set_title('LAI and Harvested Dry Matter')
    ax1.grid(True)
    ax1.legend()
    
    # Plot C_Leaf and C_Stem on second subplot
    ax2.plot(time, simulation_data[:, 1], 'b-', label='C_Leaf')
    ax2.plot(time, simulation_data[:, 2], 'c-', label='C_Stem')
    ax2.set_xlabel('Time (days)')
    ax2.set_ylabel('Carbon Content (mg/m²)')
    ax2.set_title('Leaf and Stem Carbon Content')
    ax2.grid(True)
    ax2.legend()
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig('tomato_growth_simulation.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    model = TomatoYieldModel()
    
    print("Data file not found, using default simulation")
    results = model.simulate(duration_days=300)
    
    if results:
        print('Simulation results:')
        for key, value in results.items():
            if key != 'simulation_data':
                print(f'  {key}: {value}')
        
        # Plot the results
        plot_simulation_results(results['simulation_data'], 300)
        print("\nPlot has been saved as 'tomato_growth_simulation.png'")
    else:
        print("Simulation failed")