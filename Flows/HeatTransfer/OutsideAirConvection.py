import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.Element1D import Element1D

class OutsideAirConvection(Element1D):
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
        super().__init__()
        self.A = A
        self.phi = phi
        
        # Constants
        self.s = 11  # Slope of the differentiable switch function
        
        # State variables
        self.u = 0  # Wind speed [m/s]
        
        # Heat transfer coefficients
        self.HEC_ab = 0.0
        self.alpha = 0.0
        self.alpha_a = 0.0
        self.alpha_b = 0.0
        self.du = 0.0
        
    def step(self, dt):
        """
        Calculate heat transfer by outside air convection
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        # Calculate temperature difference
        self.dT = self.port_b.T - self.port_a.T
        
        # Calculate wind speed difference from threshold
        self.du = 4 - self.u
        
        # Calculate convection coefficients using differentiable switch function
        self.alpha_a = 1/(1 + np.exp(-self.s * self.du)) * (2.8 + 1.2 * self.u)  # Used for du>0, i.e. u<4
        self.alpha_b = 1/(1 + np.exp(self.s * self.du)) * 2.5 * self.u**0.8  # Used for du<0, i.e. u>4
        self.alpha = self.alpha_a + self.alpha_b
        
        # Calculate heat exchange coefficient
        self.HEC_ab = self.alpha / np.cos(self.phi)
        
        # Calculate heat flow
        self.Q_flow = self.A * self.HEC_ab * self.dT
