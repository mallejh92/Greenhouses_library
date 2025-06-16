import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from Components.CropYield.TomatoYieldModel import TomatoYieldModel
from Components.Greenhouse.Solar_model import Solar_model
from Components.Greenhouse.Illumination import Illumination

def plot_simulation_results(simulation_data, measured_data, duration_days):
    """Plot simulation results over time with measured data"""
    # Create time array in days
    time = np.linspace(0, duration_days, len(simulation_data))
    
    # Create figure with subplots
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 20))
    fig.suptitle('Tomato Growth Simulation Results vs Measured Data', fontsize=16)
    
    # Plot LAI
    ax1.plot(time, simulation_data[:, 1] * 2.67e-5, 'g-', label='Simulated LAI')
    ax1.set_xlabel('Time (days)')
    ax1.set_ylabel('LAI')
    ax1.set_title('Leaf Area Index')
    ax1.grid(True)
    ax1.legend()
    
    # Plot C_Leaf and C_Stem
    ax2.plot(time, simulation_data[:, 1], 'b-', label='Simulated C_Leaf')
    ax2.plot(time, simulation_data[:, 2], 'c-', label='Simulated C_Stem')
    ax2.set_xlabel('Time (days)')
    ax2.set_ylabel('Carbon Content (mg/m²)')
    ax2.set_title('Leaf and Stem Carbon Content')
    ax2.grid(True)
    ax2.legend()
    
    # Plot DM_Har
    ax3.plot(time, simulation_data[:, -1], 'r-', label='Simulated DM_Har')
    ax3.set_xlabel('Time (days)')
    ax3.set_ylabel('Dry Matter (mg/m²)')
    ax3.set_title('Harvested Dry Matter')
    ax3.grid(True)
    ax3.legend()
    
    # Plot environmental conditions
    ax4.plot(measured_data['time']/86400, measured_data['T_air_sp'], 'r-', label='Air Temperature Setpoint')
    ax4.plot(measured_data['time']/86400, measured_data['CO2_air_sp'], 'g-', label='CO2 Setpoint')
    ax4.plot(measured_data['time']/86400, measured_data['I_glob'], 'b-', label='Global Radiation')
    ax4.set_xlabel('Time (days)')
    ax4.set_ylabel('Value')
    ax4.set_title('Environmental Conditions')
    ax4.grid(True)
    ax4.legend()
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig('tomato_growth_simulation_with_measured.png', dpi=300, bbox_inches='tight')
    plt.close()

def run_simulation_with_measured_data(data_file, duration_days=300):
    """Run simulation with measured environmental data"""
    try:
        # Read measured data with correct column names
        measured_data = pd.read_csv(data_file, 
                                  delimiter="\t", 
                                  skiprows=2,
                                  names=['time', 'T_out', 'RH_out', 'P_out', 'I_glob', 
                                        'u_wind', 'T_sky', 'T_air_sp', 'CO2_air_sp', 'ilu_sp'])
        
        # Initialize models
        model = TomatoYieldModel(C_Leaf_0=40e3, C_Stem_0=30e3)
        solar_model = Solar_model(A=1.4e4, I_glob=0.0, LAI=model.LAI)
        illumination = Illumination(A=1.4e4, LAI=model.LAI)
        
        # Simulation time step (1 hour)
        dt = 3600  # seconds
        
        # Store results
        results = []
        
        # Run simulation
        for t in range(0, duration_days * 86400, dt):
            # Get environmental conditions from measured data
            current_data = measured_data.iloc[t//3600 % len(measured_data)]
            
            # Update environmental conditions
            T_canK = current_data['T_air_sp'] + 273.15  # Convert to Kelvin
            CO2_air = current_data['CO2_air_sp']
            
            # Update solar radiation
            solar_model.I_glob = current_data['I_glob']
            solar_model.LAI = model.LAI
            solar_results = solar_model.compute()
            
            # Update artificial lighting
            illumination.LAI = model.LAI
            illumination.switch = current_data['ilu_sp']
            illumination_results = illumination.step(dt)
            
            # Total PAR at canopy
            R_PAR_can = solar_results['R_PAR_Can_umol'] + illumination_results['R_PAR_Can_umol']
            
            # Update model
            model.set_environmental_conditions(R_PAR_can=R_PAR_can, CO2_air=CO2_air, T_canK=T_canK)
            model.step(dt)
            
            # Store results
            results.append([
                model.C_Buf,
                model.C_Leaf,
                model.C_Stem,
                *model.C_Fruit,
                *model.N_Fruit,
                model.T_can24C,
                model.T_canSumC,
                model.W_Fruit_1_Pot,
                model.DM_Har
            ])
        
        results_array = np.array(results)
        
        # Plot results
        plot_simulation_results(results_array, measured_data, duration_days)
        
        return {
            'C_Buf': float(model.C_Buf),
            'C_Leaf': float(model.C_Leaf),
            'C_Stem': float(model.C_Stem),
            'LAI': float(model.LAI),
            'Fruit_C_total': float(np.sum(model.C_Fruit)),
            'Fruit_N_total': float(np.sum(model.N_Fruit)),
            'T_can24C': float(model.T_can24C),
            'T_canSumC': float(model.T_canSumC),
            'W_Fruit_1_Pot': float(model.W_Fruit_1_Pot),
            'DM_Har': float(model.DM_Har),
            'simulation_data': results_array
        }
        
    except Exception as e:
        print(f"Simulation failed: {e}")
        return None

def run_simulation_with_sine_env(duration_days=300):
    """사인함수 기반 임의 환경으로 시뮬레이션"""
    model = TomatoYieldModel(C_Leaf_0=40e3, C_Stem_0=30e3)
    A=1.4e4
    solar_model = Solar_model(A=A, I_glob=0.0, LAI=model.LAI)
    illumination = Illumination(A=A, LAI=model.LAI)
    dt = 3600  # 1시간
    results = []
    times = np.arange(0, duration_days * 86400, dt)
    measured_data = {'time': [], 'T_air_sp': [], 'CO2_air_sp': [], 'I_glob': []}
    for t in times:
        # 하루(24시간) 주기
        day_frac = (t % 86400) / 86400
        # 광도: 해가 뜨고 지는 효과 (0~1000)
        I_glob = max(0, 1000 * np.sin(np.pi * day_frac))
        # CO2: 430 ppm 고정
        CO2_air = 430
        # 온도: 해가 뜨면 26도, 해가 지면 18도 (사인함수로 변동)
        T_air = 22 + 4 * np.sin(np.pi * day_frac)  # 18~26도
        # 기록용 measured_data
        measured_data['time'].append(t)
        measured_data['T_air_sp'].append(T_air)
        measured_data['CO2_air_sp'].append(CO2_air)
        measured_data['I_glob'].append(I_glob)
        # Solar/조명
        solar_model.I_glob = I_glob
        solar_model.LAI = model.LAI
        solar_results = solar_model.compute()
        illumination.LAI = model.LAI
        illumination.switch = 0  # 임의 환경에서는 인공조명 off
        illumination_results = illumination.step(dt)
        R_PAR_can = solar_results['R_PAR_Can_umol'] + illumination_results['R_PAR_Can_umol']
        # 모델 업데이트
        model.set_environmental_conditions(R_PAR_can=R_PAR_can, CO2_air=CO2_air, T_canK=T_air+273.15)
        model.step(dt)
        results.append([
            model.C_Buf,
            model.C_Leaf,
            model.C_Stem,
            *model.C_Fruit,
            *model.N_Fruit,
            model.T_can24C,
            model.T_canSumC,
            model.W_Fruit_1_Pot,
            model.DM_Har
        ])
    results_array = np.array(results)
    measured_df = pd.DataFrame(measured_data)
    plot_simulation_results(results_array, measured_df, duration_days)
    return {
        'C_Buf': float(model.C_Buf),
        'C_Leaf': float(model.C_Leaf),
        'C_Stem': float(model.C_Stem),
        'LAI': float(model.LAI),
        'Fruit_C_total': float(np.sum(model.C_Fruit)),
        'Fruit_N_total': float(np.sum(model.N_Fruit)),
        'T_can24C': float(model.T_can24C),
        'T_canSumC': float(model.T_canSumC),
        'W_Fruit_1_Pot': float(model.W_Fruit_1_Pot),
        'DM_Har': float(model.DM_Har),
        'simulation_data': results_array
    }

if __name__ == '__main__':
    print('시뮬레이션 모드를 선택하세요:')
    print('1: 실측 데이터 기반')
    print('2: 임의 환경(사인함수 기반)')
    mode = input('번호를 입력하세요 (1/2): ').strip()
    duration_days = 300
    if mode == '1':
        data_file = '10Dec-22Nov.txt'
        try:
            results = run_simulation_with_measured_data(data_file, duration_days)
            if results:
                print('Simulation results:')
                for key, value in results.items():
                    if key != 'simulation_data':
                        print(f'  {key}: {value}')
                print("\nPlot has been saved as 'tomato_growth_simulation_with_measured.png'")
            else:
                print("Simulation failed")
        except FileNotFoundError:
            print(f"Data file '{data_file}' not found")
            print("Using default simulation instead")
            model = TomatoYieldModel()
            results = model.simulate(duration_days=duration_days)
            if results:
                print('Default simulation results:')
                for key, value in results.items():
                    if key != 'simulation_data':
                        print(f'  {key}: {value}')
                plot_simulation_results(results['simulation_data'], pd.DataFrame(), duration_days)
                print("\nPlot has been saved as 'tomato_growth_simulation.png'")
            else:
                print("Default simulation failed")
    elif mode == '2':
        results = run_simulation_with_sine_env(duration_days)
        if results:
            print('Sine 환경 시뮬레이션 결과:')
            for key, value in results.items():
                if key != 'simulation_data':
                    print(f'  {key}: {value}')
            print("\nPlot has been saved as 'tomato_growth_simulation_with_measured.png'")
        else:
            print('Simulation failed')
    else:
        print('잘못된 입력입니다. 1 또는 2를 입력하세요.')
