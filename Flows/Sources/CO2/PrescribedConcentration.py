from Interfaces.CO2.CO2Port_b import CO2Port_b

class PrescribedConcentration:
    """
    Variable CO2 concentration boundary condition model.
    This model represents a variable CO2 concentration boundary condition in mg/m3.
    The CO2 concentration is given as input signal to the model.
    The effect is that an instance of this model acts as an infinite reservoir
    able to absorb or generate as much CO2 as required to keep the concentration
    at the specified value.
    
    Attributes:
        port (CO2Port_b): Connected CO2 port
        CO2 (float): Input CO2 concentration in mg/m3
    """
    
    def __init__(self):
        """
        Initialize the PrescribedConcentration model.
        """
        # Connections
        self.port: CO2Port_b = None  # CO2Port_b connection
        self.CO2: float = None  # Input CO2 concentration
        
    def connect_port(self, port: CO2Port_b) -> None:
        """
        Connect a CO2Port_b to this component.
        
        Args:
            port (CO2Port_b): CO2Port_b instance to connect
        """
        self.port = port
        
    def connect_CO2(self, concentration: float) -> None:
        """
        Connect a CO2 concentration input value.
        
        Args:
            concentration (float): CO2 concentration in mg/m3
        """
        self.CO2 = concentration
        
    def calculate(self) -> None:
        """
        Calculate and apply the CO2 concentration to the port.
        The input CO2 concentration is directly applied to the connected port.
        """
        if self.port is not None and self.CO2 is not None:
            self.port.CO2 = self.CO2
            
    def __str__(self) -> str:
        """String representation of the PrescribedConcentration model"""
        return (f"PrescribedConcentration\n"
                f"CO2 = {self.CO2 if self.CO2 is not None else 'Not connected'} mg/m3\n"
                f"Port connected: {self.port is not None}")
