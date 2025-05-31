import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a

class Floor:
    """
    Python version of the Greenhouses.Components.Greenhouse.Floor model.
    Computes the floor temperature based on energy balance:
    - Sensible heat flow from surroundings
    - Absorbed short-wave solar radiation
    """

    def __init__(self, A, rho=1.0, c_p=2e6, V=0.01, T_start=298.15, steadystate=False, N_rad=2):
        """
        Initialize the Floor model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        rho : float, optional
            Density [kg/m³]
        c_p : float, optional
            Specific heat capacity [J/(kg·K)]
        V : float, optional
            Volume [m³]
        steadystate : bool, optional
            If True, sets the derivative of T to zero during initialization
        T_start : float, optional
            Initial temperature [K]
        N_rad : int, optional
            Number of short-wave radiation inputs (1 for sun only, 2 for sun + illumination)
        """
        # Parameters
        self.A = A
        self.rho = rho
        self.c_p = c_p
        self.V = V
        self.steadystate = steadystate
        self.N_rad = N_rad

        # State
        self.T = T_start
        self.Q_flow = 0.0
        
        # Heat port
        self.heatPort = HeatPort_a(T_start=T_start)
        
        # Radiation inputs
        self.R_Flr_Glob = [0.0] * N_rad  # Short-wave radiation inputs [W/m²]
        self.P_Flr = 0.0  # Total short-wave power to the floor

    def set_inputs(self, Q_flow=0.0, R_Flr_Glob=None):
        """
        Set input values for the floor
        
        Parameters:
        -----------
        Q_flow : float, optional
            Heat flow rate [W]
        R_Flr_Glob : list, optional
            List of short-wave radiation inputs [W/m²]
        """
        self.Q_flow = Q_flow
        self.heatPort.Q_flow = Q_flow
        
        if R_Flr_Glob is not None:
            if len(R_Flr_Glob) != self.N_rad:
                raise ValueError(f"R_Flr_Glob must have length {self.N_rad}")
            self.R_Flr_Glob = R_Flr_Glob

    def step(self, dt):
        """
        Update floor state
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        # Calculate total short-wave power
        self.P_Flr = sum(self.R_Flr_Glob) * self.A
        
        # Update temperature
        if not self.steadystate:
            dT = (self.Q_flow + self.P_Flr) / (self.rho * self.c_p * self.V)
            self.T += dT * dt
        
        # Update heat port
        self.heatPort.T = self.T
        return self.T

    def get_temperature(self):
        """Return the current temperature"""
        return self.T
