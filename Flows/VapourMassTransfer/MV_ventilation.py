from Interfaces.Vapour.Element1D import Element1D
from HeatAndVapourTransfer.VentilationRates.NaturalVentilationRate_1 import NaturalVentilationRate_1

class MV_ventilation(Element1D):
    """
    Vapour mass flow exchanged from the greenhouse air to the outside air by ventilation
    
    This is a Python implementation of Greenhouses.Flows.VapourMassTransfer.MV_ventilation
    """
    
    def __init__(self, A=1.0, phi=25/180*3.14159, fr_window=0.078, l=1.0, h=1.0, 
                 thermalScreen=False, topAir=False):
        """
        Initialize the MV_ventilation model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        phi : float
            Inclination of the roof [rad] (0 if horizontal, 25° for typical cover)
        fr_window : float
            Number of windows per m² greenhouse
        l : float
            Length of the window [m]
        h : float
            Width of the window [m]
        thermalScreen : bool
            Presence of a thermal screen in the greenhouse
        topAir : bool
            False for: Main air zone; True for: Top air zone
        """
        super().__init__()
        
        # Parameters
        self.A = A
        self.phi = phi
        self.fr_window = fr_window
        self.l = l
        self.h = h
        self.thermalScreen = thermalScreen
        self.topAir = topAir
        
        # Varying inputs
        self.theta_l = 0.0  # Window opening at the leeside side
        self.theta_w = 0.0  # Window opening at the windward side
        self.T_a = 300.0    # Temperature at port a (filled square)
        self.T_b = 300.0    # Temperature at port b (empty square)
        self.u = 0.0        # Wind speed
        
        # Constants
        self.R = 8314       # Gas constant
        self.M_H = 18       # Molar mass of water [kg/kmol]
        
        # Variables
        self.f_vent = 0.0   # Ventilation rate
        
        # Initialize ventilation rate calculator
        self.airExchangeRate = NaturalVentilationRate_1(
            phi=phi,
            fr_window=fr_window,
            l=l,
            h=h,
            thermalScreen=thermalScreen
        )
        
        # Modelica-style mass port names
        if not hasattr(self, 'massPort_a'):
            self.massPort_a = type('MassPort', (), {'VP': 0.0, 'P': 1e5})()
        if not hasattr(self, 'massPort_b'):
            self.massPort_b = type('MassPort', (), {'VP': 0.0, 'P': 1e5})()
        
    def step(self, dt=None):
        """
        Calculate the mass exchange rate
        
        Parameters:
        -----------
        dt : float, optional
            Time step [s]. Not used in calculations but included for compatibility.
            
        Returns:
        --------
        MV_flow : float
            Mass flow rate [kg/s]
        """
        # Update ventilation rate calculator
        self.airExchangeRate.update(
            u=self.u,
            theta_l=self.theta_l,
            theta_w=self.theta_w,
            dT=self.T_a - self.T_b
        )
        
        # Calculate mass exchange (Modelica equations)
        if not self.topAir:
            self.f_vent = self.airExchangeRate.f_vent_air
            # Modelica: MV_flow = A*M_H*f_vent/R*(port_a.VP/T_a - port_b.VP/T_b)
            self.MV_flow = self.A * self.M_H * self.f_vent / self.R * (
                self.massPort_a.VP / self.T_a - self.massPort_b.VP / self.T_b
            )
        else:
            self.f_vent = self.airExchangeRate.f_vent_top
            # Calculate pressure difference (Modelica: dP = port_a.VP - port_b.VP)
            self.dP = self.massPort_a.VP - self.massPort_b.VP
            # Modelica: MV_flow = A*M_H*f_vent/R/283*dP
            self.MV_flow = self.A * self.M_H * self.f_vent / self.R / 283 * self.dP
            
        # Update parent class
        super().update()
        
        return self.MV_flow
