import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.Element1D import Element1D

class FreeConvection(Element1D):
    """
    Upward or downward heat exchange by free convection from an horizontal or inclined surface.
    If studying heat exchange of Air-Floor: connect the filled port to the floor 
    and the unfilled port to the air.
    """
    
    def __init__(self, phi, A, floor=False, thermalScreen=False, Air_Cov=True, topAir=False):
        """
        Initialize the FreeConvection model
        
        Parameters:
        -----------
        phi : float
            Inclination of the surface (0 if horizontal, 25 for typical cover) [rad]
        A : float
            Floor surface area [m²]
        floor : bool, optional
            True if floor, false if cover or thermal screen heat flux, default is False
        thermalScreen : bool, optional
            Presence of a thermal screen in the greenhouse, default is False
        Air_Cov : bool, optional
            True if heat exchange air-cover, False if heat exchange air-screen, default is True
        topAir : bool, optional
            False if MainAir-Cov; True for: TopAir-Cov, default is False
        """
        super().__init__()
        self.phi = phi
        self.A = A
        self.floor = floor
        self.thermalScreen = thermalScreen
        self.Air_Cov = Air_Cov
        self.topAir = topAir
        
        # State variables
        self.SC = 0  # Screen closure (1:closed, 0:open)
        self.s = 11  # Slope of the differentiable switch function
        
        # Heat exchange coefficients
        self.HEC_ab = 0.0
        self.HEC_up_flr = 0.0
        self.HEC_down_flr = 0.0
        
    def step(self, dt):
        """
        Calculate heat transfer by free convection
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        # Calculate heat exchange coefficient based on conditions
        if not self.floor:
            if self.thermalScreen:
                if self.Air_Cov:
                    if not self.topAir:
                        # Exchange main air-cover (with screen)
                        self.HEC_ab = 0
                    else:
                        # Exchange top air-cover
                        self.HEC_ab = 1.7 * max(1e-9, abs(self.dT))**0.33 * (np.cos(self.phi))**(-0.66)
                else:
                    # Exchange air-screen
                    self.HEC_ab = self.SC * 1.7 * max(1e-9, abs(self.dT))**0.33
            else:
                # Exchange main air-cover (no screen)
                self.HEC_ab = 1.7 * max(1e-9, abs(self.dT))**0.33 * (np.cos(self.phi))**(-0.66)
            
            self.HEC_up_flr = 0
            self.HEC_down_flr = 0
            
        else:
            # Floor heat exchange with differentiable switch function
            self.HEC_up_flr = 1/(1 + np.exp(-self.s * self.dT)) * 1.7 * abs(self.dT)**0.33  # Used for dT>0
            self.HEC_down_flr = 1/(1 + np.exp(self.s * self.dT)) * 1.3 * abs(self.dT)**0.25  # Used for dT<0
            self.HEC_ab = self.HEC_up_flr + self.HEC_down_flr
        
        # Calculate heat flow
        self.Q_flow = self.A * self.HEC_ab * self.dT
