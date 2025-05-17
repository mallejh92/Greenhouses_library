import numpy as np

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
        self.T = T_start
        self.steadystate = steadystate

        # Constants
        self.Lv = 2.45e6  # Latent heat of vaporization [J/kg]

        # Variables
        self.Q_flow = 0.0     # Heat flow rate [W]
        self.L_scr = 0.0      # Latent heat flow [W]
        self.MV_flow = 0.0    # Water vapor mass flow [kg/s], externally set
        self.FF_i = 0.0
        self.FF_ij = 0.0

    def set_vapor_mass_flow(self, MV_flow):
        self.MV_flow = MV_flow

    def step(self, dt, Q_flow_input=None, SC_input=None):
        """
        Advance the simulation by one time step
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        Q_flow_input : float, optional
            Heat flow rate input [W]
        SC_input : float, optional
            Screen closure input (0-1)
        """
        if SC_input is not None:
            self.SC = SC_input

        self.FF_i = self.SC
        self.FF_ij = self.SC * (1 - self.tau_FIR)

        if Q_flow_input is not None:
            self.Q_flow = Q_flow_input
            
        self.L_scr = self.MV_flow * self.Lv  # [W]

        if not self.steadystate:
            dT_dt = (self.Q_flow + self.L_scr) / (self.rho * self.c_p * self.h * self.A)
            self.T += dT_dt * dt  # Euler integration
        # else: temperature remains constant

    def get_temperature(self):
        return self.T

    def get_latent_heat_flow(self):
        return self.L_scr

    def get_radiative_factors(self):
        return self.FF_i, self.FF_ij
