"""
Modelica HeatFluxInput connector implementation
Original Modelica: connector HeatFluxInput = input Modelica.SIunits.HeatFlux
"""

# 원본 Modelica와 동일: 단순한 float 값
HeatFlux = float

class HeatFluxInput:
    """
    Heat Flux Input connector - 원본 Modelica와 동일하게 단순화
    
    Original Modelica: connector HeatFluxInput = input Modelica.SIunits.HeatFlux
    단순히 float 값을 래핑하는 최소한의 클래스
    """
    
    def __init__(self, value: float = 0.0):
        """
        HeatFluxInput 초기화
        
        Args:
            value (float): 열유속 값 [W/m²]
        """
        self.value = float(value)
    
    def __float__(self) -> float:
        """float로 변환"""
        return self.value
    
    def __str__(self) -> str:
        """문자열 표현"""
        return str(self.value)
    
    def __repr__(self) -> str:
        """객체 표현"""
        return f"HeatFluxInput({self.value})"

def create_heat_flux_input(value=0.0):
    """
    HeatFluxInput 생성 함수
    
    Args:
        value (float): 열유속 값 [W/m²]
        
    Returns:
        HeatFluxInput: 열유속 입력 객체
    """
    return HeatFluxInput(value)
