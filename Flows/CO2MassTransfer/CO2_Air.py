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
        """
        Initialize the system according to initial equations
        """
        # Set initial CO2 value
        self.CO2 = self.CO2_start
        
        # If in steady state, ensure MC_flow is zero
        if self.steadystate:
            self.MC_flow = 0.0
            
        # Update derived values
        self.CO2_ppm = self.CO2 / 1.94
        
        # Modelica 원본 연결 설정
        self._setup_connections()
        
    def _setup_connections(self):
        """Modelica 원본의 connect 문들을 구현"""
        # connect(prescribedPressure.port, port)
        self.prescribedPressure.connect_port(self.port)
        
        # connect(portCO2.y, prescribedPressure.CO2) - RealExpression은 CO2 값을 직접 전달
        self.prescribedPressure.connect_CO2(self.CO2)
        
    def step(self, dt: float):
        """
        Update CO2 concentration (Modelica 방정식 구현)
        
        Modelica 방정식:
        - port.MC_flow = MC_flow
        - der(CO2) = 1/cap_CO2 * MC_flow
        - CO2_ppm = CO2/1.94
        
        Parameters:
            dt (float): Time step [s]
        """
        # Modelica: port.MC_flow = MC_flow
        self.port.MC_flow = self.MC_flow
        
        # Modelica: der(CO2) = 1/cap_CO2 * MC_flow
        if not self.steadystate:
            self.CO2 += (1.0 / self.cap_CO2) * self.MC_flow * dt
            
        # Modelica: CO2_ppm = CO2/1.94
        self.CO2_ppm = self.CO2 / 1.94
        
        # RealExpression 업데이트: portCO2.y = CO2
        self.prescribedPressure.connect_CO2(self.CO2)
        self.prescribedPressure.calculate()
        
        return self.CO2, self.CO2_ppm
