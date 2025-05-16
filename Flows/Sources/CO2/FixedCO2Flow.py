class FixedCO2Flow:
    """
    Fixed CO2 flow boundary condition model.
    This model allows a specified amount of CO2 flow rate to be injected into a system at a given port.
    The constant amount of CO2 flow rate MC_flow is given as a parameter.
    The CO2 flows into the component to which this component is connected if parameter MC_flow is positive.
    """
    
    def __init__(self, MC_flow):
        """
        Initialize the FixedCO2Flow model.
        
        Args:
            MC_flow (float): Fixed CO2 flow rate in mg/(m2.s)
        """
        self.MC_flow = MC_flow  # Fixed heat flow rate at port
        self.port = None  # CO2Port_b connection
        
    def connect_port(self, port):
        """
        Connect a CO2Port_b to this component.
        
        Args:
            port: CO2Port_b instance to connect
        """
        self.port = port
        
    def calculate(self):
        """
        Calculate the CO2 flow at the port.
        The negative sign indicates that the flow is going into the connected component.
        """
        if self.port is not None:
            self.port.MC_flow = -self.MC_flow
