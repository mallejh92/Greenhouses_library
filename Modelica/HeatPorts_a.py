from .HeatPort import HeatPort

class HeatPorts_a:
    """
    Modelica의 HeatPorts_a 인터페이스
    
    이 클래스는 Modelica의 HeatPorts_a 커넥터를 구현합니다.
    열전달 포트의 벡터를 나타내며, 각 포트는 온도와 열유량을 가집니다.
    
    속성:
        ports (list): 열전달 포트 리스트
    """
    
    def __init__(self, size=1):
        """
        HeatPorts_a 초기화
        
        매개변수:
            size (int): 포트 벡터의 크기 (기본값: 1)
        """
        self.ports = [HeatPort() for _ in range(size)]
    
    def __getitem__(self, index):
        """
        지정된 인덱스의 열전달 포트 반환
        
        매개변수:
            index (int): 열전달 포트의 인덱스
            
        반환:
            HeatPort: 지정된 인덱스의 열전달 포트
        """
        return self.ports[index]
    
    def __setitem__(self, index, port):
        """
        지정된 인덱스에 열전달 포트 설정
        
        매개변수:
            index (int): 열전달 포트의 인덱스
            port (HeatPort): 설정할 열전달 포트
        """
        if not isinstance(port, HeatPort):
            raise TypeError("HeatPort 타입만 설정 가능합니다")
        self.ports[index] = port
    
    def __len__(self):
        """
        열전달 포트의 개수 반환
        
        반환:
            int: 열전달 포트의 개수
        """
        return len(self.ports)
    
    def connect(self, other):
        """
        다른 HeatPorts_a와 연결
        
        매개변수:
            other (HeatPorts_a): 연결할 다른 HeatPorts_a
            
        예외:
            TypeError: 다른 커넥터가 HeatPorts_a 타입이 아닌 경우
            ValueError: 벡터 크기가 다른 경우
        """
        if not isinstance(other, HeatPorts_a):
            raise TypeError("HeatPorts_a 타입의 커넥터만 연결 가능합니다")
        if len(self) != len(other):
            raise ValueError("다른 크기의 열전달 포트 벡터는 연결할 수 없습니다")
        
        # 각 포트 연결
        for i in range(len(self)):
            self.ports[i].connect(other.ports[i])
    
    def __str__(self):
        """열전달 포트 벡터의 문자열 표현"""
        return (f"HeatPorts_a (크기: {len(self)})\n" +
                "\n".join(f"포트 {i}: {port}" for i, port in enumerate(self.ports))) 