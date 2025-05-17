from Flows.FluidFlow.HeatTransfer.Smoothed import Smoothed

if __name__ == "__main__":
    # Initialize Smoothed model
    model = Smoothed(
        n=3,                    # Number of nodes
        Mdotnom=1.0,           # Nominal mass flow rate [kg/s]
        Unom_l=1000.0,         # Nominal HTC for liquid [W/(m²·K)]
        Unom_tp=2000.0,        # Nominal HTC for two-phase [W/(m²·K)]
        Unom_v=500.0,          # Nominal HTC for vapor [W/(m²·K)]
        M_dot=1.0,             # Mass flow rate [kg/s]
        x=0.0                  # Vapor quality
    )
    
    # Set up fluid state
    model.FluidState[0] = {
        'density': 1000.0,              # Density [kg/m³]
        'thermal_conductivity': 0.6,    # Thermal conductivity [W/(m·K)]
        'dynamic_viscosity': 0.001,     # Dynamic viscosity [Pa·s]
        'specific_heat_capacity': 4186.0 # Specific heat capacity [J/(kg·K)]
    }
    
    # Set up thermal ports and fluid temperatures
    for i in range(model.n):
        model.thermalPortL[i].T = 298.15  # 25°C
        model.T_fluid[i] = 293.15         # 20°C
    
    # Test case 1: Nominal conditions (liquid phase)
    model.x = 0.0  # Liquid phase
    model.calculate()
    print("Test case 1: Nominal conditions (liquid phase)")
    print(model)
    
    # Test case 2: Two-phase flow
    model.x = 0.5  # Two-phase
    model.calculate()
    print("\nTest case 2: Two-phase flow")
    print(model)
    
    # Test case 3: Vapor phase
    model.x = 1.0  # Vapor phase
    model.calculate()
    print("\nTest case 3: Vapor phase")
    print(model)
    
    # Test case 4: Different mass flow rate
    model.M_dot = 2.0  # Higher mass flow rate
    model.calculate()
    print("\nTest case 4: Higher mass flow rate")
    print(model)
    
    # Test case 5: Different fluid properties (ethylene glycol)
    model.FluidState[0] = {
        'density': 1110.0,              # Density [kg/m³]
        'thermal_conductivity': 0.25,    # Thermal conductivity [W/(m·K)]
        'dynamic_viscosity': 0.016,      # Dynamic viscosity [Pa·s]
        'specific_heat_capacity': 2382.0  # Specific heat capacity [J/(kg·K)]
    }
    
    model.calculate()
    print("\nTest case 5: Different fluid properties (ethylene glycol)")
    print(model)
    
    # Test case 6: Different temperature difference
    for i in range(model.n):
        model.thermalPortL[i].T = 373.15  # 100°C
        model.T_fluid[i] = 273.15         # 0°C
    
    model.calculate()
    print("\nTest case 6: High temperature difference (0°C to 100°C)")
    print(model)