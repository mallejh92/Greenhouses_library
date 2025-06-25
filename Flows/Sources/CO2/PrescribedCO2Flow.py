from Interfaces.CO2.CO2Port_b import CO2Port_b

class PrescribedCO2Flow:
    """
    Prescribed CO2 flow boundary condition model.
    This model allows a specified amount of CO2 flow rate to be injected into a system at a given port.
    The CO2 flow rate is calculated based on the external CO2 source capacity and control valve input.
    
    The model calculates the CO2 flow rate (MC_flow) based on:
    - phi_ExtCO2: Specific capacity of the external CO2 source in g/(m2.h)
    - U_MCext: Control valve input (0-1) or U_ExtCO2 if no input is connected
    
    The calculated MC_flow is then applied to the connected CO2Port_b.
    According to the Modelica sign convention, a negative MC_flow indicates
    flow into the connected component.
    
    Attributes:
        phi_ExtCO2 (float): Specific capacity of the external CO2 source in g/(m2.h)
        U_ExtCO2 (float): Default control valve value (0-1)
        MC_flow (float): Calculated CO2 flow rate in mg/(m2.s)
        port (CO2Port_b): Connected CO2 port
        U_MCext (float): Control valve input value (0-1)
    """
    
    def __init__(self, phi_ExtCO2: float = 27.0):
        """
        Initialize the PrescribedCO2Flow model.
        
        Args:
            phi_ExtCO2 (float): Specific capacity of the external CO2 source in g/(m2.h)
        """
        # Parameters
        self.phi_ExtCO2 = phi_ExtCO2  # Specific capacity of the external CO2 source
        
        # Varying inputs
        self.U_ExtCO2 = 0.0  # Control valve of the external CO2 source
        
        # Variables
        self.MC_flow = 0.0  # CO2 flow rate at port in mg/(m2.s)
        
        # Connections
        self.port = CO2Port_b()  # CO2Port_b connection - 자동 초기화
        self.U_MCext: float = None  # RealInput connection
        
    def connect_port(self, port: CO2Port_b) -> None:
        """
        Connect a CO2Port_b to this component.
        
        Args:
            port (CO2Port_b): CO2Port_b instance to connect
        """
        self.port = port
        
    def connect_U_MCext(self, input_value: float) -> None:
        """
        Connect a real input value for U_MCext.
        
        Args:
            input_value (float): Control valve input value (0-1)
        """
        self.U_MCext = input_value
        
    def calculate(self) -> None:
        """
        Calculate the CO2 flow at the port.
        The flow is calculated based on the control valve input and external CO2 source capacity.
        
        The calculation follows these steps:
        1. Use U_ExtCO2 if no U_MCext is connected
        2. Calculate MC_flow by converting from g/(m2.h) to mg/(m2.s)
        3. Apply the negative MC_flow to the connected port
        """
        # Use default value if no input is connected
        if self.U_MCext is None:
            self.U_MCext = self.U_ExtCO2
            
        # Calculate MC_flow: convert from g/(m2.h) to mg/(m2.s)
        self.MC_flow = self.U_MCext * self.phi_ExtCO2 / 3600 * 1000
        
        # Set the port flow (negative sign indicates flow into connected component)
        if self.port is not None:
            self.port.MC_flow = -self.MC_flow
            
    def __str__(self) -> str:
        """String representation of the PrescribedCO2Flow model"""
        return (f"PrescribedCO2Flow\n"
                f"phi_ExtCO2 = {self.phi_ExtCO2:.2f} g/(m2.h)\n"
                f"U_ExtCO2 = {self.U_ExtCO2:.2f}\n"
                f"MC_flow = {self.MC_flow:.2f} mg/(m2.s)\n"
                f"U_MCext = {self.U_MCext if self.U_MCext is not None else 'Not connected'}")
