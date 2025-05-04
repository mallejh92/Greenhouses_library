import numpy as np

class TopAirCompartment:
    """
    Python version of the Greenhouses.Components.Greenhouse.Air_Top model.
    Simplified air model for the top air zone above the thermal screen.
    No shortwave radiation included due to low heat capacity.
    """

    def __init__(self, A, h_Top, c_p=1000.0, T_start=298.0,
                 steadystate=False, steadystateVP=True):
        # Parameters
        self.A = A                  # Greenhouse floor area [m²]
        self.h_Top = h_Top          # Height of top air zone [m]
        self.c_p = c_p              # Specific heat capacity [J/kg/K]
        self.P_atm = 101325.0       # Atmospheric pressure [Pa]
        self.R_a = 287.0            # Gas constant for dry air
        self.R_s = 461.5            # Gas constant for water vapor

        # Initialization options
        self.steadystate = steadystate
        self.steadystateVP = steadystateVP

        # State
        self.T = T_start            # Temperature [K]
        self.Q_flow = 0.0           # Sensible heat flow [W]
        self.massPort_VP = 0.0      # Vapor pressure [Pa]

        # Derived properties
        self.V = self.A * self.h_Top    # Volume [m³]
        self.rho = self._compute_density(self.T)  # Air density [kg/m³]

        self.w_air = 0.0            # Humidity ratio
        self.RH = 0.0               # Relative humidity

    def _compute_density(self, T):
        # Placeholder: assume constant pressure, ideal gas law for dry air
        return self.P_atm / (self.R_a * T)

    def compute_derivatives(self):
        if self.steadystate:
            return 0.0
        self.rho = self._compute_density(self.T)
        return self.Q_flow / (self.rho * self.c_p * self.V)

    def update_humidity(self):
        if self.steadystateVP:
            return
        VP = self.massPort_VP
        self.w_air = VP * self.R_a / ((self.P_atm - VP) * self.R_s)
        # Tetens formula for saturation vapor pressure
        T_C = self.T - 273.15
        Psat = 610.78 * np.exp(T_C / (T_C + 238.3) * 17.2694)
        self.RH = VP / Psat
        self.RH = np.clip(self.RH, 0, 1)

    def step(self, dt):
        dTdt = self.compute_derivatives()
        self.T += dTdt * dt
        self.update_humidity()
        return self.T, self.RH

    def set_inputs(self, Q_flow, massPort_VP):
        self.Q_flow = Q_flow
        self.massPort_VP = massPort_VP
