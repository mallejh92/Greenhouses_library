import numpy as np
from typing import Optional

class FreeConvection:
    """
    Upward or downward heat exchange by free convection from a horizontal or inclined surface
    
    This model calculates heat exchange by free convection between air and a surface
    (floor, cover, or thermal screen) based on surface inclination and temperature difference.
    """
    
    def __init__(self, 
                 phi: float,
                 A: float,
                 floor: bool = False,
                 thermalScreen: bool = False,
                 Air_Cov: bool = True,
                 topAir: bool = False):
        """
        Initialize free convection model
        
        Parameters:
            phi (float): Inclination of the surface [rad] (0 if horizontal, 25 for typical cover)
            A (float): Floor surface area [m2]
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
        self.s = 11.0  # Slope of the differentiable switch function
        
        # State variables
        self.SC = 0.0  # Screen closure (1: closed, 0: open)
        self.HEC_ab = 0.0  # Heat exchange coefficient [W/(m2.K)]
        self.HEC_up_flr = 0.0  # Upward heat exchange coefficient [W/(m2.K)]
        self.HEC_down_flr = 0.0  # Downward heat exchange coefficient [W/(m2.K)]
        self.Q_flow = 0.0  # Heat flow rate [W]
        
    def update(self, 
              SC: float,
              T_a: float,
              T_b: float) -> float:
        """
        Update free convection model state
        
        Parameters:
            SC (float): Screen closure (1: closed, 0: open)
            T_a (float): Temperature at port a [K]
            T_b (float): Temperature at port b [K]
            
        Returns:
            float: Heat flow rate [W]
        """
        # Update screen closure
        self.SC = SC
        
        # Calculate temperature difference
        dT = T_b - T_a
        
        # Calculate heat exchange coefficient based on conditions
        if not self.floor:
            if self.thermalScreen:
                if self.Air_Cov:
                    if not self.topAir:
                        # Exchange main air-cover (with screen)
                        self.HEC_ab = 0.0
                    else:
                        # Exchange top air-cover
                        self.HEC_ab = 1.7 * max(1e-9, abs(dT))**0.33 * (np.cos(self.phi))**(-0.66)
                else:
                    # Exchange air-screen
                    self.HEC_ab = self.SC * 1.7 * max(1e-9, abs(dT))**0.33
            else:
                # Exchange main air-cover (no screen)
                self.HEC_ab = 1.7 * max(1e-9, abs(dT))**0.33 * (np.cos(self.phi))**(-0.66)
                
            self.HEC_up_flr = 0.0
            self.HEC_down_flr = 0.0
            
        else:
            # Floor heat exchange with differentiable switch function
            self.HEC_up_flr = 1/(1 + np.exp(-self.s * dT)) * 1.7 * abs(dT)**0.33  # Used for dT > 0
            self.HEC_down_flr = 1/(1 + np.exp(self.s * dT)) * 1.3 * abs(dT)**0.25  # Used for dT < 0
            self.HEC_ab = self.HEC_up_flr + self.HEC_down_flr
            
        # Calculate heat flow
        self.Q_flow = self.A * self.HEC_ab * dT
        
        return self.Q_flow
