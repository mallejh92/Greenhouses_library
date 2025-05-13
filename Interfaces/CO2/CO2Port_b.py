from Interfaces.CO2.CO2Port import CO2Port

class CO2Port_b(CO2Port):
    """
    CO2 port for 1-dim. CO2 transfer (unfilled rectangular icon)
    
    This class extends CO2Port with an unfilled rectangular icon representation.
    It is used for 1-dimensional CO2 transfer between components.
    
    The variables in the connector are:
    - CO2: CO2 concentration in [mg/m³]
    - MC_flow: CO2 flow rate in [mg/(m²·s)]
    
    According to the Modelica sign convention, a positive CO2 flow rate
    MC_flow is considered to flow into a component. This convention has
    to be used whenever this connector is used in a model class.
    
    Note that CO2Port_a and CO2Port_b are identical with the only
    exception of the different icon layout.
    
    Attributes:
        CO2 (float): Partial CO2 pressure in mg/m³
        MC_flow (float): CO2 flow rate in mg/(m²·s)
                        (positive if flowing from outside into the component)
    """
    
    def __init__(self, CO2: float = 0.0, MC_flow: float = 0.0, name: str = "port_b"):
        """
        Initialize CO2Port_b
        
        Args:
            CO2 (float): Initial CO2 concentration in mg/m³ (default: 0.0)
            MC_flow (float): Initial CO2 flow rate in mg/(m²·s) (default: 0.0)
            name (str): Component name (default: "port_b")
        """
        super().__init__(CO2, MC_flow)
        self.name = name
    
    def __str__(self) -> str:
        """String representation of the CO2 port"""
        return (f"CO2Port_b(name={self.name})\n"
                f"CO2 = {self.CO2:.2f} mg/m³\n"
                f"MC_flow = {self.MC_flow:.2f} mg/(m²·s)")
