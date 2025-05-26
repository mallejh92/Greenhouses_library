import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Components.Greenhouse.BasicComponents.SurfaceVP import SurfaceVP

class ThermalScreen:
    def __init__(self, A, SC=0, rho=0.2e3, c_p=1.8e3, h=0.35e-3, tau_FIR=0.15,
                 T_start=298, steadystate=False):
        # Parameters
        self.A = A
        self.SC = SC
        self.rho = rho
        self.c_p = c_p
        self.h = h
        self.tau_FIR = tau_FIR
        self.steadystate = steadystate

        # Constants
        self.Lv = 2.45e6  # Latent heat of vaporization [J/kg]

        # Variables
        self.Q_flow = 0.0     # Heat flow rate [W]
        self.L_scr = 0.0      # Latent heat flow [W]
        self.FF_i = 0.0
        self.FF_ij = 0.0

        # Ports
        self.heatPort = HeatPort_a(T_start=T_start)  # Heat port with initial temperature
        self.massPort = WaterMassPort_a()
        self.surfaceVP = SurfaceVP(T=T_start)  # Surface vapor pressure component
        
        # Connect ports
        self.surfaceVP.port = self.massPort

    def step(self, dt):
        """
        Advance the simulation by one time step
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        # Update view factors
        self.FF_i = self.SC
        self.FF_ij = self.SC * (1 - self.tau_FIR)

        # Calculate latent heat
        self.L_scr = self.massPort.MV_flow * self.Lv

        if not self.steadystate:
            # Temperature derivative (equivalent to Modelica's der(T))
            dT_dt = (self.Q_flow + self.L_scr) / (self.rho * self.c_p * self.h * self.A)
            self.heatPort.T += dT_dt * dt  # Update temperature
            
            # Update surfaceVP temperature
            self.surfaceVP.T = self.heatPort.T

    def get_temperature(self):
        return self.heatPort.T

    def get_latent_heat_flow(self):
        return self.L_scr

    def get_radiative_factors(self):
        return self.FF_i, self.FF_ij

    def set_inputs(self, Q_flow=0.0):
        """Set heat flow input"""
        self.Q_flow = Q_flow
        self.heatPort.Q_flow = Q_flow
