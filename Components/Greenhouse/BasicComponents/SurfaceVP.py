from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a

class SurfaceVP:
    """
    표면 온도에 따른 포화 수증기압을 계산하는 기본 모델
    
    이 모델은 표면의 온도를 입력으로 받아 해당 온도에서의 포화 수증기압을 계산합니다.
    Cover, Canopy, ThermalScreen 모델에서 사용됩니다.
    """
    
    def __init__(self, T=300.0):
        """
        SurfaceVP 초기화
        
        Parameters:
        -----------
        T : float
            표면 온도 [K] (기본값: 300.0)
        """
        # Varying inputs
        self.T = T  # 표면 온도 [K]
        
        # Variables
        self.VP = 0.0  # 수증기압 [Pa]
        
        # Connectors
        self.port = WaterMassPort_a()  # 포화 수증기압 포트
        
        # 초기 계산
        self.step(0)  # dt=0으로 초기 업데이트
    
    def saturated_vapor_pressure(self, temp_C):
        """
        포화 수증기압 계산 [Pa]
        
        Parameters:
        -----------
        temp_C : float
            온도 [°C]
            
        Returns:
        --------
        float
            포화 수증기압 [Pa]
        """
        from math import exp
        return 610.78 * exp(17.269 * temp_C / (temp_C + 237.3))
    
    def step(self, dt):
        """
        시간 스텝 업데이트 (SurfaceVP는 상태 변화가 없는 순수 함수이므로 dt는 사용하지 않음)
        
        Parameters:
        -----------
        dt : float
            시간 스텝 [s] (이 모델에서는 사용하지 않음)
        """
        # Modelica 방정식: VP = Functions.SaturatedVapourPressure(T - 273.15)
        T_C = self.T - 273.15
        self.VP = self.saturated_vapor_pressure(T_C)
        
        # Modelica 방정식: port.VP = VP
        self.port.VP = self.VP
    
    def set_temperature(self, T):
        """
        온도 설정 및 즉시 업데이트
        
        Parameters:
        -----------
        T : float
            표면 온도 [K]
        """
        self.T = T
        self.step(0)  # 즉시 업데이트
    
    def get_vapor_pressure(self):
        """
        현재 수증기압 반환
        
        Returns:
        --------
        float
            수증기압 [Pa]
        """
        return self.VP