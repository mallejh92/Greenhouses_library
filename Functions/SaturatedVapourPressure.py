import numpy as np

class SaturatedVapourPressure:
    """
    Class for calculating saturated vapour pressure at any temperature
    """
    
    def calculate(self, TSat: float) -> float:
        """
        Calculate saturated vapour pressure at any temperature
        
        Parameters:
            TSat (float): Saturation temperature [°C]
            
        Returns:
            float: Saturation pressure [Pa]
        """
        pSat = -274.36 + 877.52 * np.exp(0.0545 * TSat)
        return pSat
