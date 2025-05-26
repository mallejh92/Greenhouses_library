from .HeatPort_a import HeatPort_a
from .HeatPort_b import HeatPort_b

class Element1D:
    """
    Modelica의 Element1D 인터페이스
    
    이 클래스는 Modelica의 Element1D 인터페이스를 구현합니다.
    에너지를 저장하지 않는 열전달 요소를 위한 기본 커넥터와 변수를 포함합니다.
    
    속성:
        Q_flow (float): port_a에서 port_b로의 열유량 [W]
        dT (float): 온도차 (port_a.T - port_b.T) [K]
        port_a (HeatPort_a): 입구 열전달 포트
        port_b (HeatPort_b): 출구 열전달 포트
    """
    def __init__(self, T_a_start=293.15, T_b_start=293.15):
        """
        Element1D 초기화
        
        매개변수:
            T_a_start (float): port_a의 초기 온도 [K]
            T_b_start (float): port_b의 초기 온도 [K]
        """
        # 열전달 포트
        self.port_a = HeatPort_a(T_start=T_a_start)
        self.port_b = HeatPort_b(T_start=T_b_start)
        
        # 열전달 변수
        self.Q_flow = 0.0
        self.dT = self.port_a.T - self.port_b.T

    def update(self):
        """
        Modelica 방정식을 구현:
        dT = port_a.T - port_b.T
        port_a.Q_flow = Q_flow
        port_b.Q_flow = -Q_flow
        """
        # 온도차 계산
        self.dT = self.port_a.T - self.port_b.T
        
        # 열유량 설정 (Modelica의 flow 변수 특성)
        self.port_a.Q_flow = self.Q_flow
        self.port_b.Q_flow = -self.Q_flow 