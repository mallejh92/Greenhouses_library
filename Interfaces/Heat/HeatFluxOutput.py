"""
Modelica HeatFluxOutput connector implementation
Original Modelica: connector HeatFluxOutput = output Modelica.SIunits.HeatFlux
"""
from typing import Optional, Union
from Interfaces.Heat.HeatFluxInput import HeatFlux, HeatFluxInput

class HeatFluxOutput:
    """
    Heat Flux Output connector - 원본 Modelica와 동일하게 단순화
    
    Original Modelica: connector HeatFluxOutput = output Modelica.SIunits.HeatFlux
    단순히 float 값을 래핑하는 최소한의 클래스
    """
    
    def __init__(self, value: Optional[Union[HeatFlux, float]] = None, name: str = "I"):
        """
        HeatFluxOutput 초기화
        
        Args:
            value: 초기 열유속 값 (float 또는 HeatFlux)
            name (str): 연결자 이름
        """
        self.name = name
        if value is None:
            self.value = 0.0
        elif isinstance(value, (int, float)):
            self.value = float(value)
        else:
            self.value = float(value)
    
    def __str__(self) -> str:
        """문자열 표현"""
        return f"{self.name}: {self.value}"
    
    def __float__(self) -> float:
        """float로 변환"""
        return self.value
    
    def __repr__(self) -> str:
        """객체 표현"""
        return f"HeatFluxOutput({self.value}, name='{self.name}')"
    
    def connect(self, other: HeatFluxInput) -> None:
        """
        HeatFluxInput에 연결
        
        Args:
            other (HeatFluxInput): 연결할 입력 연결자
        """
        if not isinstance(other, HeatFluxInput):
            raise TypeError("HeatFluxInput 타입의 연결자만 연결 가능")
        other.value = self.value
