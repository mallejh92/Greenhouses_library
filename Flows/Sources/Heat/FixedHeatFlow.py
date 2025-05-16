from Interfaces.Heat.HeatPorts_b import HeatPorts_b

class FixedHeatFlow:
    """
    Fixed heat flow boundary condition model.
    This model allows a specified amount of heat flow rate to be "injected"
    into a thermal system at a given port. The constant amount of heat
    flow rate Q_flow is given as a parameter. The heat flows into the
    component to which this component is connected if parameter Q_flow is positive.
    
    Attributes:
        Q_flow (float): Fixed heat flow rate at port in W
        port (HeatPorts_b): Connected heat port
    """
    
    def __init__(self, Q_flow: float):
        """
        Initialize the FixedHeatFlow model.
        
        Args:
            Q_flow (float): Fixed heat flow rate at port in W
        """
        # Parameters
        self.Q_flow = Q_flow  # Fixed heat flow rate at port
        
        # Connections
        self.port: HeatPorts_b = None  # HeatPorts_b connection
        
    def connect_port(self, port: HeatPorts_b) -> None:
        """
        Connect a HeatPorts_b to this component.
        
        Args:
            port (HeatPorts_b): HeatPorts_b instance to connect
        """
        self.port = port
        
    def calculate(self) -> None:
        """
        Calculate and apply the heat flow to the port.
        The negative sign indicates that the heat flows into the connected component
        if Q_flow is positive.
        """
        if self.port is not None:
            self.port.Q_flow = -self.Q_flow
            
    def __str__(self) -> str:
        """String representation of the FixedHeatFlow model"""
        return (f"FixedHeatFlow\n"
                f"Q_flow = {self.Q_flow:.2f} W\n"
                f"Port connected: {self.port is not None}")
