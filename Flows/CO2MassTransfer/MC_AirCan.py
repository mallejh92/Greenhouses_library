class MC_AirCan:
    """
    Greenhouse CO2 net assimilation rate by the canopy.
    The value computed in a yield model is used as input.
    """
    
    def __init__(self, MC_AirCan: float = 3.0):
        """
        Initialize CO2 net assimilation rate model
        
        Parameters:
            MC_AirCan (float): CO2 flux between the greenhouse air and the canopy [mg/(m2.s)]
        """
        # Input variable
        self.MC_AirCan = MC_AirCan  # CO2 flux between the greenhouse air and the canopy [mg/(m2.s)]
        
        # Port variable
        self.port_MC_flow = MC_AirCan  # CO2 mass flow rate at the port [mg/(m2.s)]
        
    def step(self, MC_AirCan: float = None) -> float:
        """
        Update CO2 net assimilation rate
        
        Parameters:
            MC_AirCan (float, optional): New CO2 flux value [mg/(m2.s)]. If None, uses current value.
            
        Returns:
            float: Updated CO2 mass flow rate at the port [mg/(m2.s)]
        """
        # Update input if provided
        if MC_AirCan is not None:
            self.MC_AirCan = MC_AirCan
            
        # Update port flow rate
        self.port_MC_flow = self.MC_AirCan
        
        return self.port_MC_flow
