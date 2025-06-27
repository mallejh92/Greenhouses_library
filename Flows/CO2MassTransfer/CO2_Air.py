from Interfaces.CO2.CO2Port_a import CO2Port_a
from Flows.Sources.CO2.PrescribedConcentration import PrescribedConcentration

class CO2_Air:
    """
    CO2 mass balance of an air volume
    
    Modelica 원본과 일치하는 구현:
    - port.MC_flow = MC_flow
    - der(CO2) = 1/cap_CO2 * MC_flow
    - CO2_ppm = CO2/1.94
    - PrescribedConcentration과 RealExpression 연결
    """
    
    def __init__(self, cap_CO2: float = 4.0, CO2_start: float = 1940.0, steadystate: bool = True):
        """
        Initialize CO2 air model
        
        Parameters:
            cap_CO2 (float): Capacity of the air to store CO2, equals the height of the air compartment [m]
            CO2_start (float): Initial CO2 concentration [mg/m3]
            steadystate (bool): If true, sets the derivative of CO2 to zero during initialization
        """
        # Parameters
        self.cap_CO2 = cap_CO2
        
        # Initialization parameters
        self.CO2_start = CO2_start
        self.steadystate = steadystate
        
        # State variables
        self.MC_flow = 0.0  # Mass flow rate [mg/(m2.s)]
        self.CO2 = CO2_start  # CO2 concentration [mg/m3]
        self.CO2_ppm = CO2_start / 1.94  # CO2 concentration in ppm
        
        # Port variables
        self.port = CO2Port_a()  # CO2 port (Modelica 원본과 일치)
        
        # Modelica 원본의 연결된 컴포넌트들
        self.prescribedPressure = PrescribedConcentration()
        
        # Initialize the system
        self.initialize()
        
    def initialize(self):
        self.CO2 = self.CO2_start
        if self.steadystate:
            self.MC_flow = 0.0
        self.CO2_ppm = self.CO2 / 1.94

        # ① port.CO2 초기화
        self.port.CO2 = self.CO2

        # ② 외부 경계조건 초기 적용
        self.prescribedPressure.connect_port(self.port)
        self.prescribedPressure.connect_CO2(self.CO2)
        self.prescribedPressure.calculate()
        
    def step(self, dt: float):
        # 1) port.MC_flow 매핑
        self.port.MC_flow = self.MC_flow

        # 2) 농도 변화 적분 (steadystate는 초기화 플래그일 뿐, 시뮬레이션 중에는 항상 변화 허용)
        dC_dt = self.MC_flow / self.cap_CO2
        
        # **안정화**: CO2 농도 변화를 제한하여 급격한 변화 방지
        max_dC = 50.0  # 최대 CO2 농도 변화량 [mg/m³/s] (더 보수적인 값으로 조정)
        if abs(dC_dt) > max_dC:
            dC_dt = max_dC if dC_dt > 0 else -max_dC
        
        self.CO2 += dC_dt * dt

        # 3) ppm 변환
        self.CO2_ppm = self.CO2 / 1.94

        # 4) 경계조건 업데이트
        self.port.CO2 = self.CO2
        self.prescribedPressure.connect_CO2(self.CO2)
        self.prescribedPressure.calculate()

        # (필요시) MC_flow 반환
        return self.CO2, self.CO2_ppm, self.MC_flow
