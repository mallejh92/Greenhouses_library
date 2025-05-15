import numpy as np
from typing import Optional
from HeatAndVapourTransfer.VentilationRates.NaturalVentilationRate_1 import NaturalVentilationRate_1

class FreeVentilation:
    """
    Heat exchange by ventilation
    
    This model calculates heat exchange by ventilation between inside and outside air
    based on window openings, wind speed, and air properties.
    """
    
    def __init__(self, 
                 A: float,
                 phi: float = 25/180*np.pi,
                 fr_window: float = 0.078,
                 l: float = 0.0,
                 h: float = 0.0,
                 f_leakage: float = 1.5e-4,
                 thermalScreen: bool = False,
                 topAir: bool = False):
        """
        Initialize free ventilation model
        
        Parameters:
            A (float): Floor surface area [m2]
            phi (float): Inclination of the roof [rad] (0 if horizontal, 25 for typical cover)
            fr_window (float): Number of windows per m2 greenhouse
            l (float): Length of the window [m]
            h (float): Width of the window [m]
            f_leakage (float): Greenhouse leakage coefficient
            thermalScreen (bool): Presence of a thermal screen in the greenhouse
            topAir (bool): False for: Main air zone; True for: Top air zone
        """
        # Parameters
        self.A = A
        self.phi = phi
        self.fr_window = fr_window
        self.l = l
        self.h = h
        self.f_leakage = f_leakage
        self.thermalScreen = thermalScreen
        self.topAir = topAir
        
        # Constants
        self.rho_air = 1.2  # Air density [kg/m3]
        self.c_p_air = 1005.0  # Specific heat capacity of air [J/(kg.K)]
        
        # State variables
        self.theta_l = 0.0  # Window opening at the leeside side [rad]
        self.theta_w = 0.0  # Window opening at the windward side [rad]
        self.u = 0.0  # Wind speed [m/s]
        self.HEC_ab = 0.0  # Heat exchange coefficient [W/(m2.K)]
        self.f_vent = 0.0  # Ventilation rate [m3/(m2.s)]
        self.Q_flow = 0.0  # Heat flow rate [W]
        
        # Create air exchange rate model
        self.airExchangeRate = NaturalVentilationRate_1(
            phi=phi,
            fr_window=fr_window,
            l=l,
            h=h,
            thermalScreen=thermalScreen
        )
        
    def update(self, 
              theta_l: float,
              theta_w: float,
              u: float,
              T_a: float,
              T_b: float) -> float:
        """
        Update free ventilation model state
        
        Parameters:
            theta_l (float): Window opening at the leeside side [rad]
            theta_w (float): Window opening at the windward side [rad]
            u (float): Wind speed [m/s]
            T_a (float): Temperature at port a [K]
            T_b (float): Temperature at port b [K]
            
        Returns:
            float: Heat flow rate [W]
        """
        # Update state variables
        self.theta_l = theta_l
        self.theta_w = theta_w
        self.u = u
        
        # Calculate temperature difference
        dT = T_b - T_a
        
        # Update air exchange rate
        self.airExchangeRate.update(
            u=u,
            theta_l=theta_l,
            theta_w=theta_w,
            dT=dT
        )
        
        # Calculate ventilation rate based on air zone
        if not self.topAir:
            self.f_vent = self.airExchangeRate.f_vent_air
        else:
            self.f_vent = self.airExchangeRate.f_vent_top
            
        # Calculate heat exchange coefficient
        if self.thermalScreen:
            if self.topAir:
                self.HEC_ab = self.rho_air * self.c_p_air * (self.f_vent + max(0.25, u) * self.f_leakage)
            else:
                self.HEC_ab = 0.0
        else:
            self.HEC_ab = self.rho_air * self.c_p_air * (self.f_vent + max(0.25, u) * self.f_leakage)
            
        # Calculate heat flow
        self.Q_flow = self.A * self.HEC_ab * dT
        
        return self.Q_flow
