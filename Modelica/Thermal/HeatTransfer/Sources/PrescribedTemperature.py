from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_b import HeatPort_b

class PrescribedTemperature:
    """
    Variable temperature boundary condition in Kelvin.
    
    This model represents a variable temperature boundary condition. The temperature in [K] 
    is given as input signal T to the model. The effect is that an instance of this model 
    acts as an infinite reservoir able to absorb or generate as much energy as required 
    to keep the temperature at the specified value.
    
    Attributes:
    -----------
    port : HeatPort_b
        Heat port for connection to other components
    T : float
        Prescribed temperature [K]
    """
    
    def __init__(self, T_start=293.15):
        """
        Initialize PrescribedTemperature component
        
        Parameters:
        -----------
        T_start : float
            Initial temperature [K]
        """
        self.port = HeatPort_b(T_start=T_start)
        self.T = T_start
    
    def connect_port(self, port):
        """
        Connect to another heat port
        
        Parameters:
        -----------
        port : HeatPort_b
            Heat port to connect to
        """
        self.port = port
        self.port.T = self.T
    
    def connect_T(self, T):
        """
        Set prescribed temperature and update port
        
        Parameters:
        -----------
        T : float
            Temperature [K]
        """
        if T <= 0:
            raise ValueError("Temperature must be positive (in Kelvin)")
        self.T = T
        self.port.T = T
        self.port.Q_flow = 0.0  # 열유량 초기화
    
    def calculate(self):
        """
        Update port temperature to prescribed value
        """
        self.port.T = self.T
        self.port.Q_flow = 0.0  # 열유량 초기화 