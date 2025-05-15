import numpy as np
from typing import Optional

class PipeFreeConvection:
    """
    Heating pipe heat exchange by free or hindered convection with air
    
    This model calculates heat exchange between heating pipes and air by free convection
    or hindered convection based on pipe characteristics and temperature difference.
    """
    
    def __init__(self, 
                 A: float,
                 d: float,
                 l: float,
                 freePipe: bool = True):
        """
        Initialize pipe free convection model
        
        Parameters:
            A (float): Floor surface area [m2]
            d (float): Characteristic dimension of the pipe (pipe diameter) [m]
            l (float): Length of heating pipes per m2 floor surface [m]
            freePipe (bool): True if pipe in free air, false if hindered pipe
        """
        # Parameters
        self.A = A
        self.d = d
        self.l = l
        self.freePipe = freePipe
        
        # State variables
        self.HEC_ab = 0.0  # Heat exchange coefficient [W/(m2.K)]
        self.alpha = 0.0  # Convection coefficient
        self.Q_flow = 0.0  # Heat flow rate [W]
        
    def update(self, 
              T_a: float,
              T_b: float) -> float:
        """
        Update pipe free convection model state
        
        Parameters:
            T_a (float): Temperature at port a [K]
            T_b (float): Temperature at port b [K]
            
        Returns:
            float: Heat flow rate [W]
        """
        # Calculate temperature difference
        dT = T_b - T_a
        
        # Calculate convection coefficient based on conditions
        if abs(dT) > 0:
            if self.freePipe:
                self.alpha = 1.28 * self.d**(-0.25) * max(1e-9, abs(dT))**0.25
            else:
                self.alpha = 1.99 * max(1e-9, abs(dT))**0.32
        else:
            self.alpha = 0.0
            
        # Calculate heat exchange coefficient
        self.HEC_ab = self.alpha * np.pi * self.d * self.l
        
        # Calculate heat flow
        self.Q_flow = self.A * self.HEC_ab * dT
        
        return self.Q_flow
