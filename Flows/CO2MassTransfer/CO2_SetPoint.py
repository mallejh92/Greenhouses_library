import numpy as np

class CO2_SetPoint:
    """
    The CO2 setpoint depends on the global radiation and the aperture of the ventilation openings
    """
    
    def __init__(self, I_g_max: float = 500.0, U_vents_max: float = 0.1,
                 CO2_Air_ExtMax: float = 850.0, CO2_Air_ExtMin: float = 365.0):
        """
        Initialize CO2 setpoint calculator
        
        Parameters:
            I_g_max (float): Outdoor global radiation at which the maximum CO2 concentration set-point could be reached [W/m2]
            U_vents_max (float): Window aperture at which the minimum CO2 concentration set-point could be reached
            CO2_Air_ExtMax (float): Maximum CO2 concentration set-point [umol/mol]
            CO2_Air_ExtMin (float): Minimum CO2 concentration set-point [umol/mol]
        """
        # Parameters
        self.I_g_max = I_g_max
        self.U_vents_max = U_vents_max
        self.CO2_Air_ExtMax = CO2_Air_ExtMax
        self.CO2_Air_ExtMin = CO2_Air_ExtMin
        
        # Input variables
        self.U_vents = 0.0  # Window aperture
        self.I_g = 300.0  # Outdoor global radiation [W/m2]
        
        # Intermediate variables
        self.f_Ig = 0.0  # Radiation factor
        self.g_Uv = 0.0  # Ventilation factor
        self.CO2_Air_ExtOn = 0.0  # CO2 setpoint [umol/mol]
        
        # Output
        self.y = 0.0  # CO2 setpoint [mg/m3]
        
    def update(self, U_vents: float, I_g: float) -> float:
        """
        Update CO2 setpoint
        
        Parameters:
            U_vents (float): Window aperture
            I_g (float): Outdoor global radiation [W/m2]
            
        Returns:
            float: CO2 setpoint [mg/m3]
        """
        # Update input variables
        self.U_vents = U_vents
        self.I_g = I_g
        
        # Calculate radiation factor
        self.f_Ig = min(1.0, self.I_g / self.I_g_max)
        
        # Calculate ventilation factor
        self.g_Uv = (1.0 / (1.0 + np.exp(100 * (self.U_vents - self.U_vents_max)))) * (1.0 - self.U_vents / self.U_vents_max)
        
        # Calculate CO2 setpoint in umol/mol
        self.CO2_Air_ExtOn = (self.f_Ig * self.g_Uv * (self.CO2_Air_ExtMax - self.CO2_Air_ExtMin) + 
                             self.CO2_Air_ExtMin)
        
        # Convert to mg/m3 (1 umol/mol = 1.94 mg/m3)
        self.y = self.CO2_Air_ExtOn * 1.94
        
        return self.y
