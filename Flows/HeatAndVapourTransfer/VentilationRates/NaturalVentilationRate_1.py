import numpy as np

class NaturalVentilationRate_1:
    """
    Air exchange rate from the greenhouse air to the outside air function of wind and temperature
    by De Jong (1990)
    """
    
    def __init__(self, phi: float = 25/180*np.pi, fr_window: float = 0.078,
                 l: float = 1.0, h: float = 1.0, thermalScreen: bool = False):
        """
        Initialize natural ventilation rate calculator
        
        Parameters:
            phi (float): Inclination of the roof (0 if horizontal, 25 for typical cover) [rad]
            fr_window (float): Number of windows per m2 greenhouse
            l (float): Length of the window [m]
            h (float): Width of the window [m]
            thermalScreen (bool): Presence of a thermal screen in the greenhouse
        """
        # Parameters
        self.phi = phi
        self.fr_window = fr_window
        self.l = l
        self.h = h
        self.thermalScreen = thermalScreen
        
        # Input variables
        self.u = 0.0  # Wind speed [m/s]
        self.theta_l = 0.0  # Window opening at the leeside side [rad]
        self.theta_w = 0.0  # Window opening at the windward side [rad]
        self.dT = 10.0  # Temperature difference [K]
        
        # State variables
        self.f_vent = 0.0  # Total ventilation rate [m3/(m2.s)]
        self.f_vent_wind = 0.0  # Wind-driven ventilation rate [m3/(m2.s)]
        self.f_vent_temp = 0.0  # Temperature-driven ventilation rate [m3/(m2.s)]
        self.C_f = 0.6  # Constant of discharge of energy caused by friction in the window opening
        self.beta = 1/283  # Thermal expansion coefficient [1/K]
        self.f_vent_top = 0.0  # Air exchange rate at the top air compartment [m3/(m2.s)]
        self.f_vent_air = 0.0  # Air exchange rate at the main air compartment [m3/(m2.s)]
        
    def update(self, u: float = None, theta_l: float = None, 
              theta_w: float = None, dT: float = None) -> tuple:
        """
        Update ventilation rates
        
        Parameters:
            u (float, optional): Wind speed [m/s]
            theta_l (float, optional): Window opening at the leeside side [rad]
            theta_w (float, optional): Window opening at the windward side [rad]
            dT (float, optional): Temperature difference [K]
            
        Returns:
            tuple: (f_vent_top, f_vent_air) Air exchange rates [m3/(m2.s)]
        """
        # Update input variables if provided
        if u is not None:
            self.u = u
        if theta_l is not None:
            self.theta_l = theta_l
        if theta_w is not None:
            self.theta_w = theta_w
        if dT is not None:
            self.dT = dT
            
        # Calculate temperature-driven ventilation
        g_n = 9.81  # Gravitational acceleration [m/s2]
        self.f_vent_temp = (self.C_f * self.l/3 * np.sqrt(abs(g_n * self.beta * self.dT)) * 
                          (self.h * (np.sin(self.phi) - np.sin(self.phi - self.theta_l)))**1.5 +
                          self.C_f * self.l/3 * np.sqrt(abs(g_n * self.beta * self.dT)) * 
                          (self.h * (np.sin(self.phi) - np.sin(self.phi - self.theta_w)))**1.5)
        
        # Calculate wind-driven ventilation
        self.f_vent_wind = ((2.29e-2 * (1 - np.exp(-self.theta_l/21.1)) + 
                           1.2e-3 * self.theta_w * np.exp(self.theta_w/211)) * 
                          self.l * self.h * self.u)
        
        # Calculate total ventilation rate
        self.f_vent = 0.5 * self.fr_window * np.sqrt(self.f_vent_wind**2 + self.f_vent_temp**2)
        
        # Calculate final ventilation rates based on thermal screen presence
        if self.thermalScreen:
            self.f_vent_top = self.f_vent
            self.f_vent_air = 0.0
        else:
            self.f_vent_top = 0.0
            self.f_vent_air = self.f_vent
            
        return self.f_vent_top, self.f_vent_air

