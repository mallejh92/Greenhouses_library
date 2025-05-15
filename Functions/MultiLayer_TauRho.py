class MultiLayer_TauRho:
    """
    Class for calculating transmission and reflection coefficient of a double layer
    """
    
    def calculate(self, tau_1: float, tau_2: float, rho_1: float, rho_2: float) -> tuple[float, float]:
        """
        Calculate transmission and reflection coefficient of a double layer
        
        Parameters:
            tau_1 (float): Transmission coefficient of first layer
            tau_2 (float): Transmission coefficient of second layer
            rho_1 (float): Reflection coefficient of first layer
            rho_2 (float): Reflection coefficient of second layer
            
        Returns:
            tuple[float, float]: 
                - tau_12: Combined transmission coefficient
                - rho_12: Combined reflection coefficient
        """
        tau_12 = tau_1 * tau_2 / (1 - rho_1 * rho_2)
        rho_12 = rho_1 + tau_1**2 * rho_2 / (1 - rho_1 * rho_2)
        
        return tau_12, rho_12
