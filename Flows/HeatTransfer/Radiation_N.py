import numpy as np
from Interfaces.Heat.HeatPorts_a import HeatPorts_a
from Interfaces.Heat.HeatPorts_b import HeatPorts_b

class Radiation_N:
    """
    Lumped thermal element for radiation heat transfer
    
    This class implements the radiation heat transfer model between multiple surfaces
    in a greenhouse system.
    """
    
    def __init__(self, A, epsilon_a, epsilon_b, N=2):
        """
        Initialize the Radiation_N model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        epsilon_a : float
            Emissivity coefficient of surface A
        epsilon_b : float
            Emissivity coefficient of surface B
        N : int, optional
            Number of discrete flow volumes, default is 2
        """
        if N < 1:
            raise ValueError("N must be greater than or equal to 1")
            
        self.A = A
        self.epsilon_a = epsilon_a
        self.epsilon_b = epsilon_b
        self.N = N
        
        # Constants
        self.sigma = 5.67e-8  # Stefan-Boltzmann constant [W/(m²·K⁴)]
        
        # State variables
        self.FFa = 1.0  # View factor of element A
        self.FFb = 1.0  # View factor of element B
        self.FFab1 = 0.0  # View factor of intermediate element between A and B
        self.FFab2 = 0.0  # View factor of intermediate element between A and B
        self.FFab3 = 0.0  # View factor of intermediate element between A and B
        self.FFab4 = 0.0  # View factor of intermediate element between A and B
        
        # Initialize heat ports
        self.heatPorts_a = HeatPorts_a(N)  # Vector of heat ports
        self.port_b = HeatPorts_b(1)[0]  # Single heat port using HeatPorts_b
        
    def calculate(self):
        """
        Calculate heat transfer by radiation
        
        This method updates the Q_flow values in the heat ports directly,
        similar to the Modelica implementation.
        """
        # Calculate temperature differences to the fourth power
        dT4 = np.zeros(self.N)
        for i in range(self.N):
            dT4[i] = self.heatPorts_a[i].T**4 - self.port_b.T**4
            
        # Calculate radiation exchange coefficient
        REC_ab = (self.epsilon_a * self.epsilon_b * self.FFa * self.FFb * 
                 (1 - self.FFab1) * (1 - self.FFab2) * 
                 (1 - self.FFab3) * (1 - self.FFab4) * self.sigma)
        
        # Calculate individual heat flows
        for i in range(self.N):
            self.heatPorts_a[i].Q_flow = self.A / self.N * REC_ab * dT4[i]
            
        # Calculate total heat flow
        Q_flow = sum(port.Q_flow for port in self.heatPorts_a.ports)
        self.port_b.Q_flow = -Q_flow  # Negative sign as in original Modelica code
        
        return Q_flow
