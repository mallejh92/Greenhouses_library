from .HeatPort import HeatPort

class HeatPort_a(HeatPort):
    """
    Modelica의 HeatPort_a 인터페이스
    
    이 클래스는 Modelica의 HeatPort_a 커넥터를 구현합니다.
    HeatPort를 상속받으며, 채워진 사각형 아이콘을 가진 1차원 열전달 포트입니다.
    
    Note:
        HeatPort_a와 HeatPort_b는 아이콘 레이아웃만 다르고 기능적으로는 동일합니다.
        양의 열유량(Q_flow)은 컴포넌트로 들어가는 방향을 의미합니다.
    """
    def __init__(self, T_start=293.15):
        """
        HeatPort_a 초기화
        
        매개변수:
            T_start (float): 초기 온도 [K]
        """
        super().__init__(T_start)
    
    def __str__(self):
        """열전달 포트의 문자열 표현"""
        return f"HeatPort_a(T={self.T:.2f}K, Q_flow={self.Q_flow:.2f}W)" 