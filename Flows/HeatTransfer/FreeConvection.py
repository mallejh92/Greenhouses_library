import numpy as np

class FreeConvection:
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
        self.phi = phi
        self.A = A
        self.floor = floor
        self.thermalScreen = thermalScreen
        self.Air_Cov = Air_Cov
        self.topAir = topAir
        
        # State variables
        self.SC = 0  # Screen closure (1:closed, 0:open)
        self.s = 11  # Slope of the differentiable switch function
        
    def calculate_heat_transfer(self, T_a, T_b):
        """
        Calculate heat transfer by free convection
        
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
        
        # Calculate heat exchange coefficient based on conditions
        if not self.floor:
            if self.thermalScreen:
                if self.Air_Cov:
                    if not self.topAir:
                        # Exchange main air-cover (with screen)
                        HEC_ab = 0
                    else:
                        # Exchange top air-cover
                        HEC_ab = 1.7 * max(1e-9, abs(dT))**0.33 * (np.cos(self.phi))**(-0.66)
                else:
                    # Exchange air-screen
                    HEC_ab = self.SC * 1.7 * max(1e-9, abs(dT))**0.33
            else:
                # Exchange main air-cover (no screen)
                HEC_ab = 1.7 * max(1e-9, abs(dT))**0.33 * (np.cos(self.phi))**(-0.66)
            
            HEC_up_flr = 0
            HEC_down_flr = 0
            
        else:
            # Floor heat exchange with differentiable switch function
            HEC_up_flr = 1/(1 + np.exp(-self.s * dT)) * 1.7 * abs(dT)**0.33  # Used for dT>0
            HEC_down_flr = 1/(1 + np.exp(self.s * dT)) * 1.3 * abs(dT)**0.25  # Used for dT<0
            HEC_ab = HEC_up_flr + HEC_down_flr
        
        # Calculate heat flow
        Q_flow = self.A * HEC_ab * dT
        
        return Q_flow
