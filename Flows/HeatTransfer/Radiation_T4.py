import numpy as np
from Interfaces.Heat.Element1D import Element1D

class Radiation_T4(Element1D):
    """
    Lumped thermal element for radiation heat transfer between two surfaces.
    """
    def __init__(self, A, epsilon_a, epsilon_b, FFa=1.0, FFb=1.0, FFab1=0.0, FFab2=0.0, FFab3=0.0, FFab4=0.0):
        """
        Initialize the Radiation_T4 model
        Parameters:
            A (float): Floor surface area [m²]
            epsilon_a (float): Emissivity coefficient of surface A
            epsilon_b (float): Emissivity coefficient of surface B
            FFa, FFb, FFab1-4: View factors
        """
        super().__init__()
        self.A = A
        self.epsilon_a = epsilon_a
        self.epsilon_b = epsilon_b
        self.sigma = 5.67e-8
        self.FFa = FFa
        self.FFb = FFb
        self.FFab1 = FFab1
        self.FFab2 = FFab2
        self.FFab3 = FFab3
        self.FFab4 = FFab4
    def step(self, dt=None):
        """
        Calculate heat transfer by radiation
        Parameters:
            dt (float, optional): Time step [s]
        Returns:
            Q_flow (float): Heat flow rate [W]
        """
        REC_ab = (self.epsilon_a * self.epsilon_b * self.FFa * self.FFb * 
                 (1 - self.FFab1) * (1 - self.FFab2) * 
                 (1 - self.FFab3) * (1 - self.FFab4) * self.sigma)
        Q_flow = self.A * REC_ab * (self.heatPort_a.T**4 - self.heatPort_b.T**4)
        self.heatPort_a.Q_flow = Q_flow
        self.heatPort_b.Q_flow = -Q_flow
        return Q_flow
