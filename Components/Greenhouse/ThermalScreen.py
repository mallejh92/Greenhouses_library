import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Components.Greenhouse.BasicComponents.SurfaceVP import SurfaceVP

class ThermalScreen:
    def __init__(self, A, SC=0, rho=0.2e3, c_p=1.8e3, h=0.35e-3, tau_FIR=0.15,
                 T_start=298.15, steadystate=False, steadystateVP=True):
        """
        Initialize ThermalScreen component
        
        Parameters:
        -----------
        A : float
            Screen area [m²]
        SC : float
            Screen closure [0-1]
        rho : float
            Material density [kg/m³]
        c_p : float
            Specific heat capacity [J/(kg·K)]
        h : float
            Material thickness [m]
        tau_FIR : float
            Far-infrared transmittance [-]
        T_start : float
            Initial temperature [K]
        steadystate : bool
            Whether to use steady state initialization
        steadystateVP : bool
            Whether to use steady state initialization for vapor pressure
        """
        # Parameters
        self.A = A
        self.SC = SC
        self.rho = rho
        self.c_p = c_p
        self.h = h
        self.tau_FIR = tau_FIR
        self.steadystate = steadystate
        self.steadystateVP = steadystateVP
        
        # State variables
        self.T = T_start  # Temperature [K]
        self.Q_flow = 0.0  # Heat flow rate [W]
        self.L_scr = 0.0  # Latent heat flow [W]
        
        # View factors
        self.FF_i = SC  # View factor for radiation
        self.FF_ij = SC * (1 - tau_FIR)  # View factor for FIR
        
        # Constants
        self.Lv = 2.5e6  # Latent heat of vaporization [J/kg]
        
        # Components
        self.heatPort = HeatPort_a(T_start=T_start)
        self.massPort = WaterMassPort_a()
        self.surfaceVP = SurfaceVP(T=T_start)
        
        # Connect surfaceVP to massPort
        self.surfaceVP.port = self.massPort
    
    def step(self, dt):
        """
        Update the thermal screen state for one time step
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        # Update view factors (same as Modelica equations)
        self.FF_i = self.SC
        self.FF_ij = self.SC * (1 - self.tau_FIR)
        
        # Calculate latent heat (same as Modelica equation)
        self.L_scr = self.massPort.MV_flow * self.Lv
        
        if not self.steadystate:
            # Temperature derivative (equivalent to Modelica's der(T))
            dT_dt = (self.Q_flow + self.L_scr) / (self.rho * self.c_p * self.h * self.A)
            self.T += dT_dt * dt
            
            # Update surfaceVP temperature
            self.surfaceVP.T = self.T
            
            # Update heat port temperature
            self.heatPort.T = self.T
    
    def get_temperature(self):
        """Return the current temperature"""
        return self.T
    
    def get_latent_heat_flow(self):
        """Return the latent heat flow"""
        return self.L_scr
    
    def get_radiative_factors(self):
        """Return the radiative view factors"""
        return self.FF_i, self.FF_ij
    
    def set_inputs(self, Q_flow=0.0):
        """
        Set heat flow input
        
        Parameters:
        -----------
        Q_flow : float
            Heat flow rate [W]
        """
        self.Q_flow = Q_flow
        self.heatPort.Q_flow = Q_flow
