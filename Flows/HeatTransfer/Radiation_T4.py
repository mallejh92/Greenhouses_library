import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.Element1D import Element1D

class Radiation_T4(Element1D):
    """
    Lumped thermal element for radiation heat transfer between two surfaces.
    
    This model describes the thermal radiation between two bodies as a result of their temperatures.
    The constitutive equation used is:
        Q_flow = Gr*sigma*(port_a.T^4 - port_b.T^4)
    where Gr is the radiation conductance and sigma is the Stefan-Boltzmann constant.
    
    Typical emissivity values for greenhouse elements:
    - glass cover: 0.84
    - pipes: 0.88
    - canopy leaves: 1.00
    - concrete floor: 0.89
    - thermal screen: 1.00
    """
    def __init__(self, A, epsilon_a, epsilon_b, FFa=1.0, FFb=1.0, FFab1=0.0, FFab2=0.0, FFab3=0.0, FFab4=0.0):
        """
        Initialize the Radiation_T4 model
        
        Parameters:
            A (float): Floor surface area [m²]
            epsilon_a (float): Emissivity coefficient of surface A (0-1)
            epsilon_b (float): Emissivity coefficient of surface B (0-1)
            FFa (float): View factor of element A (default: 1.0)
            FFb (float): View factor of element B (default: 1.0)
            FFab1-4 (float): View factors of intermediate elements between A and B (default: 0.0)
        """
        super().__init__()  # Element1D의 __init__ 호출
        
        # Parameters
        self.A = A
        self.epsilon_a = epsilon_a
        self.epsilon_b = epsilon_b
        self.FFa = FFa
        self.FFb = FFb
        self.FFab1 = FFab1
        self.FFab2 = FFab2
        self.FFab3 = FFab3
        self.FFab4 = FFab4
        
        # Stefan-Boltzmann constant [W/(m²·K⁴)]
        self.sigma = 5.67e-8

    def step(self, dt=None):
        # 1) Modelica와 동일하게 REC_ab 매 스텝마다 재계산
        REC_ab = (self.epsilon_a * self.epsilon_b * self.FFa * self.FFb * 
                 (1 - self.FFab1) * (1 - self.FFab2) * 
                 (1 - self.FFab3) * (1 - self.FFab4) * self.sigma)
        
        # 2) 현재 포트 온도를 Kelvin으로 읽어 온 뒤
        T_a = self.port_a.T   # <-- 반드시 Kelvin으로 들어와야 함
        T_b = self.port_b.T   # <-- Kelvin
        
        # 3) 복사열 계산
        Q_flow = self.A * REC_ab * (T_a**4 - T_b**4)
        
        # 4) 포트에 반영
        self.port_a.Q_flow = Q_flow
        self.port_b.Q_flow = -Q_flow
        
        return Q_flow
