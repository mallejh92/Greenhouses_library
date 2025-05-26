class HeatPort:
    """
    Modelica의 기본 열전달 포트 인터페이스
    
    이 클래스는 Modelica의 기본 열전달 포트를 구현합니다.
    포트는 온도(T)와 열유량(Q_flow)을 포함합니다.
    
    속성:
        T (float): 포트 온도 [K]
        Q_flow (float): 열유량 (양수는 포트로 들어가는 방향) [W]
    """
    def __init__(self, T_start=293.15):
        """
        열전달 포트 초기화
        
        매개변수:
            T_start (float): 초기 온도 [K]
        """
        self.T = T_start  # 포트 온도 [K]
        self.Q_flow = 0.0  # 열유량 [W]
    
    def connect(self, other):
        """
        다른 열전달 포트와 연결
        
        매개변수:
            other (HeatPort): 연결할 다른 열전달 포트
            
        설명:
            - 연결된 포트들의 온도(T)는 같아야 합니다.
            - 열유량(Q_flow)의 합은 0이어야 합니다 (Modelica의 flow 변수 특성).
        """
        if not isinstance(other, HeatPort):
            raise TypeError("HeatPort 타입의 포트만 연결 가능합니다")
        
        # 연결된 포트들의 온도는 같아야 함
        self.T = other.T
        
        # Modelica에서 연결점의 Q_flow 합은 0이어야 함
        # Q_flow가 양수이면 포트로 들어가는 방향
        self.Q_flow = -other.Q_flow
    
    def __str__(self):
        """열전달 포트의 문자열 표현"""
        return f"HeatPort(T={self.T:.2f}K, Q_flow={self.Q_flow:.2f}W)" 