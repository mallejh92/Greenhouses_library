from Interfaces.CO2.CO2Port_b import CO2Port_b

class FixedCO2Flow:
    """
    Fixed CO2 flow boundary condition model.
    This model allows a specified amount of CO2 flow rate to be injected into a system at a given port.
    The constant amount of CO2 flow rate MC_flow is given as a parameter.
    The CO2 flows into the component to which this component is connected if parameter MC_flow is positive.
    """
    
    def __init__(self, MC_flow: float, name: str = "FixedCO2Flow"):
        """
        Initialize the FixedCO2Flow model.
        
        Args:
            MC_flow (float): Fixed CO2 flow rate in mg/(m²·s)
            name (str): Component name (default: "FixedCO2Flow")
        """
        self.MC_flow = MC_flow  # Fixed CO2 flow rate at port
        self.name = name
        self.port = CO2Port_b(name=f"{name}.port")  # CO2Port_b connection
        
    def calculate(self):
        """
        Calculate the CO2 flow at the port.
        The negative sign indicates that the flow is going into the connected component.
        """
        self.port.MC_flow = -self.MC_flow
    
    def __str__(self) -> str:
        """String representation of the FixedCO2Flow component"""
        return (f"FixedCO2Flow(name={self.name})\n"
                f"MC_flow = {self.MC_flow:.2f} mg/(m²·s)\n"
                f"port.MC_flow = {self.port.MC_flow:.2f} mg/(m²·s)")
