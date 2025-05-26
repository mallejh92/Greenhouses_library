class MC_ventilation2:
    """
    CO2 mass flow accompanying an air flow caused by ventilation processes
    """
    
    def __init__(self, f_vent=0.0):
        """
        Initialize ventilation CO2 mass flow model
        
        Parameters:
            f_vent (float): Air exchange rate [m3/(m2.s)], default is 0.0
        """
        # Input variable
        self.f_vent = f_vent  # Air exchange rate [m3/(m2.s)]
        
        # State variables
        self.MC_flow = 0.0  # CO2 mass flow rate [mg/(m2.s)]
        self.dC = 0.0  # CO2 concentration difference [mg/m3]
        
    def update(self, f_vent: float = None, dC: float = None) -> float:
        """
        Update CO2 mass flow
        
        Parameters:
            f_vent (float, optional): Air exchange rate [m3/(m2.s)]
            dC (float, optional): CO2 concentration difference [mg/m3]
            
        Returns:
            float: Updated CO2 mass flow rate [mg/(m2.s)]
        """
        # Update input variables if provided
        if f_vent is not None:
            self.f_vent = f_vent
        if dC is not None:
            self.dC = dC
            
        # Calculate CO2 mass flow
        self.MC_flow = self.f_vent * self.dC
        
        return self.MC_flow
