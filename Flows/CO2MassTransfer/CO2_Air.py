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
        """Initialize the CO2 air model (Modelica initial equation)"""
        self.CO2 = self.CO2_start
        if self.steadystate:
            self.MC_flow = 0.0  # Modelica: der(CO2) = 0 during initialization
        self.CO2_ppm = self.CO2 / 1.94

        # Port 초기화
        self.port.CO2 = self.CO2

        # PrescribedConcentration 연결 (Modelica 원본과 일치)
        self.prescribedPressure.connect_port(self.port)
        self.prescribedPressure.connect_CO2(self.CO2)
        self.prescribedPressure.calculate()
        
    def step(self, dt: float):
        """
        Update CO2 concentration for one time step (Modelica equation: der(CO2) = 1/cap_CO2 * MC_flow)
        
        Args:
            dt (float): Time step [s]
        """
        # Modelica 원본 방정식: port.MC_flow = MC_flow
        self.port.MC_flow = self.MC_flow

        # Modelica 원본 방정식: der(CO2) = 1/cap_CO2 * MC_flow
        if not self.steadystate:
            # Forward Euler integration: CO2(t+dt) = CO2(t) + dt * der(CO2)
            self.CO2 += (1.0 / self.cap_CO2) * self.MC_flow * dt
            # **중요**: Modelica 원본에는 농도 하한 제한이 없음 - 제거

        # Modelica 원본 방정식: CO2_ppm = CO2/1.94
        self.CO2_ppm = self.CO2 / 1.94

        # Port 업데이트
        self.port.CO2 = self.CO2
        
        # PrescribedConcentration 업데이트
        self.prescribedPressure.connect_CO2(self.CO2)
        self.prescribedPressure.calculate()

        return self.CO2, self.CO2_ppm, self.MC_flow
