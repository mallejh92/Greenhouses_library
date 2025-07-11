from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_b import HeatPort_b

class PrescribedTemperature:
    """
    Variable temperature boundary condition in Kelvin
    원본 Modelica: port.T = T
    """
    
    def __init__(self, T_start=293.15):
        """
        PrescribedTemperature 초기화
        
        Args:
            T_start (float): 초기 온도 [K]
        """
        self.T = T_start  # 입력 온도 [K]
        self.port = HeatPort_b(T_start=T_start)  # 열 포트
        
        # 원본 Modelica 방정식: port.T = T
        self.port.T = self.T
    
    def update_temperature(self, T):
        """
        온도 업데이트 (원본 Modelica: port.T = T)
        
        Args:
            T (float): 새로운 온도 [K]
        """
        self.T = T
        self.port.T = T 