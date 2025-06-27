from Interfaces.CO2.CO2Port_a import CO2Port_a

class MC_AirCan:
    """
    Greenhouse CO2 net assimilation rate by the canopy.
    The value computed in a yield model is used as input.
    
    Modelica 원본과 정확히 일치:
    - port.MC_flow = MC_AirCan
    - MC_AirCan이 양수일 때 작물이 CO2를 흡수 (공기에서 작물로 이동)
    """
    
    def __init__(self, MC_AirCan: float = 3.0):
        """
        Initialize CO2 net assimilation rate model
        
        Parameters:
            MC_AirCan (float): CO2 flux between the greenhouse air and the canopy [mg/(m2.s)]
                              양수일 때 작물이 CO2를 흡수 (공기에서 작물로 이동)
        """
        # Input variable
        self.MC_AirCan = MC_AirCan  # CO2 flux between the greenhouse air and the canopy [mg/(m2.s)]
        
        # Port variable
        self.port = CO2Port_a()     # Modelica 구조와 동일하게 CO2Port_a 사용
        
    def step(self, MC_AirCan: float = None) -> float:
        """
        Update CO2 net assimilation rate and synchronize port
        
        Parameters:
            MC_AirCan (float, optional): New CO2 flux value [mg/(m2.s)]. If None, uses current value.
            
        Returns:
            float: Updated CO2 mass flow rate at the port [mg/(m2.s)]
        """
        # Update input if provided
        if MC_AirCan is not None:
            self.MC_AirCan = MC_AirCan
            
        # Modelica 원본 방정식: port.MC_flow = MC_AirCan
        # MC_AirCan이 양수일 때 작물이 CO2를 흡수 (공기에서 작물로 이동)
        self.port.MC_flow = self.MC_AirCan
        
        return self.port.MC_flow
