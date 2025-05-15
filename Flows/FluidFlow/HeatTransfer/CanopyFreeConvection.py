import numpy as np
from typing import Optional

class CanopyFreeConvection:
    """
    Leaves heat exchange by free convection with air
    
    This model calculates the heat exchange between leaves and air by free convection
    based on the leaf area index and heat transfer coefficient.
    """
    
    def __init__(self, A: float, U: float = 5.0):
        """
        Initialize canopy free convection model
        
        Parameters:
            A (float): Floor surface area [m2]
            U (float): Leaves heat transfer coefficient [W/(m2.K)]
        """
        # Parameters
        self.A = A
        self.U = U
        
        # State variables
        self.LAI = 1.0  # Leaf Area Index
        self.HEC_ab = 0.0  # Heat exchange coefficient [W/(m2.K)]
        self.Q_flow = 0.0  # Heat flow rate [W]
        
    def update(self, 
              LAI: float,
              T_a: float,
              T_b: float) -> float:
        """
        Update canopy free convection model state
        
        Parameters:
            LAI (float): Leaf Area Index
            T_a (float): Temperature at port a [K]
            T_b (float): Temperature at port b [K]
            
        Returns:
            float: Heat flow rate [W]
        """
        # Update leaf area index
        self.LAI = LAI
        
        # Calculate temperature difference
        dT = T_b - T_a
        
        # Calculate heat exchange coefficient
        self.HEC_ab = 2 * self.LAI * self.U
        
        # Calculate heat flow
        self.Q_flow = self.A * self.HEC_ab * dT
        
        return self.Q_flow
