import numpy as np
from HeatAndVapourTransfer.VentilationRates.NaturalVentilationRate_1 import NaturalVentilationRate_1

class FreeVentilation:
    """
    Heat exchange by ventilation
    
    This class implements the heat transfer model for ventilation in a greenhouse system.
    """
    
    def __init__(self, A, phi=np.radians(25), fr_window=0.078, l=0, h=0, 
                 f_leakage=1.5e-4, thermalScreen=False, topAir=False):
        """
        Initialize the FreeVentilation model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        phi : float, optional
            Inclination of the roof [rad], default is 25 degrees
        fr_window : float, optional
            Number of windows per m² greenhouse, default is 0.078
        l : float, optional
            Length of the window [m]
        h : float, optional
            Width of the window [m]
        f_leakage : float, optional
            Greenhouse leakage coefficient, default is 1.5e-4
        thermalScreen : bool, optional
            Presence of a thermal screen in the greenhouse, default is False
        topAir : bool, optional
            False for: Main air zone; True for: Top air zone, default is False
        """
        self.A = A
        self.phi = phi
        self.fr_window = fr_window
        self.l = l
        self.h = h
        self.f_leakage = f_leakage
        self.thermalScreen = thermalScreen
        self.topAir = topAir
        
        # Constants
        self.rho_air = 1.2  # Air density [kg/m³]
        self.c_p_air = 1005  # Specific heat capacity of air [J/(kg·K)]
        
        # State variables
        self.theta_l = 0  # Window opening at the leeside side [rad]
        self.theta_w = 0  # Window opening at the windward side [rad]
        self.u = 0  # Wind speed [m/s]
        
        # Initialize ventilation rate calculator
        self.airExchangeRate = NaturalVentilationRate_1(
            phi=phi,
            fr_window=fr_window,
            l=l,
            h=h,
            thermalScreen=thermalScreen
        )
        
    def calculate_heat_transfer(self, T_a, T_b):
        """
        Calculate heat transfer by ventilation
        
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
        
        # Update ventilation rate calculator
        self.airExchangeRate.update(u=self.u, theta_l=self.theta_l, theta_w=self.theta_w, dT=dT)
        
        # Calculate ventilation rate
        if not self.topAir:
            f_vent = self.airExchangeRate.f_vent_air
        else:
            f_vent = self.airExchangeRate.f_vent_top
            
        # Calculate heat exchange coefficient
        if self.thermalScreen:
            if self.topAir:
                HEC_ab = self.rho_air * self.c_p_air * (f_vent + max(0.25, self.u) * self.f_leakage)
            else:
                HEC_ab = 0
        else:
            HEC_ab = self.rho_air * self.c_p_air * (f_vent + max(0.25, self.u) * self.f_leakage)
            
        # Calculate heat flow
        Q_flow = self.A * HEC_ab * dT
        
        return Q_flow
