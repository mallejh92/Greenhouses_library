from Interfaces.CO2.CO2Port_a import CO2Port_a
from Interfaces.CO2.CO2Port_b import CO2Port_b

class Element1D:
    """
    Partial CO2 mass transfer element with two CO2Port connectors that does not store energy
    
    This partial model contains the basic connectors and variables to
    allow CO2 transfer models to be created that do not store energy.
    This model defines and includes equations for the CO2 concentration
    drop across the element, dC, and the CO2 flow rate through the
    element from port_a to port_b, MC_flow.
    
    By extending this model, it is possible to write simple
    constitutive equations for many types of CO2 transfer components.
    
    Attributes:
        MC_flow (float): CO2 flow rate from port_a -> port_b in mg/(m²·s)
        dC (float): port_a.CO2 - port_b.CO2 in mg/m³
        port_a (CO2Port_a): CO2 port a (inlet)
        port_b (CO2Port_b): CO2 port b (outlet)
    """
    
    def __init__(self):
        """Initialize Element1D"""
        self.MC_flow = 0.0  # CO2 flow rate
        self.dC = 0.0       # CO2 concentration difference
        self.port_a = CO2Port_a()  # inlet port
        self.port_b = CO2Port_b()  # outlet port
    
    def update(self) -> None:
        """
        Update the element state
        
        This method implements the Modelica equations:
        - dC = port_a.CO2 - port_b.CO2
        - port_a.MC_flow = MC_flow
        - port_b.MC_flow = -MC_flow
        """
        # Update concentration difference
        self.dC = self.port_a.CO2 - self.port_b.CO2
        
        # Update flow rates
        self.port_a.MC_flow = self.MC_flow
        self.port_b.MC_flow = -self.MC_flow
    
    def set_flow_rate(self, MC_flow: float) -> None:
        """
        Set CO2 flow rate
        
        Args:
            MC_flow (float): CO2 flow rate in mg/(m²·s)
        """
        self.MC_flow = float(MC_flow)
        self.update()
    
    def get_flow_rate(self) -> float:
        """
        Get CO2 flow rate
        
        Returns:
            float: CO2 flow rate in mg/(m²·s)
        """
        return self.MC_flow
    
    def get_concentration_difference(self) -> float:
        """
        Get CO2 concentration difference
        
        Returns:
            float: CO2 concentration difference in mg/m³
        """
        return self.dC
    
    def connect_port_a(self, other: CO2Port_a) -> None:
        """
        Connect port_a to another CO2Port_a
        
        Args:
            other (CO2Port_a): CO2Port_a to connect with
        """
        self.port_a = other
        self.update()
    
    def connect_port_b(self, other: CO2Port_b) -> None:
        """
        Connect port_b to another CO2Port_b
        
        Args:
            other (CO2Port_b): CO2Port_b to connect with
        """
        self.port_b = other
        self.update()
    
    def __str__(self) -> str:
        """String representation of the element"""
        return (f"Element1D\n"
                f"MC_flow = {self.MC_flow:.2f} mg/(m²·s)\n"
                f"dC = {self.dC:.2f} mg/m³\n"
                f"Port A:\n{self.port_a}\n"
                f"Port B:\n{self.port_b}")
