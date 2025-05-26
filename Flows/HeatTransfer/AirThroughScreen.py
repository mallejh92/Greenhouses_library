import numpy as np
from scipy import constants
from Interfaces.HeatAndVapour.Element1D import Element1D

class AirThroughScreen(Element1D):
    """
    Heat and mass flux exchange and air exchange rate through the screen
    
    This class implements the heat and mass transfer model for air flow through a screen
    in a greenhouse system.
    """
    
    def __init__(self, A: float, K: float, SC: float = 0.0, W: float = 9.6):
        """
        Initialize the AirThroughScreen model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        K : float
            Screen flow coefficient
        SC : float
            Screen closure (1:closed, 0:open), default is 0.0
        W : float
            Length of the screen when closed (SC=1) [m], default is 9.6
        """
        # Initialize parent class
        super().__init__()
        
        self.A = A
        self.K = K
        self.SC = SC
        self.W = W
        
        # Constants
        self.c_p_air = 1005  # Specific heat capacity of air [J/(kg·K)]
        self.g_n = constants.g  # Gravitational acceleration [m/s²]
        self.R = 8314  # Gas constant [J/(kmol·K)]
        self.M_H = 18  # Molar mass of water [kg/kmol]
        
        # State variables
        self.f_AirTop = 0.0  # Air exchange rate through screen [m/s]
        self.Q_flow = 0.0  # Heat flow rate [W]
        self.MV_flow = 0.0  # Mass flow rate [kg/s]
        self.MV_flow2 = 0.0  # Secondary mass flow rate [kg/s]
        self.VEC_AirTop = 0.0  # Mass transfer coefficient [kg/(s·Pa·m²)]
        
        # Port variables
        self.HeatPort_a_T = 293.15  # Temperature at port a [K]
        self.HeatPort_b_T = 293.15  # Temperature at port b [K]
        self.MassPort_a_VP = 0.0  # Vapor pressure at port a [Pa]
        self.MassPort_b_VP = 0.0  # Vapor pressure at port b [Pa]
        self.MassPort_a_P = 1e5  # Pressure at port a [Pa]
        self.MassPort_b_P = 1e5  # Pressure at port b [Pa]
        
    def step(self, dt: float):
        """
        Update the model state for one time step
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        # Update SC value from thScreen
        if hasattr(self, 'thScreen'):
            self.SC = self.thScreen.SC
            
        # Calculate temperature difference
        dT = self.HeatPort_b_T - self.HeatPort_a_T
        dP = self.MassPort_b_P - self.MassPort_a_P
        
        # Calculate air densities
        rho_air = self._calculate_air_density(self.HeatPort_a_T)
        rho_top = self._calculate_air_density(self.HeatPort_b_T)
        rho_mean = (rho_air + rho_top) / 2
        
        # Calculate air exchange rate
        self.f_AirTop = (self.SC * self.K * max(1e-9, abs(dT))**0.66 + 
                   (1 - self.SC) * (max(1e-9, 0.5 * rho_mean * self.W * 
                   (1 - self.SC) * self.g_n * max(1e-9, abs(rho_air - rho_top))))**0.5 / rho_mean)
        
        # Calculate heat exchange coefficient and heat flow
        HEC_ab = rho_air * self.c_p_air * self.f_AirTop
        self.Q_flow = self.A * HEC_ab * dT
        
        # Calculate mass exchange coefficient and mass flows
        self.VEC_AirTop = self.M_H * self.f_AirTop / (self.R * 287)
        self.MV_flow2 = self.A * self.M_H / self.R * self.f_AirTop * (
            self.MassPort_a_VP / self.HeatPort_a_T - 
            self.MassPort_b_VP / self.HeatPort_b_T
        )
        self.MV_flow = self.A * self.VEC_AirTop * dP
        
        # Update parent class variables
        super().update()
        
    def _calculate_air_density(self, T):
        """
        Calculate air density at given temperature
        
        Parameters:
        -----------
        T : float
            Temperature [K]
            
        Returns:
        --------
        rho : float
            Air density [kg/m³]
        """
        # Using ideal gas law: rho = P/(R*T)
        R = 287.058  # Specific gas constant for air [J/(kg·K)]
        P = 1e5  # Pressure [Pa]
        return P / (R * T)
