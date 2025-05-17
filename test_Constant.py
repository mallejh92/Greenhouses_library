from Flows.FluidFlow.HeatTransfer.SinglePhaseCorrelations.MuleyManglik1999 import MuleyManglik1999

if __name__ == "__main__":
    # Test code
    model = MuleyManglik1999(
        Re_lam=400.0,  # Fully laminar Reynolds number
        Re_tur=1000.0  # Fully turbulent Reynolds number
    )
    
    # Set up test conditions
    test_state = {
        'density': 1000.0,              # Water density [kg/m³]
        'thermal_conductivity': 0.6,    # Water thermal conductivity [W/(m·K)]
        'dynamic_viscosity': 0.001,     # Water dynamic viscosity [Pa·s]
        'prandtl_number': 7.0           # Water Prandtl number
    }
    
    # Update model state and parameters
    model.update_state(test_state)
    model.m_dot = 1.0  # Mass flow rate [kg/s]
    model.q_dot = 1000.0  # Heat flux [W/m²]
    
    # Calculate heat transfer coefficient
    model.calculate()
    print("Initial test with water:")
    print(model)
    
    # Test different flow conditions
    print("\nTesting different flow conditions:")
    
    # Test case 1: Laminar flow (Re < 400)
    model.m_dot = 0.1  # Lower mass flow rate for laminar flow
    model.calculate()
    print("\nLaminar flow (Re < 400):")
    print(model)
    
    # Test case 2: Transitional flow (400 < Re < 1000)
    model.m_dot = 0.5  # Medium mass flow rate for transitional flow
    model.calculate()
    print("\nTransitional flow (400 < Re < 1000):")
    print(model)
    
    # Test case 3: Turbulent flow (Re > 1000)
    model.m_dot = 2.0  # Higher mass flow rate for turbulent flow
    model.calculate()
    print("\nTurbulent flow (Re > 1000):")
    print(model)
    
    # Test case 4: Different fluid properties (ethylene glycol)
    test_state_eg = {
        'density': 1110.0,             # Ethylene glycol density [kg/m³]
        'thermal_conductivity': 0.25,  # Ethylene glycol thermal conductivity [W/(m·K)]
        'dynamic_viscosity': 0.016,    # Ethylene glycol dynamic viscosity [Pa·s]
        'prandtl_number': 150.0        # Ethylene glycol Prandtl number
    }
    model.update_state(test_state_eg)
    model.m_dot = 1.0
    model.calculate()
    print("\nEthylene glycol properties:")
    print(model)
    
    # Test case 5: Different plate geometry
    model = MuleyManglik1999(
        Re_lam=400.0,
        Re_tur=1000.0
    )
    model.update_state(test_state)  # Back to water properties
    model.m_dot = 1.0
    model.q_dot = 1000.0
    model.calculate()
    print("\nDifferent plate geometry:")
    print(model)