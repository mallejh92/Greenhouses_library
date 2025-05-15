import numpy as np
from scipy import constants

class AirThroughScreen:
    """
    Heat exchange and air exchange rate through the screen
    
    This class implements the heat transfer model for air flow through a screen
    in a greenhouse system.
    """
    
    def __init__(self, A, W, K):
        """
        Initialize the AirThroughScreen model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        W : float
            Length of the screen when closed (SC=1) [m]
        K : float
            Screen flow coefficient
        """
        self.A = A
        self.W = W
        self.K = K
        
        # Constants
        self.c_p_air = 1005  # Specific heat capacity of air [J/(kg·K)]
        self.g_n = constants.g  # Gravitational acceleration [m/s²]
        
        # State variables
        self.SC = 0  # Screen closure (1:closed, 0:open)
        
    def calculate_heat_transfer(self, T_a, T_b):
        """
        Calculate heat transfer through the screen
        
        Parameters:
        -----------
        T_a : float
            Temperature at port a [K]
        T_b : float
            Temperature at port b [K]
            
        Returns:
        --------
        Q_flow : float
            Heat flow rate [W]
        """
        # Calculate air densities
        rho_air = self._calculate_air_density(T_a)
        rho_top = self._calculate_air_density(T_b)
        rho_mean = (rho_air + rho_top) / 2
        
        # Calculate temperature difference
        dT = T_b - T_a
        
        # Calculate air exchange rate
        f_AirTop = (self.SC * self.K * max(1e-9, abs(dT))**0.66 + 
                   (1 - self.SC) * (max(1e-9, 0.5 * rho_mean * self.W * 
                   (1 - self.SC) * self.g_n * max(1e-9, abs(rho_air - rho_top))))**0.5 / rho_mean)
        
        # Calculate heat exchange coefficient
        HEC_ab = rho_air * self.c_p_air * f_AirTop
        
        # Calculate heat flow
        Q_flow = self.A * HEC_ab * dT
        
        return Q_flow
    
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
        # Simplified air density calculation at 1e5 Pa
        # Using ideal gas law: rho = P/(R*T)
        R = 287.058  # Specific gas constant for air [J/(kg·K)]
        P = 1e5  # Pressure [Pa]
        return P / (R * T)
