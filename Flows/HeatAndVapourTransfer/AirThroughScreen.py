import numpy as np

class AirThroughScreen:
    """
    Heat and mass flux exchange and air exchange rate through the screen
    """
    
    def __init__(self, A: float, W: float, K: float):
        """
        Initialize air through screen model
        
        Parameters:
            A (float): Floor surface [m2]
            W (float): Length of the screen when closed (SC=1) [m]
            K (float): Screen flow coefficient
        """
        # Parameters
        self.A = A
        self.W = W
        self.K = K
        
        # Constants
        self.c_p_air = 1005.0  # Specific heat capacity of air [J/(kg.K)]
        self.R = 8314.0  # Gas constant [J/(kmol.K)]
        self.M_H = 18.0  # Molar mass of water [kg/kmol]
        self.g_n = 9.81  # Gravitational acceleration [m/s2]
        
        # Input variables
        self.SC = 0.0  # Screen closure 1:closed, 0:open
        
        # State variables
        self.HEC_ab = 0.0  # Heat exchange coefficient [W/(m2.K)]
        self.rho_air = 0.0  # Air density at port a [kg/m3]
        self.rho_top = 0.0  # Air density at port b [kg/m3]
        self.rho_mean = 0.0  # Mean air density [kg/m3]
        self.f_AirTop = 0.0  # Air exchange rate [m3/(m2.s)]
        self.VEC_AirTop = 0.0  # Mass transfer coefficient [kg/(s.Pa.m2)]
        self.MV_flow = 0.0  # Mass flow rate [kg/s]
        self.MV_flow2 = 0.0  # Alternative mass flow rate [kg/s]
        self.Q_flow = 0.0  # Heat flow rate [W]
        
    def update(self, SC: float, T_a: float, T_b: float, VP_a: float, VP_b: float, dP: float) -> tuple:
        """
        Update heat and mass flux exchange
        
        Parameters:
            SC (float): Screen closure (1:closed, 0:open)
            T_a (float): Temperature at port a [K]
            T_b (float): Temperature at port b [K]
            VP_a (float): Vapor pressure at port a [Pa]
            VP_b (float): Vapor pressure at port b [Pa]
            dP (float): Pressure difference [Pa]
            
        Returns:
            tuple: (Q_flow, MV_flow) Heat and mass flow rates [W, kg/s]
        """
        # Update input variable
        self.SC = SC
        
        # Calculate air densities (simplified from Modelica.Media.Air.ReferenceAir.Air_pT)
        self.rho_air = 1e5 / (287.0 * T_a)  # Ideal gas law
        self.rho_top = 1e5 / (287.0 * T_b)
        self.rho_mean = (self.rho_air + self.rho_top) / 2
        
        # Calculate air exchange rate
        self.f_AirTop = (self.SC * self.K * max(1e-9, abs(T_a - T_b))**0.66 + 
                        (1 - self.SC) * (max(1e-9, 0.5 * self.rho_mean * self.W * 
                        (1 - self.SC) * self.g_n * max(1e-9, abs(self.rho_air - self.rho_top))))**0.5 / 
                        self.rho_mean)
        
        # Calculate heat exchange coefficient and heat flow
        self.HEC_ab = self.rho_air * self.c_p_air * self.f_AirTop
        self.Q_flow = self.A * self.HEC_ab * (T_a - T_b)
        
        # Calculate mass exchange coefficient and mass flow
        self.VEC_AirTop = self.M_H * self.f_AirTop / (self.R * 287.0)
        self.MV_flow2 = self.A * self.M_H / self.R * self.f_AirTop * (VP_a/T_a - VP_b/T_b)
        self.MV_flow = self.A * self.VEC_AirTop * dP
        
        return self.Q_flow, self.MV_flow
