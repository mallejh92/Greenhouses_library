import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_b import HeatPort_b

class Radiation_N:
    """
    Lumped thermal element for radiation heat transfer between N discrete volumes and a single surface.
    
    This model describes thermal radiation (electromagnetic radiation) emitted between bodies
    as a result of their temperatures. The constitutive equation used is:
        Q_flow = Gr * sigma * (T_a^4 - T_b^4)
    where Gr is the radiation conductance and sigma is the Stefan-Boltzmann constant.
    
    Parameters for greenhouse elements:
    - glass cover: 0.84
    - pipes: 0.88
    - canopy leaves: 1.00
    - concrete floor: 0.89
    - thermal screen: 1.00
    """
    
    def __init__(self, A, epsilon_a, epsilon_b, N=2):
        """
        Initialize Radiation_N model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        epsilon_a : float
            Emissivity coefficient of surface A (0-1)
        epsilon_b : float
            Emissivity coefficient of surface B (0-1)
        N : int, optional
            Number of discrete flow volumes (default: 2)
        """
        # Parameters
        self.A = A
        self.epsilon_a = epsilon_a
        self.epsilon_b = epsilon_b
        self.N = N
        
        # Varying inputs (view factors)
        self.FFa = 1.0    # View factor of element A
        self.FFb = 1.0    # View factor of element B
        self.FFab1 = 0.0  # View factor of intermediate element 1
        self.FFab2 = 0.0  # View factor of intermediate element 2
        self.FFab3 = 0.0  # View factor of intermediate element 3
        self.FFab4 = 0.0  # View factor of intermediate element 4
        
        # Initialize heat ports
        self.heatPorts_a = np.array([HeatPort_a() for _ in range(N)], dtype=object)
        self.port_b = HeatPort_b()
        
        # State variables
        self.dT4 = np.zeros(N)  # Temperature difference to the 4th power
        self.Q_flow = 0.0       # Total heat flow rate [W]
        self.REC_ab = 0.0       # Radiation exchange coefficient [W/(m²·K⁴)]
        self.sigma = 5.67e-8

        
        # Calculate initial radiation exchange coefficient
        self._update_REC_ab()
    
    def _update_REC_ab(self):
        """Update radiation exchange coefficient"""
        self.REC_ab = (self.epsilon_a * self.epsilon_b * self.FFa * self.FFb * 
                      (1 - self.FFab1) * (1 - self.FFab2) * 
                      (1 - self.FFab3) * (1 - self.FFab4) * self.sigma)
    
    def set_heatPorts_a_temperature(self, T):
        """
        Set temperature for all heatPorts_a
        
        Parameters:
        -----------
        T : float or array-like
            Temperature value(s) to set. If float, same value is set for all ports.
            If array-like, must have length equal to N.
        """
        if isinstance(T, (int, float)):
            for port in self.heatPorts_a:
                port.T = T
        else:
            if len(T) != self.N:
                raise ValueError(f"Temperature array length must match N={self.N}")
            for port, t in zip(self.heatPorts_a, T):
                port.T = t
    
    def step(self):
        """
        Advance simulation by one time step
        """
        # Calculate temperature differences to the 4th power
        for i in range(self.N):
            self.dT4[i] = self.heatPorts_a[i].T**4 - self.port_b.T**4
        
        # Calculate heat flows for each port
        for i in range(self.N):
            self.heatPorts_a[i].Q_flow = (self.A / self.N) * self.REC_ab * self.dT4[i]
        
        # Calculate total heat flow
        self.Q_flow = np.sum([port.Q_flow for port in self.heatPorts_a])
        
        # Set port_b heat flow (negative of total)
        self.port_b.Q_flow = -self.Q_flow

        return self.Q_flow
