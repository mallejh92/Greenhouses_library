from .FluidPort import FluidPort, Medium

class FluidPort_b(FluidPort):
    """
    Modelica의 출구 유체 포트 인터페이스
    
    이 클래스는 Modelica의 FluidPort_b 커넥터를 구현합니다.
    FluidPort를 상속받으며, 출구 유체 포트를 나타냅니다.
    
    Note:
        FluidPort_a와 FluidPort_b는 아이콘 레이아웃만 다르고 기능적으로는 동일합니다.
        양의 질량유량(m_flow)은 포트로 들어가는 방향을 의미합니다.
    """
    def __init__(self, Medium=Medium(), p_start=1e5, h_start=0.0):
        """
        FluidPort_b 초기화
        
        매개변수:
            Medium (class): 매체 모델
            p_start (float): 초기 압력 [Pa]
            h_start (float): 초기 비엔탈피 [J/kg]
        """
        super().__init__(Medium, p_start, h_start)
    
    def __str__(self):
        """유체 포트의 문자열 표현"""
        return (f"FluidPort_b(p={self.p:.2f} Pa, m_flow={self.m_flow:.2f} kg/s, "
                f"h_outflow={self.h_outflow:.2f} J/kg)") 