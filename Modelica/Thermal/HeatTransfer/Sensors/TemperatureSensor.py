from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a

class TemperatureSensor:
    """
    이상적인 절대 온도 센서 (K)
    - 연결된 포트의 온도를 그대로 출력
    - 센서 자체는 열적 상호작용 없음
    """
    def __init__(self):
        self.port = HeatPort_a()  # 입력 포트
        self.T = 273.15           # 출력: 절대온도(K)

    def measure(self):
        """
        연결된 포트의 온도를 읽어와 T에 저장
        """
        self.T = self.port.T
        return self.T
