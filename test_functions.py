from Functions.DerivativeSaturatedVapourPressure import DerivativeSaturatedVapourPressure
from Functions.MultiLayer_TauRho import MultiLayer_TauRho
from Functions.SaturatedVapourPressure import SaturatedVapourPressure
from Functions.WaterVapourPressure import WaterVapourPressure

def test_derivative_saturated_vapour_pressure():
    calculator = DerivativeSaturatedVapourPressure()
    TSat = 20.0  # 20°C
    result = calculator.calculate(TSat)
    print(f"DerivativeSaturatedVapourPressure at {TSat}°C: {result:.2f} Pa/K")

def test_multi_layer_tau_rho():
    calculator = MultiLayer_TauRho()
    # 예시 값 설정
    tau_1, tau_2 = 0.8, 0.7
    rho_1, rho_2 = 0.2, 0.3
    tau_12, rho_12 = calculator.calculate(tau_1, tau_2, rho_1, rho_2)
    print(f"MultiLayer_TauRho results:")
    print(f"tau_12: {tau_12:.4f}")
    print(f"rho_12: {rho_12:.4f}")

def test_saturated_vapour_pressure():
    calculator = SaturatedVapourPressure()
    TSat = 20.0  # 20°C
    result = calculator.calculate(TSat)
    print(f"SaturatedVapourPressure at {TSat}°C: {result:.2f} Pa")

def test_water_vapour_pressure():
    calculator = WaterVapourPressure()
    TSat = 20.0  # 20°C
    RH = 70.0    # 70%
    result = calculator.calculate(TSat, RH)
    print(f"WaterVapourPressure at {TSat}°C and {RH}% RH: {result:.2f} Pa")

if __name__ == "__main__":
    print("Testing all converted functions...\n")
    
    print("1. Testing DerivativeSaturatedVapourPressure:")
    test_derivative_saturated_vapour_pressure()
    print()
    
    print("2. Testing MultiLayer_TauRho:")
    test_multi_layer_tau_rho()
    print()
    
    print("3. Testing SaturatedVapourPressure:")
    test_saturated_vapour_pressure()
    print()
    
    print("4. Testing WaterVapourPressure:")
    test_water_vapour_pressure() 