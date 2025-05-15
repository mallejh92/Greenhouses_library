import numpy as np

class PipeFreeConvection:
    """
    Heating pipe heat exchange by free or hindered convection with air
    
    This class implements the heat transfer model for convection between heating pipes
    and air in a greenhouse system.
    """
    
    def __init__(self, A, d, l, freePipe=True):
        """
        Initialize the PipeFreeConvection model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        d : float
            Characteristic dimension of the pipe (pipe diameter) [m]
        l : float
            Length of heating pipes per m² floor surface [m]
        freePipe : bool, optional
            True if pipe in free air, false if hindered pipe, default is True
        """
        self.A = A
        self.d = d
        self.l = l
        self.freePipe = freePipe
        
    def calculate_heat_transfer(self, T_a, T_b):
        """
        Calculate heat transfer by pipe convection
        
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
        # Calculate temperature difference
        dT = T_b - T_a
        
        # Calculate convection coefficient based on conditions
        if abs(dT) > 0:
            if self.freePipe:
                alpha = 1.28 * self.d**(-0.25) * max(1e-9, abs(dT))**0.25
            else:
                alpha = 1.99 * max(1e-9, abs(dT))**0.32
        else:
            alpha = 0
            
        # Calculate heat exchange coefficient
        HEC_ab = alpha * np.pi * self.d * self.l
        
        # Calculate heat flow
        Q_flow = self.A * HEC_ab * dT
        
        return Q_flow
