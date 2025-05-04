import numpy as np

class Floor:
    """
    Python version of the Greenhouses.Components.Greenhouse.Floor model.
    Computes the floor temperature based on energy balance:
    - Sensible heat flow from surroundings
    - Absorbed short-wave solar radiation
    """

    def __init__(self, A, rho, c_p, V, N_rad=2, T_start=298.0, steadystate=False):
        # Parameters
        self.A = A                  # Greenhouse floor area [m²]
        self.rho = rho              # Floor material density [kg/m³]
        self.c_p = c_p              # Specific heat capacity [J/kg/K]
        self.V = V                  # Volume of floor material [m³]
        self.N_rad = N_rad          # Number of radiation sources

        # State
        self.T = T_start            # Temperature [K]
        self.steadystate = steadystate

        # Inputs
        self.Q_flow = 0.0           # Sensible heat flow [W]
        self.R_Flr_Glob = np.zeros(N_rad)  # Shortwave radiation vector [W/m²]

        # Outputs
        self.P_Flr = 0.0            # Total absorbed shortwave radiation [W]

    def compute_radiation_input(self):
        self.P_Flr = np.sum(self.R_Flr_Glob) * self.A

    def compute_derivatives(self):
        if self.steadystate:
            return 0.0
        self.compute_radiation_input()
        return (self.Q_flow + self.P_Flr) / (self.rho * self.c_p * self.V)

    def step(self, dt):
        dTdt = self.compute_derivatives()
        self.T += dTdt * dt
        return self.T

    def set_inputs(self, Q_flow, R_Flr_Glob):
        self.Q_flow = Q_flow
        self.R_Flr_Glob = np.array(R_Flr_Glob)
