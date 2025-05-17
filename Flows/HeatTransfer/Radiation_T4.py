import numpy as np
from Interfaces.Heat.Element1D import Element1D

class Radiation_T4(Element1D):
    """
    Lumped thermal element for radiation heat transfer
    
    This class implements the radiation heat transfer model between two surfaces
    in a greenhouse system.
    """
    
    def __init__(self, A, epsilon_a, epsilon_b, FFa=1.0, FFb=1.0, FFab1=0.0, FFab2=0.0, FFab3=0.0, FFab4=0.0):
        """
        Initialize the Radiation_T4 model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        epsilon_a : float
            Emissivity coefficient of surface A
        epsilon_b : float
            Emissivity coefficient of surface B
        FFa : float, optional
            View factor of element A, default is 1.0
        FFb : float, optional
            View factor of element B, default is 1.0
        FFab1 : float, optional
            View factor of intermediate element between A and B, default is 0.0
        FFab2 : float, optional
            View factor of intermediate element between A and B, default is 0.0
        FFab3 : float, optional
            View factor of intermediate element between A and B, default is 0.0
        FFab4 : float, optional
            View factor of intermediate element between A and B, default is 0.0
        """
        super().__init__()  # Initialize Element1D
        
        self.A = A
        self.epsilon_a = epsilon_a
        self.epsilon_b = epsilon_b
        
        # Constants
        self.sigma = 5.67e-8  # Stefan-Boltzmann constant [W/(m²·K⁴)]
        
        # State variables
        self.FFa = FFa  # View factor of element A
        self.FFb = FFb  # View factor of element B
        self.FFab1 = FFab1  # View factor of intermediate element between A and B
        self.FFab2 = FFab2  # View factor of intermediate element between A and B
        self.FFab3 = FFab3  # View factor of intermediate element between A and B
        self.FFab4 = FFab4  # View factor of intermediate element between A and B
        
    def calculate(self):
        """
        Calculate heat transfer by radiation
        
        This method updates the Q_flow values in the heat ports directly,
        similar to the Modelica implementation.
        
        Returns:
        --------
        Q_flow : float
            Heat flow rate [W]
        """
        # Calculate radiation exchange coefficient
        REC_ab = (self.epsilon_a * self.epsilon_b * self.FFa * self.FFb * 
                 (1 - self.FFab1) * (1 - self.FFab2) * 
                 (1 - self.FFab3) * (1 - self.FFab4) * self.sigma)
        
        # Calculate heat flow
        Q_flow = self.A * REC_ab * (self.port_a.T**4 - self.port_b.T**4)
        
        # Update heat flows
        self.port_a.Q_flow = Q_flow
        self.port_b.Q_flow = -Q_flow  # Negative sign as in original Modelica code
        
        return Q_flow
