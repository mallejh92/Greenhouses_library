import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.Element1D import Element1D

class PipeFreeConvection(Element1D):
    """
    Heating pipe heat exchange by free or hindered convection with air
    
    This model computes the heat transfer between heating pipes and air in a greenhouse system.
    The magnitude of convective heat depends on the pipe position:
    - freePipe=True: pipes in free air (free convection)
    - freePipe=False: pipes situated close to the canopy and near the floor (hindered convection)
    
    The free convection is modeled based on the Nu-Ra relation [1], while the hindered convection
    is modeled by experimental correlations [2].
    
    References:
    [1] Luc Balemans. Assessment of criteria for energetic effectiveness of
        greenhouse screens. PhD thesis, Agricultural University, Ghent, 1989.
    [2] G.P.A Bot. Greenhouse climate : from physical processes to a dynamic
        model. PhD thesis, Wageningen University, 1983.
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
        super().__init__()  # Element1D의 __init__ 호출
        
        # Parameters (Modelica parameters)
        self.A = A
        self.d = d
        self.l = l
        self.freePipe = freePipe
        
        # Variables (Modelica variables)
        self.HEC_ab = 0  # Heat exchange coefficient
        self.alpha = 0   # Convection coefficient
        
    def step(self):
        """
        Calculate and update heat transfer by pipe convection.
        
        Returns:
        --------
        Q_flow : float
            Heat flow rate [W] from port_a to port_b
            
        Raises:
            RuntimeError: If ports are not properly connected
        """
        # 포트 연결 확인
        if not hasattr(self, 'port_a') or not hasattr(self, 'port_b'):
            raise RuntimeError("Both port_a and port_b must be connected before calling step()")
            
        # Get temperatures from ports
        T_a = self.port_a.T
        T_b = self.port_b.T
        
        # 온도 검증
        if T_a <= 0 or T_b <= 0:
            raise ValueError("Temperatures must be positive (in Kelvin)")
        
        # Calculate temperature difference
        dT = T_b - T_a
        
        # Calculate convection coefficient based on conditions (Modelica equation)
        if abs(dT) > 0:
            if self.freePipe:
                self.alpha = 1.28 * self.d**(-0.25) * max(1e-9, abs(dT))**0.25
            else:
                self.alpha = 1.99 * max(1e-9, abs(dT))**0.32
        else:
            self.alpha = 0
            
        # Calculate heat exchange coefficient (Modelica equation)
        self.HEC_ab = self.alpha * np.pi * self.d * self.l
        
        # Calculate heat flow (Modelica equation)
        Q_flow = self.A * self.HEC_ab * dT
        
        # Update ports
        self.port_a.Q_flow = Q_flow
        self.port_b.Q_flow = -Q_flow
        
        # Update Element1D
        self.update()
        
        return Q_flow
