import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Components.Greenhouse.BasicComponents.SurfaceVP import SurfaceVP
from Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature import PrescribedTemperature
from Modelica.Blocks.Sources.RealExpression import RealExpression

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
        """
        Initialize Cover component
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        phi : float
            Roof slope [rad]
        rho : float
            Cover density [kg/m³]
        c_p : float
            Specific heat capacity [J/(kg·K)]
        h_cov : float
            Cover thickness [m]
        T_start : float
            Initial temperature [K]
        steadystate : bool
            Whether to use steady state initialization
        """
        # Parameters
        self.A = A                      # Floor surface area [m²]
        self.phi = phi                  # Roof slope [rad]
        self.h_cov = h_cov              # Cover thickness [m]
        self.rho = rho                  # Cover density [kg/m³]
        self.c_p = c_p                  # Specific heat capacity [J/(kg·K)]
        self.latent_heat_vap = 2.45e6   # Latent heat of vaporization [J/kg]

        # Options
        self.steadystate = steadystate

        # State variables
        self.T = T_start                # Temperature [K]
        self.Q_flow = 0.0               # Net heat flow [W]
        self.R_SunCov_Glob = 0.0        # Solar radiation [W/m²]
        self.MV_flow = 0.0              # Moisture flow [kg/s]

        # Derived variables
        self.V = self.h_cov * self.A / np.cos(self.phi)  # Volume [m³]
        self.P_SunCov = 0.0             # Absorbed power [W]
        self.L_cov = 0.0                # Latent heat [W]

        # Components
        self.heatPort = HeatPort_a(T_start=T_start)
        self.massPort = WaterMassPort_a()  # VP는 나중에 설정
        self.surfaceVP = SurfaceVP(T=T_start)
        self.preTem = PrescribedTemperature(T_start=T_start)
        
        # RealExpression for port temperature
        # Modelica: portT(y=T) -> RealExpression with y=T
        self.portT = RealExpression(y=lambda time: self.T)  # time-dependent expression
        
        # Connect components
        self.portT.connect(self.preTem)  # portT.y -> preTem.T
        self.preTem.connect_port(self.heatPort)  # preTem.port -> heatPort
        self.surfaceVP.port = self.massPort  # surfaceVP.port -> massPort

    def compute_power_input(self):
        """Calculate absorbed power from solar radiation"""
        self.P_SunCov = self.R_SunCov_Glob * self.A

    def compute_latent_heat(self):
        """Calculate latent heat from condensation"""
        self.L_cov = self.MV_flow * self.latent_heat_vap

    def compute_derivatives(self):
        """Compute temperature derivative"""
        if self.steadystate:
            return 0.0
            
        self.compute_power_input()
        self.compute_latent_heat()
        
        # Modelica equation: der(T) = 1/(rho*c_p*V)*(Q_flow + P_SunCov + L_cov)
        return (self.Q_flow + self.P_SunCov + self.L_cov) / (self.rho * self.c_p * self.V)

    def step(self, dt):
        """
        Advance simulation by one time step
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        # Update temperature
        dTdt = self.compute_derivatives()
        self.T += dTdt * dt
        
        # Update components
        self.heatPort.T = self.T
        self.surfaceVP.T = self.T
        
        # Update RealExpression and propagate changes
        self.portT.time += dt  # Advance time
        self.portT.calculate()  # Calculate and propagate new value
        
        return self.T

    def set_inputs(self, Q_flow, R_SunCov_Glob, MV_flow=0.0):
        """
        Set input values
        
        Parameters:
        -----------
        Q_flow : float
            Total heat flow to the cover [W]
        R_SunCov_Glob : float
            Global solar radiation on the cover [W/m²]
        MV_flow : float, optional
            Mass vapor flow rate [kg/s]
        """
        self.Q_flow = Q_flow
        self.R_SunCov_Glob = R_SunCov_Glob
        self.MV_flow = MV_flow
        self.heatPort.Q_flow = Q_flow
