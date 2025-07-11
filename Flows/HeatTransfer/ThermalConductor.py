from Modelica.Thermal.HeatTransfer.Interfaces.Element1D import Element1D

class ThermalConductor(Element1D):
    """
    열을 저장하지 않고 전달하는 집중 열소자
    
    Element1D를 상속받아 열전도체 모델을 구현합니다.
    
    열전도도 G는 다양한 기하학적 형태에 대해 계산할 수 있습니다:
    
    1. 박스 형태 (열이 박스 길이를 따라 흐름):
       G = k*A/L
       여기서:
       k: 열전도계수 (재료 상수)
       A: 박스 면적
       L: 박스 길이
    
    2. 원통 형태 (열이 내부에서 외부 반지름으로 흐름):
       G = 2*pi*k*L/log(r_out/r_in)
       여기서:
       k: 열전도계수 (재료 상수)
       L: 원통 길이
       r_out: 외부 반지름
       r_in: 내부 반지름
    """
    
    def __init__(self, G=1.0):
        """
        ThermalConductor 모델 초기화
        
        Args:
            G (float): 재료의 열전도도 [W/K], 기본값은 1.0
        """
        super().__init__()  # Element1D 초기화 (port_a, port_b 자동 생성)
        self.G = G  # 재료의 열전도도
        self._Q_flow = 0.0  # 열유량 [W]
        
    @property
    def dT(self):
        """
        포트 간 온도차
        
        Returns:
            float: 온도차 [K]
        """
        # 포트가 None인 경우 안전장치
        if self.port_a is None or self.port_b is None:
            return 0.0
        return self.port_a.T - self.port_b.T
        
    def calculate(self):
        """
        열전도체를 통한 열전달 계산
        
        Returns:
            float: 열유량 [W]
        """
        # 포트가 None인 경우 안전장치
        if self.port_a is None or self.port_b is None:
            self._Q_flow = 0.0
            return self._Q_flow
        
        # Q_flow = G * dT를 사용하여 열유량 계산
        self._Q_flow = self.G * self.dT
        self.port_a.Q_flow = self._Q_flow  # 포트 a의 열유량 설정
        self.port_b.Q_flow = -self._Q_flow  # 포트 b의 열유량 설정 (반대 방향)
        return self._Q_flow
        
    def get_Q_flow(self):
        """
        현재 열유량 반환
        
        Returns:
            float: 열유량 [W]
        """
        return self._Q_flow
