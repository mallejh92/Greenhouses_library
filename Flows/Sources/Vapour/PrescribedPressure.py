from Interfaces.Vapour.WaterMassPort_b import WaterMassPort_b

class PrescribedPressure:
    """
    Variable pressure boundary condition model.
    This model represents a variable pressure boundary condition in Pascals.
    The pressure is given as input signal to the model.
    The effect is that an instance of this model acts as an infinite reservoir
    able to absorb or generate as much water vapour as required to keep the pressure
    at the specified value.
    
    Attributes:
        port (WaterMassPort_b): Connected water mass port
        VP (float): Input vapour pressure in Pa
    """
    
    def __init__(self):
        """
        Initialize the PrescribedPressure model.
        """
        # Connections
        self.port: WaterMassPort_b = None  # WaterMassPort_b connection
        self.VP: float = None  # Input vapour pressure
        
    def connect_port(self, port: WaterMassPort_b) -> None:
        """
        Connect a WaterMassPort_b to this component.
        
        Args:
            port (WaterMassPort_b): WaterMassPort_b instance to connect
        """
        self.port = port
        
    def connect_VP(self, pressure: float) -> None:
        """
        Connect a vapour pressure input value.
        
        Args:
            pressure (float): Vapour pressure in Pa
        """
        self.VP = pressure
        
    def calculate(self) -> None:
        """
        Calculate and apply the vapour pressure to the port.
        The input vapour pressure is directly applied to the connected port.
        """
        if self.port is not None and self.VP is not None:
            self.port.VP = self.VP
            
    def __str__(self) -> str:
        """String representation of the PrescribedPressure model"""
        return (f"PrescribedPressure\n"
                f"VP = {self.VP if self.VP is not None else 'Not connected'} Pa\n"
                f"Port connected: {self.port is not None}")
