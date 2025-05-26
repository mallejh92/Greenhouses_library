import numpy as np
from .VentilationRates.NaturalVentilationRate_2 import NaturalVentilationRate_2
from .VentilationRates.ForcedVentilationRate import ForcedVentilationRate
from Interfaces.HeatAndVapour.Element1D import Element1D

class Ventilation(Element1D):
    """
    Heat and vapour mass flows exchanged from the greenhouse air to the outside air by ventilation
    """
    
    def __init__(self, A: float, thermalScreen: bool = False, topAir: bool = False,
                 forcedVentilation: bool = False, phi_VentForced: float = 0.0):
        """
        Initialize ventilation model
        
        Parameters:
            A (float): Greenhouse floor surface [m2]
            thermalScreen (bool): Presence of a thermal screen in the greenhouse
            topAir (bool): False for Main air zone, True for Top air zone
            forcedVentilation (bool): Presence of a mechanical ventilation system
            phi_VentForced (float): Air flow capacity of the forced ventilation system [m3/s]
        """
        super().__init__()
        
        # Parameters
        self.A = A
        self.thermalScreen = thermalScreen
        self.topAir = topAir
        self.forcedVentilation = forcedVentilation
        self.phi_VentForced = phi_VentForced
        
        # Constants
        self.rho_air = 1.2  # Air density [kg/m3]
        self.c_p_air = 1005.0  # Specific heat capacity of air [J/(kg.K)]
        self.R = 8314.0  # Gas constant [J/(kmol.K)]
        self.M_H = 18.0  # Molar mass of water [kg/kmol]
        
        # Input variables
        self.SC = 0.0  # Screen closure 1:closed, 0:open
        self.u = 0.0  # Wind speed [m/s]
        self.U_vents = 0.0  # Control of the aperture of the roof vents (0 to 1)
        self.U_VentForced = 0.0  # Control of the forced ventilation (0 to 1)
        
        # State variables
        self.HEC_ab = 0.0  # Heat exchange coefficient [W/(m2.K)]
        self.f_vent = 0.0  # Natural air exchange rate [m3/(m2.s)]
        self.f_ventForced = 0.0  # Forced air exchange rate [m3/(m2.s)]
        self.f_vent_total = 0.0  # Total air exchange rate [m3/(m2.s)]
        self.Q_flow = 0.0  # Heat flow rate [W]
        self.MV_flow = 0.0  # Mass flow rate [kg/s]
        
        # Create ventilation rate models
        self.natural_vent = NaturalVentilationRate_2(
            thermalScreen=self.thermalScreen
        )
        self.forced_vent = ForcedVentilationRate(
            A=self.A,
            phi_VentForced=self.phi_VentForced
        )
        
    def update(self, SC: float, u: float, U_vents: float, T_a: float, T_b: float,
              VP_a: float, VP_b: float, U_VentForced: float = None) -> tuple:
        """
        Update heat and mass flux exchange
        
        Parameters:
            SC (float): Screen closure (1:closed, 0:open)
            u (float): Wind speed [m/s]
            U_vents (float): Control of roof vents (0 to 1)
            T_a (float): Temperature at port a [K]
            T_b (float): Temperature at port b [K]
            VP_a (float): Vapor pressure at port a [Pa]
            VP_b (float): Vapor pressure at port b [Pa]
            U_VentForced (float, optional): Control of forced ventilation (0 to 1)
            
        Returns:
            tuple: (Q_flow, MV_flow) Heat and mass flow rates [W, kg/s]
        """
        # Update input variables
        self.SC = SC
        self.u = u
        self.U_vents = U_vents
        if U_VentForced is not None:
            self.U_VentForced = U_VentForced
            
        # Update port temperatures and vapor pressures
        self.HeatPort_a.T = T_a
        self.HeatPort_b.T = T_b
        self.MassPort_a.VP = VP_a
        self.MassPort_b.VP = VP_b
        
        # Calculate temperature difference
        dT = T_a - T_b
        
        # Update natural ventilation rate
        self.natural_vent.update(
            u=self.u,
            dT=dT,
            T_a=T_a,
            T_b=T_b,
            U_roof=self.U_vents,
            SC=self.SC
        )
        
        # Get natural ventilation rate based on air zone
        if not self.topAir:
            self.f_vent = self.natural_vent.f_vent_air
        else:
            self.f_vent = self.natural_vent.f_vent_top
            
        # Calculate forced ventilation rate
        if self.forcedVentilation and not self.topAir:
            self.forced_vent.update(U_VentForced=self.U_VentForced)
            self.f_ventForced = self.forced_vent.f_ventForced
        else:
            self.f_ventForced = 0.0
            
        # Calculate total ventilation rate
        self.f_vent_total = self.f_vent + self.f_ventForced
        
        # Calculate heat transfer
        self.HEC_ab = self.rho_air * self.c_p_air * self.f_vent_total
        self.Q_flow = self.A * self.HEC_ab * dT
        
        # Calculate moisture transfer
        self.MV_flow = (self.A * self.M_H * self.f_vent_total / self.R * 
                       (VP_a/T_a - VP_b/T_b))
        
        # Update port flows
        self.HeatPort_a.Q_flow = self.Q_flow
        self.HeatPort_b.Q_flow = -self.Q_flow
        self.MassPort_a.MV_flow = self.MV_flow
        self.MassPort_b.MV_flow = -self.MV_flow
        
        return self.Q_flow, self.MV_flow
