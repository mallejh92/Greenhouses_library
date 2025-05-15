import numpy as np
from typing import Optional

class OutsideAirConvection:
    """
    Cover heat exchange by convection with outside air function of wind speed
    
    This model calculates heat exchange by convection between the cover and outside air
    based on wind speed and surface inclination.
    """
    
    def __init__(self, A: float, phi: float = 25/180*np.pi):
        """
        Initialize outside air convection model
        
        Parameters:
            A (float): Floor surface area [m2]
            phi (float): Inclination of the surface [rad] (0 if horizontal, 25 for typical cover)
        """
        # Parameters
        self.A = A
        self.phi = phi
        
        # Constants
        self.s = 11.0  # Slope of the differentiable switch function
        
        # State variables
        self.u = 0.0  # Wind speed [m/s]
        self.HEC_ab = 0.0  # Heat exchange coefficient [W/(m2.K)]
        self.alpha = 0.0  # Convection coefficient
        self.alpha_a = 0.0  # Convection coefficient for u < 4
        self.alpha_b = 0.0  # Convection coefficient for u > 4
        self.Q_flow = 0.0  # Heat flow rate [W]
        
    def update(self, 
              u: float,
              T_a: float,
              T_b: float) -> float:
        """
        Update outside air convection model state
        
        Parameters:
            u (float): Wind speed [m/s]
            T_a (float): Temperature at port a [K]
            T_b (float): Temperature at port b [K]
            
        Returns:
            float: Heat flow rate [W]
        """
        # Update wind speed
        self.u = u
        
        # Calculate temperature difference
        dT = T_b - T_a
        
        # Calculate convection coefficient using differentiable switch function
        du = 4 - u
        self.alpha_a = 1/(1 + np.exp(-self.s * du)) * (2.8 + 1.2 * u)  # Used for du > 0, i.e. u < 4
        self.alpha_b = 1/(1 + np.exp(self.s * du)) * 2.5 * u**0.8  # Used for du < 0, i.e. u > 4
        self.alpha = self.alpha_a + self.alpha_b
        
        # Calculate heat exchange coefficient
        self.HEC_ab = self.alpha / np.cos(self.phi)
        
        # Calculate heat flow
        self.Q_flow = self.A * self.HEC_ab * dT
        
        return self.Q_flow
