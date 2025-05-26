import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Components.Greenhouse.BasicComponents.SurfaceVP import SurfaceVP

class Canopy:
    """
    Python version of the Greenhouses.Components.Greenhouse.Canopy model.
    Computes canopy temperature based on energy balance including:
    - Long-wave radiation and convection (Q_flow)
    - Short-wave solar radiation (R_Can_Glob)
    - Latent heat from transpiration (L_can)
    """

    def __init__(self, A, LAI=1.0, Cap_leaf=1200, N_rad=2,
                 T_start=298.0, steadystate=False):
        # Parameters
        self.A = A                  # Greenhouse floor surface area [m²]
        self.LAI = LAI              # Leaf Area Index
        self.Cap_leaf = Cap_leaf    # Heat capacity per m² of leaf [J/K]
        self.N_rad = N_rad          # Number of radiation sources
        self.latent_heat_vap = 2.45e6  # Latent heat of vaporization [J/kg]

        # Options
        self.steadystate = steadystate

        # State
        self.T = T_start            # Temperature [K]

        # Inputs
        self.Q_flow = 0.0           # Net sensible heat from surroundings [W]
        self.R_Can_Glob = np.zeros(N_rad)  # Short-wave radiation inputs [W/m²]
        self.massPort_MV_flow = 0.0 # Moisture mass flow rate [kg/s]

        # Outputs
        self.P_Can = 0.0            # Radiation power absorbed [W]
        self.L_can = 0.0            # Latent heat transfer [W]
        self.FF = 0.0               # Foliage factor

        # Ports
        self.heatPort = HeatPort_a(T_start=T_start)  # Heat port with initial temperature
        self.massPort = WaterMassPort_a()
        self.surfaceVP = SurfaceVP(T=T_start)  # Surface vapor pressure component
        
        # Connect ports
        self.surfaceVP.port = self.massPort

    def compute_power_input(self):
        self.P_Can = np.sum(self.R_Can_Glob) * self.A

    def compute_latent_heat(self):
        self.L_can = self.massPort_MV_flow * self.latent_heat_vap

    def compute_derivatives(self):
        if self.steadystate:
            return 0.0
        self.compute_power_input()
        self.compute_latent_heat()
        # Foliage factor (affects absorption, optional)
        self.FF = 1 - np.exp(-0.94 * self.LAI)
        return (self.Q_flow + self.P_Can + self.L_can) / (self.Cap_leaf * self.LAI * self.A)

    def step(self, dt):
        dTdt = self.compute_derivatives()
        self.T += dTdt * dt
        self.heatPort.T = self.T  # Update heat port temperature
        self.surfaceVP.T = self.T  # Update surfaceVP temperature
        return self.T

    def set_inputs(self, Q_flow, R_Can_Glob, MV_flow):
        self.Q_flow = Q_flow
        self.R_Can_Glob = np.array(R_Can_Glob)
        self.massPort_MV_flow = MV_flow
        self.heatPort.Q_flow = Q_flow  # Update heat port heat flow
