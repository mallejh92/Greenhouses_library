import numpy as np

class Convection_Evaporation:
    """
    Heat and mass transfer by evaporation from a surface to the air.
    Mass transfer by evaporation from the cover/screen (empty port) to the air (filled port).
    """
    
    def __init__(self, A: float, SC: float = 0.0):
        """
        Initialize convection and evaporation model
        
        Parameters:
            A (float): Floor surface [m2]
            SC (float): Screen closure (1:closed, 0:open), default is 0.0
        """
        # Parameters
        self.A = A
        
        # Input variables
        self.SC = SC  # Screen closure 1:closed, 0:open
        
        # Port variables (Modelica naming)
        class HeatPort:
            def __init__(self):
                self.T = 293.15  # Temperature [K]
                self.Q_flow = 0.0  # Heat flow rate [W]
        
        class MassPort:
            def __init__(self):
                self.VP = 0.0  # Vapor pressure [Pa]
                self.P = 101325.0  # Total pressure [Pa]
                self.MV_flow = 0.0  # Mass flow rate [kg/s]
        
        self.HeatPort_a = HeatPort()
        self.HeatPort_b = HeatPort()
        self.MassPort_a = MassPort()
        self.MassPort_b = MassPort()
        
        # State variables
        self.HEC_ab = 0.0  # Heat exchange coefficient [W/(m2.K)]
        self.VEC_ab = 0.0  # Mass transfer coefficient [kg/(s.Pa.m2)]
        self.Q_flow = 0.0  # Heat flow rate [W]
        self.MV_flow = 0.0  # Mass flow rate [kg/s]
        
    def step(self, dt: float) -> None:
        """
        Update heat and mass flux exchange for one time step
        
        Parameters:
            dt (float): Time step [s]
        """
        # Update heat and mass flux exchange
        self.update(
            SC=self.SC,
            T_a=self.HeatPort_a.T,
            T_b=self.HeatPort_b.T,
            VP_a=self.MassPort_a.VP,
            VP_b=self.MassPort_b.VP
        )
        
    def update(self, SC: float, T_a: float, T_b: float, VP_a: float, VP_b: float) -> tuple:
        """
        Update heat and mass flux exchange
        
        Parameters:
            SC (float): Screen closure (1:closed, 0:open)
            T_a (float): Temperature at port a [K]
            T_b (float): Temperature at port b [K]
            VP_a (float): Vapor pressure at port a [Pa]
            VP_b (float): Vapor pressure at port b [Pa]
            
        Returns:
            tuple: (Q_flow, MV_flow) Heat and mass flow rates [W, kg/s]
        """
        # Update input variable
        self.SC = SC
        
        # Calculate temperature difference
        dT = T_a - T_b
        
        # Calculate heat exchange coefficient
        self.HEC_ab = self.SC * 1.7 * max(1e-9, abs(dT))**0.33
        
        # Calculate heat flow
        self.Q_flow = self.A * self.HEC_ab * dT
        
        # Calculate mass transfer coefficient and mass flow
        self.VEC_ab = max(0, 6.4e-9 * self.HEC_ab)
        self.MV_flow = max(0, self.A * self.VEC_ab * (VP_a - VP_b))  # Evaporation fluxes are prohibited from being negative
        
        # Update port values
        self.HeatPort_a.Q_flow = self.Q_flow
        self.HeatPort_b.Q_flow = -self.Q_flow
        self.MassPort_a.MV_flow = self.MV_flow
        self.MassPort_b.MV_flow = -self.MV_flow
        
        return self.Q_flow, self.MV_flow
