import numpy as np
from Interfaces.Heat.HeatPorts_a import HeatPorts_a
from Interfaces.Heat.HeatPorts_b import HeatPorts_b

class PipeFreeConvection_N:
    """
    Heating pipe heat exchange by free or hindered convection with air
    
    This class implements the heat transfer model for convection between multiple heating pipes
    and air in a greenhouse system.
    """
    
    def __init__(self, N_p=1, N=2, A=0, d=0, l=0, freePipe=True):
        """
        Initialize the PipeFreeConvection_N model
        
        Parameters:
        -----------
        N_p : int, optional
            Number of pipes in parallel, default is 1
        N : int, optional
            Number of cells for pipe side, default is 2
        A : float
            Floor surface area [m²]
        d : float
            Characteristic dimension of the pipe (pipe diameter) [m]
        l : float
            Length of heating pipes [m]
        freePipe : bool, optional
            True if pipe in free air, false if hindered pipe, default is True
        """
        if N_p < 1 or N < 1:
            raise ValueError("N_p and N must be greater than or equal to 1")
            
        self.N_p = N_p
        self.N = N
        self.A = A
        self.d = d
        self.l = l
        self.freePipe = freePipe
        
        # Initialize heat ports
        self.heatPorts_a = HeatPorts_a(N)  # Vector of heat ports
        self.port_b = HeatPorts_b(1)[0]  # Single heat port using HeatPorts_b
        
    def calculate(self):
        """
        Calculate heat transfer by pipe convection for multiple pipes
        
        This method updates the Q_flow values in the heat ports directly,
        similar to the Modelica implementation.
        """
        # Initialize arrays
        dT = np.zeros(self.N)
        alpha = np.zeros(self.N)
        HEC_ab = np.zeros(self.N)
        
        # Calculate for each pipe
        for i in range(self.N):
            # Calculate temperature difference
            dT[i] = self.heatPorts_a[i].T - self.port_b.T
            
            # Calculate convection coefficient
            if self.freePipe:
                alpha[i] = 1.28 * self.d**(-0.25) * max(1e-9, abs(dT[i]))**0.25
            else:
                alpha[i] = 1.99 * max(1e-9, abs(dT[i]))**0.32
                
            # Calculate heat exchange coefficient
            HEC_ab[i] = alpha[i] * np.pi * self.d * self.l * self.N_p / self.A
            
            # Calculate individual heat flow
            self.heatPorts_a[i].Q_flow = self.A / self.N * HEC_ab[i] * dT[i]
            
        # Calculate total heat flow
        Q_flow = sum(port.Q_flow for port in self.heatPorts_a.ports)
        self.port_b.Q_flow = -Q_flow  # Negative sign as in original Modelica code
        
        return Q_flow
