import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a

class Floor:
    """
    Python version of the Greenhouses.Components.Greenhouse.Floor model.
    Computes the floor temperature based on energy balance:
    - Sensible heat flow from surroundings
    - Absorbed short-wave solar radiation
    """

    def __init__(self, rho, c_p, A, V, steadystate=False, T_start=298.15):
        """
        Initialize the Floor model
        
        Parameters:
        -----------
        rho : float
            Density [kg/m³]
        c_p : float
            Specific heat capacity [J/(kg·K)]
        A : float
            Floor surface area [m²]
        V : float
            Volume [m³]
        steadystate : bool, optional
            If True, sets the derivative of T to zero during initialization
        T_start : float, optional
            Initial temperature [K]
        """
        self.rho = rho
        self.c_p = c_p
        self.A = A
        self.V = V
        self.steadystate = steadystate
        self.T = T_start
        
        # Heat port
        self.heatPort = HeatPort_a(T_start=T_start)
        
        # Radiation inputs
        self.R_Flr_Glob = [0.0, 0.0]  # [Sun radiation, Illumination radiation]
        self.P_Flr = 0.0  # Total short-wave power to the floor
        
        # Heat flow
        self.Q_flow = 0.0

    def set_inputs(self, Q_flow, R_Flr_Glob):
        """
        Set input values for the floor
        
        Parameters:
        -----------
        Q_flow : float
            Heat flow rate [W]
        R_Flr_Glob : list
            List of short-wave radiation inputs [W/m²]
        """
        self.Q_flow = Q_flow
        self.R_Flr_Glob = R_Flr_Glob
        self.heatPort.Q_flow = Q_flow  # Update heat port heat flow

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
