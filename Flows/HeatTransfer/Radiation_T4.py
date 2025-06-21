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

    Note:
    - port_a.T and port_b.T must be in Kelvin
    - All view factors (FFa, FFb, FFab1-4) must be between 0 and 1
    - Emissivity coefficients (epsilon_a, epsilon_b) must be between 0 and 1
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
            
        Raises:
            ValueError: If any parameter is outside its valid range
        """
        super().__init__()  # Element1D의 __init__ 호출
        
        # 입력값 검증
        if not (0 <= epsilon_a <= 1):
            raise ValueError(f"epsilon_a must be between 0 and 1, got {epsilon_a}")
        if not (0 <= epsilon_b <= 1):
            raise ValueError(f"epsilon_b must be between 0 and 1, got {epsilon_b}")
        if not (0 <= FFa <= 1):
            raise ValueError(f"FFa must be between 0 and 1, got {FFa}")
        if not (0 <= FFb <= 1):
            raise ValueError(f"FFb must be between 0 and 1, got {FFb}")
        if not all(0 <= ff <= 1 for ff in [FFab1, FFab2, FFab3, FFab4]):
            raise ValueError("All FFab values must be between 0 and 1")
        if A <= 0:
            raise ValueError(f"Surface area A must be positive, got {A}")
        
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
        
        # Radiation exchange coefficient [W/(m²·K⁴)]
        self.REC_ab = 0.0
        
        # Calculate initial radiation exchange coefficient
        self._update_REC_ab()

    def _update_REC_ab(self):
        """
        Update radiation exchange coefficient based on current view factors.
        
        This method recalculates the radiation exchange coefficient (REC_ab)
        using the current view factor values. It should be called whenever
        view factors are updated.
        """
        # View Factor가 0이면 복사 열전달도 0
        if self.FFa <= 0 or self.FFb <= 0:
            self.REC_ab = 0.0
        else:
            self.REC_ab = (self.epsilon_a * self.epsilon_b * self.FFa * self.FFb * 
                          (1 - self.FFab1) * (1 - self.FFab2) * 
                          (1 - self.FFab3) * (1 - self.FFab4) * self.sigma)

    def step(self, dt=None):
        """
        Calculate and update radiation heat transfer between two surfaces.
        
        Returns:
            float: Heat flow rate [W] from port_a to port_b
            
        Raises:
            RuntimeError: If ports are not properly connected
        """
        # 포트 연결 확인
        if not hasattr(self, 'port_a') or not hasattr(self, 'port_b'):
            raise RuntimeError("Both port_a and port_b must be connected before calling step()")
            
        # 1) Modelica와 동일하게 REC_ab 매 스텝마다 재계산
        self._update_REC_ab()
        
        # 2) 현재 포트 온도를 Kelvin으로 읽어 온 뒤
        T_a = self.port_a.T   # <-- 반드시 Kelvin으로 들어와야 함
        T_b = self.port_b.T   # <-- Kelvin
        
        # 온도 검증
        if T_a <= 0 or T_b <= 0:
            raise ValueError("Temperatures must be positive (in Kelvin)")
        
        # 3) 복사열 계산
        Q_flow = self.A * self.REC_ab * (T_a**4 - T_b**4)
        
        # 4) 클래스의 Q_flow 속성에 저장 (중요!)
        self.Q_flow = Q_flow
        
        # 5) 포트에 반영
        self.port_a.Q_flow = Q_flow
        self.port_b.Q_flow = -Q_flow
        
        # 6) Element1D의 update() 호출하여 포트 열유량 업데이트
        self.update()
        
        return Q_flow
