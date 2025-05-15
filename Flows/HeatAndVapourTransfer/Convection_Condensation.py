import numpy as np

class Convection_Condensation:
    """
    Upward or downward heat exchange by free convection from an horizontal or inclined surface.
    Mass transfer by condensation from the air (filled port) to the cover/screen (empty port).
    If studying heat exchange of Air-Floor: connect the filled port to the floor and the unfilled port to the air.
    """
    
    def __init__(self, phi: float, A: float, floor: bool = False, 
                 thermalScreen: bool = False, Air_Cov: bool = True, topAir: bool = False):
        """
        Initialize convection and condensation model
        
        Parameters:
            phi (float): Inclination of the surface (0 if horizontal, 25 for typical cover) [rad]
            A (float): Floor surface [m2]
            floor (bool): True if floor, false if cover or thermal screen heat flux
            thermalScreen (bool): Presence of a thermal screen in the greenhouse
            Air_Cov (bool): True if heat exchange air-cover, False if heat exchange air-screen
            topAir (bool): False if MainAir-Cov; True for: TopAir-Cov
        """
        # Parameters
        self.phi = phi
        self.A = A
        self.floor = floor
        self.thermalScreen = thermalScreen
        self.Air_Cov = Air_Cov
        self.topAir = topAir
        
        # Constants
        self.s = 11.0  # Slope of the differentiable switch function for vapour pressure differences
        
        # Input variables
        self.SC = 0.0  # Screen closure 1:closed, 0:open
        
        # State variables
        self.HEC_ab = 0.0  # Heat exchange coefficient [W/(m2.K)]
        self.VEC_ab = 0.0  # Mass transfer coefficient [kg/(s.Pa.m2)]
        self.HEC_up_flr = 0.0  # Upward heat exchange coefficient [W/(m2.K)]
        self.HEC_down_flr = 0.0  # Downward heat exchange coefficient [W/(m2.K)]
        self.Q_flow = 0.0  # Heat flow rate [W]
        self.MV_flow = 0.0  # Mass flow rate [kg/s]
        
    def update(self, SC: float, T_a: float, T_b: float, VP_a: float, VP_b: float) -> tuple:
        """
        Update heat and mass flux exchange
        
        Parameters:
            SC (float): Screen closure (1:closed, 0:open)
            T_a (float): Temperature at port a [K]
            T_b (float): Temperature at port b [K]
            VP_a (float): Vapor pressure at port a [Pa]
            VP_b (float): Vapor pressure at port b [Pa]
            
        Returns:
            tuple: (Q_flow, MV_flow) Heat and mass flow rates [W, kg/s]
        """
        # Update input variable
        self.SC = SC
        
        # Calculate temperature difference
        dT = T_a - T_b
        
        # Calculate heat exchange coefficient based on conditions
        if not self.floor:
            if self.thermalScreen:
                if self.Air_Cov:
                    if not self.topAir:
                        # Exchange main air-cover (with screen)
                        self.HEC_ab = (1 - self.SC) * 1.7 * max(1e-9, abs(dT))**0.33 * (np.cos(self.phi))**(-0.66)
                    else:
                        # Exchange top air-cover
                        self.HEC_ab = self.SC * 1.7 * max(1e-9, abs(dT))**0.33 * (np.cos(self.phi))**(-0.66)
                else:
                    # Exchange air-screen
                    self.HEC_ab = self.SC * 1.7 * max(1e-9, abs(dT))**0.33
            else:
                # Exchange main air-cover (no screen)
                self.HEC_ab = 1.7 * max(1e-9, abs(dT))**0.33 * (np.cos(self.phi))**(-0.66)
            self.HEC_up_flr = 0.0  # dummy
            self.HEC_down_flr = 0.0
        else:
            # Calculate heat exchange coefficients using differentiable switch function
            self.HEC_up_flr = 1/(1 + np.exp(-self.s * dT)) * 1.7 * abs(dT)**0.33  # Used for dT>0
            self.HEC_down_flr = 1/(1 + np.exp(self.s * dT)) * 1.3 * abs(dT)**0.25  # Used for dT<0
            self.HEC_ab = self.HEC_up_flr + self.HEC_down_flr
            
        # Calculate heat flow
        self.Q_flow = self.A * self.HEC_ab * dT
        
        # Calculate mass transfer coefficient and mass flow
        self.VEC_ab = max(0, 6.4e-9 * self.HEC_ab)
        self.MV_flow = max(0, self.A * self.VEC_ab * (VP_a - VP_b))  # Condensation fluxes are prohibited from being negative
        
        return self.Q_flow, self.MV_flow
