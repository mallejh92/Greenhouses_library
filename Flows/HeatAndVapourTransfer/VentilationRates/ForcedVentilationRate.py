class ForcedVentilationRate:
    """
    Air exchange rate due to a forced ventilation system
    """
    
    def __init__(self, A: float, phi_VentForced: float):
        """
        Initialize forced ventilation rate calculator
        
        Parameters:
            A (float): Greenhouse floor surface [m2]
            phi_VentForced (float): Air flow capacity of the forced ventilation system [m3/s]
        """
        # Parameters
        self.A = A
        self.phi_VentForced = phi_VentForced
        
        # Input variable
        self.U_VentForced = 0.0  # Control of the forced ventilation
        
        # Output variable
        self.f_ventForced = 0.0  # Air exchange rate at the main air compartment [m3/(m2.s)]
        
    def update(self, U_VentForced: float = None) -> float:
        """
        Update forced ventilation rate
        
        Parameters:
            U_VentForced (float, optional): Control of the forced ventilation
            
        Returns:
            float: Updated air exchange rate [m3/(m2.s)]
        """
        # Update input variable if provided
        if U_VentForced is not None:
            self.U_VentForced = U_VentForced
            
        # Calculate forced ventilation rate
        self.f_ventForced = self.U_VentForced * self.phi_VentForced / self.A
        
        return self.f_ventForced
