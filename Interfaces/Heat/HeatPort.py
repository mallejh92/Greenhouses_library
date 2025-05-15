class HeatPort:
    """
    Heat Port connector (Modelica.Thermal.HeatTransfer.Interfaces.HeatPort)
    
    This class implements the Modelica HeatPort connector in Python.
    It represents a single-node heat port with temperature and heat flow rate.
    
    Attributes:
        T (float): Temperature in Kelvin
        Q_flow (float): Heat flow rate in Watts
    """
    
    def __init__(self, T: float = 293.15, Q_flow: float = 0.0):
        """
        Initialize HeatPort
        
        Args:
            T (float): Initial temperature in Kelvin (default: 293.15)
            Q_flow (float): Initial heat flow rate in Watts (default: 0.0)
        """
        self.T = float(T)
        self.Q_flow = float(Q_flow)
    
    def connect(self, other: 'HeatPort') -> None:
        """
        Connect this heat port to another heat port
        
        Args:
            other (HeatPort): Other heat port to connect with
            
        Raises:
            TypeError: If the other connector is not of type HeatPort
        """
        if not isinstance(other, HeatPort):
            raise TypeError("Can only connect with HeatPort type connectors")
        
        # Connect temperature and heat flow
        self.T = other.T
        self.Q_flow = other.Q_flow
    
    def __str__(self) -> str:
        """String representation of the heat port"""
        return (f"HeatPort\n"
                f"T = {self.T:.2f} K\n"
                f"Q_flow = {self.Q_flow:.2f} W") 