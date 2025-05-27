import numpy as np
from Interfaces.Heat.HeatPorts_a import HeatPorts_a
from Interfaces.Heat.HeatPorts_b import HeatPorts_b

class Radiation_N:
    """
    Lumped thermal element for radiation heat transfer between multiple surfaces.
    """
    def __init__(self, A, epsilon_a, epsilon_b, N=2):
        """
        Initialize the Radiation_N model
        Parameters:
            A (float): Floor surface area [m²]
            epsilon_a (float): Emissivity coefficient of surface A
            epsilon_b (float): Emissivity coefficient of surface B
            N (int): Number of discrete flow volumes
        """
        if N < 1:
            raise ValueError("N must be greater than or equal to 1")
        self.A = A
        self.epsilon_a = epsilon_a
        self.epsilon_b = epsilon_b
        self.N = N
        self.sigma = 5.67e-8
        self.FFa = 1.0
        self.FFb = 1.0
        self.FFab1 = 0.0
        self.FFab2 = 0.0
        self.FFab3 = 0.0
        self.FFab4 = 0.0
        self.dT4 = np.zeros(N)
        self.Q_flow = 0.0
        self.REC_ab = 0.0
        # Modelica-style port names
        self.heatPorts_a = HeatPorts_a(N)
        self.heatPort_b = HeatPorts_b(1)[0]
    def step(self, dt):
        """
        Update the radiation heat transfer calculation
        Parameters:
            dt (float): Time step [s]
        """
        for i in range(self.N):
            self.dT4[i] = self.heatPorts_a[i].T**4 - self.heatPort_b.T**4
        self.REC_ab = (self.epsilon_a * self.epsilon_b * self.FFa * self.FFb * 
                      (1 - self.FFab1) * (1 - self.FFab2) * 
                      (1 - self.FFab3) * (1 - self.FFab4) * self.sigma)
        for i in range(self.N):
            self.heatPorts_a[i].Q_flow = self.A / self.N * self.REC_ab * self.dT4[i]
        self.Q_flow = sum(port.Q_flow for port in self.heatPorts_a.ports)
        self.heatPort_b.Q_flow = -self.Q_flow
