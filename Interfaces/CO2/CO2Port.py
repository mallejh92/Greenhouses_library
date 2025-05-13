class CO2Port:
    """
    CO2 port for 1-dim. CO2 transfer
    
    This class implements the Modelica CO2Port connector in Python.
    It represents a port for CO2 transfer with concentration and flow rate.
    
    Attributes:
        CO2 (float): Partial CO2 pressure in mg/m³
        MC_flow (float): CO2 flow rate in mg/(m²·s)
                        (positive if flowing from outside into the component)
    """
    
    def __init__(self, CO2: float = 0.0, MC_flow: float = 0.0):
        """
        Initialize CO2Port
        
        Args:
            CO2 (float): Initial CO2 concentration in mg/m³ (default: 0.0)
            MC_flow (float): Initial CO2 flow rate in mg/(m²·s) (default: 0.0)
        """
        self.CO2 = float(CO2)
        self.MC_flow = float(MC_flow)
    
    def set_concentration(self, CO2: float) -> None:
        """
        Set CO2 concentration
        
        Args:
            CO2 (float): CO2 concentration in mg/m³
        """
        self.CO2 = float(CO2)
    
    def set_flow_rate(self, MC_flow: float) -> None:
        """
        Set CO2 flow rate
        
        Args:
            MC_flow (float): CO2 flow rate in mg/(m²·s)
        """
        self.MC_flow = float(MC_flow)
    
    def get_concentration(self) -> float:
        """
        Get CO2 concentration
        
        Returns:
            float: CO2 concentration in mg/m³
        """
        return self.CO2
    
    def get_flow_rate(self) -> float:
        """
        Get CO2 flow rate
        
        Returns:
            float: CO2 flow rate in mg/(m²·s)
        """
        return self.MC_flow
    
    def connect(self, other: 'CO2Port') -> None:
        """
        Connect this CO2 port to another CO2 port
        
        Args:
            other (CO2Port): Other CO2 port to connect with
            
        Raises:
            TypeError: If the other connector is not of type CO2Port
        """
        if not isinstance(other, CO2Port):
            raise TypeError("Can only connect with CO2Port type connectors")
        
        # Connect concentration and flow rate
        self.CO2 = other.CO2
        self.MC_flow = other.MC_flow
    
    def __str__(self) -> str:
        """String representation of the CO2 port"""
        return (f"CO2Port\n"
                f"CO2 = {self.CO2:.2f} mg/m³\n"
                f"MC_flow = {self.MC_flow:.2f} mg/(m²·s)")
