import numpy as np

class OutsideAirConvection:
    """
    Cover heat exchange by convection with outside air function of wind speed
    
    This class implements the heat transfer model for convection between the cover
    and outside air in a greenhouse system.
    """
    
    def __init__(self, A, phi):
        """
        Initialize the OutsideAirConvection model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        phi : float
            Inclination of the surface [rad] (0 if horizontal, 25 for typical cover)
        """
        self.A = A
        self.phi = phi
        
        # Constants
        self.s = 11  # Slope of the differentiable switch function
        
        # State variables
        self.u = 0  # Wind speed [m/s]
        
    def calculate_heat_transfer(self, T_a, T_b):
        """
        Calculate heat transfer by outside air convection
        
        Parameters:
        -----------
        T_a : float
            Temperature at port a [K]
        T_b : float
            Temperature at port b [K]
            
        Returns:
        --------
        Q_flow : float
            Heat flow rate [W]
        """
        # Calculate temperature difference
        dT = T_b - T_a
        
        # Calculate wind speed difference from threshold
        du = 4 - self.u
        
        # Calculate convection coefficients using differentiable switch function
        alpha_a = 1/(1 + np.exp(-self.s * du)) * (2.8 + 1.2 * self.u)  # Used for du>0, i.e. u<4
        alpha_b = 1/(1 + np.exp(self.s * du)) * 2.5 * self.u**0.8  # Used for du<0, i.e. u>4
        alpha = alpha_a + alpha_b
        
        # Calculate heat exchange coefficient
        HEC_ab = alpha / np.cos(self.phi)
        
        # Calculate heat flow
        Q_flow = self.A * HEC_ab * dT
        
        return Q_flow
