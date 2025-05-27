import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.Element1D import Element1D

class FreeConvection(Element1D):
    """
    Upward or downward heat exchange by free convection from a horizontal or inclined surface.
    If studying heat exchange of Air-Floor: connect the filled port to the floor and the unfilled port to the air.
    """
    def __init__(self, phi, A, floor=False, thermalScreen=False, Air_Cov=True, topAir=False):
        """
        Initialize the FreeConvection model
        Parameters:
            phi (float): Inclination of the surface [rad]
            A (float): Floor surface area [m²]
            floor (bool): True if floor, false if cover or thermal screen heat flux
            thermalScreen (bool): Presence of a thermal screen in the greenhouse
            Air_Cov (bool): True if heat exchange air-cover, False if air-screen
            topAir (bool): False if MainAir-Cov; True for TopAir-Cov
        """
        super().__init__()
        self.phi = phi
        self.A = A
        self.floor = floor
        self.thermalScreen = thermalScreen
        self.Air_Cov = Air_Cov
        self.topAir = topAir
        self.SC = 0
        self.s = 11
        self.HEC_ab = 0.0
        self.HEC_up_flr = 0.0
        self.HEC_down_flr = 0.0
        # Modelica-style port names
        if not hasattr(self, 'heatPort_a'):
            self.heatPort_a = type('HeatPort', (), {'T': 293.15, 'Q_flow': 0.0})()
        if not hasattr(self, 'heatPort_b'):
            self.heatPort_b = type('HeatPort', (), {'T': 293.15, 'Q_flow': 0.0})()
    def step(self, dt):
        """
        Calculate heat transfer by free convection
        Parameters:
            dt (float): Time step [s]
        """
        self.dT = self.heatPort_a.T - self.heatPort_b.T
        if not self.floor:
            if self.thermalScreen:
                if self.Air_Cov:
                    if not self.topAir:
                        self.HEC_ab = 0
                    else:
                        self.HEC_ab = 1.7 * max(1e-9, abs(self.dT))**0.33 * (np.cos(self.phi))**(-0.66)
                else:
                    self.HEC_ab = self.SC * 1.7 * max(1e-9, abs(self.dT))**0.33
            else:
                self.HEC_ab = 1.7 * max(1e-9, abs(self.dT))**0.33 * (np.cos(self.phi))**(-0.66)
            self.HEC_up_flr = 0
            self.HEC_down_flr = 0
        else:
            self.HEC_up_flr = 1/(1 + np.exp(-self.s * self.dT)) * 1.7 * abs(self.dT)**0.33
            self.HEC_down_flr = 1/(1 + np.exp(self.s * self.dT)) * 1.3 * abs(self.dT)**0.25
            self.HEC_ab = self.HEC_up_flr + self.HEC_down_flr
        self.Q_flow = self.A * self.HEC_ab * self.dT
        self.heatPort_a.Q_flow = self.Q_flow
        self.heatPort_b.Q_flow = -self.Q_flow
