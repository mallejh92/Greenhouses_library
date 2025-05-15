import numpy as np
from typing import Optional

class AirThroughScreen:
    """
    Heat exchange and air exchange rate through the screen
    
    This model calculates the heat exchange and air exchange rate through a screen
    based on screen closure, temperature difference, and air properties.
    """
    
    def __init__(self, A: float, W: float, K: float):
        """
        Initialize screen model
        
        Parameters:
            A (float): Floor surface area [m2]
            W (float): Length of the screen when closed (SC=1) [m]
            K (float): Screen flow coefficient
        """
        # Parameters
        self.A = A
        self.W = W
        self.K = K
        
        # Constants
        self.c_p_air = 1005.0  # Specific heat capacity of air [J/(kg.K)]
        self.g_n = 9.81  # Gravitational acceleration [m/s2]
        
        # State variables
        self.SC = 0.0  # Screen closure (1: closed, 0: open)
        self.HEC_ab = 0.0  # Heat exchange coefficient [W/(m2.K)]
        self.rho_air = 0.0  # Air density [kg/m3]
        self.rho_mean = 0.0  # Mean air density [kg/m3]
        self.rho_top = 0.0  # Top air density [kg/m3]
        self.f_AirTop = 0.0  # Air exchange rate [m3/(m2.s)]
        self.Q_flow = 0.0  # Heat flow rate [W]
        
    def density_pT(self, p: float, T: float) -> float:
        """
        Calculate air density from pressure and temperature
        
        Parameters:
            p (float): Pressure [Pa]
            T (float): Temperature [K]
            
        Returns:
            float: Air density [kg/m3]
        """
        # Simplified air properties
        R = 287.0  # Gas constant for air [J/(kg.K)]
        return p / (R * T)
        
    def update(self, 
              SC: float,
              T_a: float,
              T_b: float) -> tuple:
        """
        Update screen model state
        
        Parameters:
            SC (float): Screen closure (1: closed, 0: open)
            T_a (float): Temperature at port a [K]
            T_b (float): Temperature at port b [K]
            
        Returns:
            tuple: (Q_flow, f_AirTop) Heat flow rate and air exchange rate
        """
        # Update screen closure
        self.SC = SC
        
        # Calculate temperature difference
        dT = T_b - T_a
        
        # Calculate air densities
        self.rho_air = self.density_pT(1e5, T_a)
        self.rho_top = self.density_pT(1e5, T_b)
        self.rho_mean = (self.rho_air + self.rho_top) / 2
        
        # Calculate air exchange rate
        self.f_AirTop = (self.SC * self.K * max(1e-9, abs(dT))**0.66 + 
                        (1 - self.SC) * (max(1e-9, 0.5 * self.rho_mean * self.W * 
                        (1 - self.SC) * self.g_n * max(1e-9, abs(self.rho_air - self.rho_top))))**0.5 / 
                        self.rho_mean)
        
        # Calculate heat exchange coefficient and heat flow
        self.HEC_ab = self.rho_air * self.c_p_air * self.f_AirTop
        self.Q_flow = self.A * self.HEC_ab * dT
        
        return self.Q_flow, self.f_AirTop
