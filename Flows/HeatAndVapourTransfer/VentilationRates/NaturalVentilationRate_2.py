import numpy as np

class NaturalVentilationRate_2:
    """
    Air exchange rate from the greenhouse air to the outside air function of wind and temperature
    by Boulard and Baille (1995)
    """
    
    def __init__(self, thermalScreen: bool = False, C_d: float = 0.75, C_w: float = 0.09,
                 eta_RfFlr: float = 0.1, h_vent: float = 0.68, c_leakage: float = 1.5e-4):
        """
        Initialize natural ventilation rate calculator
        
        Parameters:
            thermalScreen (bool): Presence of a thermal screen in the greenhouse
            C_d (float): Ventilation discharge coefficient, function of greenhouse shape
            C_w (float): Ventilation global wind pressure coefficient, function of greenhouse shape
            eta_RfFlr (float): Ratio between the maximum roof vent area and the greenhouse floor area A_roof/A_floor
            h_vent (float): Vertical dimension of a single ventilation opening [m]
            c_leakage (float): Greenhouse leakage coefficient
        """
        # Parameters
        self.thermalScreen = thermalScreen
        self.C_d = C_d
        self.C_w = C_w
        self.eta_RfFlr = eta_RfFlr
        self.h_vent = h_vent
        self.c_leakage = c_leakage
        
        # Input variables
        self.SC = 0.0  # Screen closure 1:closed, 0:open
        self.U_roof = 0.0  # Control of the aperture of the roof vents
        self.u = 0.0  # Wind speed [m/s]
        self.dT = 10.0  # T_a-T_b [K]
        self.T_a = 293.15  # Temperature at port a [K]
        self.T_b = 276.15  # Temperature at port b [K]
        
        # State variables
        self.f_vent = 0.0  # Ventilation rate [m3/(m2.s)]
        self.f_leakage = 0.0  # Air exchange rate due to leakage [m3/(m2.s)]
        self.T_mean = 0.0  # Mean temperature [K]
        self.f_vent_top = 0.0  # Air exchange rate at the top air compartment [m3/(m2.s)]
        self.f_vent_air = 0.0  # Air exchange rate at the main air compartment [m3/(m2.s)]
        
    def update(self, SC: float = None, U_roof: float = None, u: float = None,
              dT: float = None, T_a: float = None, T_b: float = None) -> tuple:
        """
        Update ventilation rates
        
        Parameters:
            SC (float, optional): Screen closure (1:closed, 0:open)
            U_roof (float, optional): Control of the aperture of the roof vents
            u (float, optional): Wind speed [m/s]
            dT (float, optional): T_a-T_b [K]
            T_a (float, optional): Temperature at port a [K]
            T_b (float, optional): Temperature at port b [K]
            
        Returns:
            tuple: (f_vent_top, f_vent_air) Air exchange rates [m3/(m2.s)]
        """
        # Update input variables if provided
        if SC is not None:
            self.SC = SC
        if U_roof is not None:
            self.U_roof = U_roof
        if u is not None:
            self.u = u
        if dT is not None:
            self.dT = dT
        if T_a is not None:
            self.T_a = T_a
        if T_b is not None:
            self.T_b = T_b
            
        # Calculate mean temperature
        self.T_mean = (self.T_a + self.T_b) / 2
        
        # Calculate roof ventilation rate
        g_n = 9.81  # Gravitational acceleration [m/s2]
        self.f_vent = (self.U_roof * self.eta_RfFlr * self.C_d / 2 * 
                      np.sqrt(abs(g_n * self.h_vent / 2 * abs(self.dT) / self.T_mean + 
                                self.C_w * self.u**2)))
        
        # Calculate leakage rate
        self.f_leakage = max(0.25, self.u) * self.c_leakage
        
        # Calculate final ventilation rates based on thermal screen presence
        if self.thermalScreen:
            self.f_vent_top = self.SC * self.f_vent + 0.5 * self.f_leakage
            self.f_vent_air = (1 - self.SC) * self.f_vent + 0.5 * self.f_leakage
        else:
            self.f_vent_top = 0.0
            self.f_vent_air = self.f_vent + self.f_leakage
            
        return self.f_vent_top, self.f_vent_air 