import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Components.Greenhouse.BasicComponents.SurfaceVP import SurfaceVP

class Cover:
    """
    Python version of the Greenhouses.Components.Greenhouse.Cover model.
    Computes energy balance of the greenhouse cover including:
    - Sensible heat flow (convection, radiation)
    - Latent heat from condensation
    - Absorbed solar radiation
    """

    def __init__(self, A, phi, rho=2600, c_p=840, h_cov=1e-3,
                 T_start=298.0, steadystate=False):
        # Parameters
        self.A = A                      # Floor surface area [m²]
        self.phi = phi                  # Roof slope [rad]
        self.h_cov = h_cov              # Cover thickness [m]
        self.rho = rho                  # Cover density [kg/m³]
        self.c_p = c_p                  # Specific heat capacity [J/kg/K]
        self.latent_heat_vap = 2.45e6   # [J/kg]

        # Options
        self.steadystate = steadystate

        # State
        self.T = T_start                # Temperature [K]
        self.Q_flow = 0.0               # Net heat flow [W]
        self.R_SunCov_Glob = 0.0        # Solar radiation [W/m²]
        self.MV_flow = 0.0              # Moisture flow [kg/s]

        # Derived
        self.V = self.h_cov * self.A / np.cos(self.phi)  # Volume of the cover material
        self.P_SunCov = 0.0
        self.L_cov = 0.0

        # Ports
        self.heatPort = HeatPort_a(T_start=T_start)  # Heat port with initial temperature
        self.massPort = WaterMassPort_a()
        self.surfaceVP = SurfaceVP(T=T_start)  # Surface vapor pressure component
        
        # Connect ports
        self.surfaceVP.port = self.massPort

    def compute_power_input(self):
        self.P_SunCov = self.R_SunCov_Glob * self.A

    def compute_latent_heat(self):
        self.L_cov = self.MV_flow * self.latent_heat_vap

    def compute_derivatives(self):
        if self.steadystate:
            return 0.0
        self.compute_power_input()
        self.compute_latent_heat()
        return (self.Q_flow + self.P_SunCov + self.L_cov) / (self.rho * self.c_p * self.V)

    def step(self, dt):
        dTdt = self.compute_derivatives()
        self.T += dTdt * dt
        self.heatPort.T = self.T  # Update heat port temperature
        self.surfaceVP.T = self.T  # Update surfaceVP temperature
        return self.T

    def set_inputs(self, Q_flow, R_SunCov_Glob, MV_flow=0.0):
        """
        Set input values for the cover
        
        Parameters:
        -----------
        Q_flow : float
            Total heat flow to the cover [W]
        R_SunCov_Glob : float
            Global solar radiation on the cover [W/m²]
        MV_flow : float, optional
            Mass vapor flow rate [kg/s], defaults to 0.0
        """
        self.Q_flow = Q_flow
        self.R_SunCov_Glob = R_SunCov_Glob
        self.MV_flow = MV_flow
        self.heatPort.Q_flow = Q_flow  # Update heat port heat flow
