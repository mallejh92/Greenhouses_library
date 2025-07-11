from typing import Optional, Union, List
import pandas as pd
from Interfaces.Heat.HeatFluxInput import HeatFlux
from Interfaces.Heat.HeatFluxVectorInput import HeatFluxVectorInput

class HeatFluxVectorOutput:
    """
    HeatFlux 벡터 출력 연결자
    
    Modelica HeatFluxVectorOutput 연결자의 Python 구현
    여러 열유속 값을 출력으로 보내는 인터페이스 제공
    """
    
    def __init__(self, values: Optional[Union[List[float], float]] = None, 
                 name: str = "u"):
        """
        HeatFluxVectorOutput 연결자 초기화
        
        Args:
            values: float 값들의 리스트 또는 단일 float 값
            name (str): 연결자 이름
        """
        self.name = name
        
        if values is None:
            self.values: List[float] = []
        elif isinstance(values, (list, tuple)):
            self.values = [float(v) for v in values]
        elif isinstance(values, (int, float)):
            self.values = [float(values)]
        else:
            self.values = [float(values)]
    
    def __str__(self) -> str:
        """문자열 표현"""
        values_str = ", ".join(str(v) for v in self.values)
        return f"{self.name}: [{values_str}]"
    
    def __len__(self) -> int:
        """열유속 값의 개수 반환"""
        return len(self.values)
    
    def __getitem__(self, index: int) -> float:
        """지정된 인덱스의 열유속 값 반환"""
        return self.values[index]
    
    def __setitem__(self, index: int, value: Union[float, int]) -> None:
        """지정된 인덱스의 열유속 값 설정"""
        self.values[index] = float(value)
    
    def append(self, value: Union[float, int]) -> None:
        """새로운 열유속 값을 벡터에 추가"""
        self.values.append(float(value))
    
    def connect(self, other: HeatFluxVectorInput) -> None:
        """
        HeatFluxVectorInput에 연결
        
        Args:
            other (HeatFluxVectorInput): 연결할 입력 벡터 연결자
        """
        if not isinstance(other, HeatFluxVectorInput):
            raise TypeError("HeatFluxVectorInput 타입의 연결자만 연결 가능")
        
        # float 값들을 직접 전달
        other.values = self.values.copy()
    
    def to_pandas(self) -> 'pd.DataFrame':
        """열유속 값들을 pandas DataFrame으로 변환"""
        import pandas as pd
        return pd.DataFrame({
            'heat_flux': self.values
        })
