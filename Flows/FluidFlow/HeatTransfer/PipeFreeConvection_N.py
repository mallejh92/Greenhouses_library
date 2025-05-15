import numpy as np
from typing import Optional, List, Tuple

class PipeFreeConvection_N:
    """
    Heating pipe heat exchange by free or hindered convection with air
    
    This model calculates heat exchange between multiple heating pipes in parallel
    and air by free convection or hindered convection based on pipe characteristics
    and temperature differences.
    """
    
    def __init__(self, 
                 N_p: int = 1,
                 N: int = 2,
                 A: float = 0.0,
                 d: float = 0.0,
                 l: float = 0.0,
                 freePipe: bool = True):
        """
        Initialize pipe free convection model for multiple pipes
        
        Parameters:
            N_p (int): Number of pipes in parallel
            N (int): Number of cells for pipe side
            A (float): Floor surface area [m2]
            d (float): Characteristic dimension of the pipe (pipe diameter) [m]
            l (float): Length of heating pipes [m]
            freePipe (bool): True if pipe in free air, false if hindered pipe
        """
        # Parameters
        self.N_p = max(1, N_p)  # Ensure at least 1 pipe
        self.N = max(1, N)      # Ensure at least 1 cell
        self.A = A
        self.d = d
        self.l = l
        self.freePipe = freePipe
        
        # State variables
        self.HEC_ab = np.zeros(N)  # Heat exchange coefficients [W/(m2.K)]
        self.alpha = np.zeros(N)   # Convection coefficients
        self.dT = np.zeros(N)      # Temperature differences [K]
        self.Q_flow = 0.0          # Total heat flow rate [W]
        self.Q_flow_cells = np.zeros(N)  # Heat flow rates per cell [W]
        
    def update(self, 
              T_pipes: List[float],
              T_air: float) -> Tuple[float, List[float]]:
        """
        Update pipe free convection model state
        
        Parameters:
            T_pipes (List[float]): Temperatures of pipe cells [K]
            T_air (float): Temperature of air [K]
            
        Returns:
            Tuple[float, List[float]]: (Total heat flow rate, Heat flow rates per cell)
        """
        # Calculate temperature differences
        self.dT = np.array(T_pipes) - T_air
        
        # Calculate convection coefficients and heat flows for each cell
        for i in range(self.N):
            if self.freePipe:
                self.alpha[i] = 1.28 * self.d**(-0.25) * max(1e-9, abs(self.dT[i]))**0.25
            else:
                self.alpha[i] = 1.99 * max(1e-9, abs(self.dT[i]))**0.32
                
            # Calculate heat exchange coefficient
            self.HEC_ab[i] = (self.alpha[i] * np.pi * self.d * self.l * self.N_p / self.A)
            
            # Calculate heat flow for this cell
            self.Q_flow_cells[i] = (self.A / self.N) * self.HEC_ab[i] * self.dT[i]
            
        # Calculate total heat flow
        self.Q_flow = np.sum(self.Q_flow_cells)
        
        return self.Q_flow, self.Q_flow_cells.tolist()
