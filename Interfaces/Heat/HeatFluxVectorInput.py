"""
Modelica HeatFluxVectorInput connector implementation
Original Modelica: connector HeatFluxVectorInput = input Modelica.SIunits.HeatFlux
"""
from typing import List, Union

class HeatFluxVectorInput:
    """
    Heat Flux Vector Input connector - 원본 Modelica와 동일하게 단순화
    
    Original Modelica: connector HeatFluxVectorInput = input Modelica.SIunits.HeatFlux
    단순히 float 값들의 리스트를 래핑하는 최소한의 클래스
    """
    
    def __init__(self, values: Union[List[float], float, None] = None):
        """
        HeatFluxVectorInput 초기화
        
        Args:
            values: float 값 또는 float 리스트
        """
        if values is None:
            self.values = []
        elif isinstance(values, (list, tuple)):
            self.values = [float(v) for v in values]
        else:
            self.values = [float(values)]
    
    def __len__(self) -> int:
        """길이 반환"""
        return len(self.values)
    
    def __getitem__(self, index: int) -> float:
        """인덱스로 값 가져오기"""
        return self.values[index]
    
    def __setitem__(self, index: int, value: float) -> None:
        """인덱스로 값 설정"""
        self.values[index] = float(value)
    
    def __iter__(self):
        """반복자"""
        return iter(self.values)
    
    def __str__(self) -> str:
        """문자열 표현"""
        return str(self.values)
    
    def __repr__(self) -> str:
        """객체 표현"""
        return f"HeatFluxVectorInput({self.values})"
    
    def append(self, value: float) -> None:
        """값 추가"""
        self.values.append(float(value))

def create_heat_flux_vector_input(values=None):
    """
    HeatFluxVectorInput 생성 함수
    
    Args:
        values: float 값 또는 float 리스트
        
    Returns:
        HeatFluxVectorInput: 열유속 벡터 입력 객체
    """
    return HeatFluxVectorInput(values)