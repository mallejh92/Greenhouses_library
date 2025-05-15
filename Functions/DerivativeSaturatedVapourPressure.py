import numpy as np

class DerivativeSaturatedVapourPressure:
    """
    Class for calculating the slope of the tangent at the saturated vapour pressure at any temperature
    """
    
    def calculate(self, TSat: float) -> float:
        """
        Calculate the slope of the tangent at the saturated vapour pressure at any temperature
        
        Parameters:
            TSat (float): Saturation temperature [°C]
            
        Returns:
            float: Slope of saturation pressure [Pa/K]
        """
        dpSat_dT = 47.82 * np.exp(0.0545 * TSat)
        return dpSat_dT
