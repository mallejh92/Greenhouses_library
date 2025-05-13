class HeatPort_a:
    """
    Heat Port connector (Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a)
    
    This class implements the Modelica HeatPort_a connector in Python.
    It represents a single-node heat port with temperature and heat flow rate.
    
    Attributes:
        T (float): Temperature in Kelvin
        Q_flow (float): Heat flow rate in Watts
    """
    
    def __init__(self, T: float = 293.15, Q_flow: float = 0.0):
        """
        Initialize HeatPort_a
        
        Args:
            T (float): Initial temperature in Kelvin (default: 293.15)
            Q_flow (float): Initial heat flow rate in Watts (default: 0.0)
        """
        self.T = float(T)
        self.Q_flow = float(Q_flow)
    
    def set_temperature(self, T: float) -> None:
        """
        Set temperature
        
        Args:
            T (float): Temperature in Kelvin
        """
        self.T = float(T)
    
    def set_heat_flow(self, Q_flow: float) -> None:
        """
        Set heat flow rate
        
        Args:
            Q_flow (float): Heat flow rate in Watts
        """
        self.Q_flow = float(Q_flow)
    
    def get_temperature(self) -> float:
        """
        Get temperature
        
        Returns:
            float: Temperature in Kelvin
        """
        return self.T
    
    def get_heat_flow(self) -> float:
        """
        Get heat flow rate
        
        Returns:
            float: Heat flow rate in Watts
        """
        return self.Q_flow
    
    def connect(self, other: 'HeatPort_a') -> None:
        """
        Connect this heat port to another heat port
        
        Args:
            other (HeatPort_a): Other heat port to connect with
            
        Raises:
            TypeError: If the other connector is not of type HeatPort_a
        """
        if not isinstance(other, HeatPort_a):
            raise TypeError("Can only connect with HeatPort_a type connectors")
        
        # Connect temperature and heat flow
        self.T = other.T
        self.Q_flow = other.Q_flow
    
    def __str__(self) -> str:
        """String representation of the heat port"""
        return (f"HeatPort_a\n"
                f"T = {self.T:.2f} K\n"
                f"Q_flow = {self.Q_flow:.2f} W") 