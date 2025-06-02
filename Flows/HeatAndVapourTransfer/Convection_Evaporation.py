import numpy as np
from Interfaces.HeatAndVapour.Element1D import Element1D

class Convection_Evaporation(Element1D):
    """
    Upward heat exchange by free convection between the thermal screen (filled port) and top air (empty port).
    Mass transfer by evaporation from upper side of the screen to the air at the top compartment.
    """
    
    def __init__(self, A: float, SC: float = 0.0):
        """
        Initialize convection and evaporation model
        
        Parameters:
            A (float): Floor surface [m²]
            SC (float): Screen closure (1:closed, 0:open), default is 0.0
        """
        # Initialize parent class with default values
        super().__init__()
        
        # Parameters
        self.A = A
        
        # Input variables
        self.SC = SC  # Screen closure 1:closed, 0:open
        self.MV_AirScr = 0.0  # Mass flow rate from the main air zone to the screen [kg/s]
        
        # State variables
        self.HEC_ab = 0.0  # Heat exchange coefficient [W/(m²·K)]
        self.VEC_ab = 0.0  # Mass transfer coefficient [kg/(s·Pa·m²)]
        
        # Mass transfer ports
        self.MassPort_a = type('MassPort', (), {'VP': 0.0, 'P': 0.0})()
        self.MassPort_b = type('MassPort', (), {'VP': 0.0, 'P': 0.0})()
        self.massPort_a = self.MassPort_a
        self.massPort_b = self.MassPort_b
        
    def step(self) -> None:
        """
        Update heat and mass flux exchange for one time step
        """
        # Update heat and mass flux exchange
        self.update(
            SC=self.SC,
            MV_AirScr=self.MV_AirScr,
            T_a=self.HeatPort_a.T,
            T_b=self.HeatPort_b.T,
            VP_a=self.MassPort_a.VP,
            VP_b=self.MassPort_b.VP
        )
        
    def update(self, SC: float, MV_AirScr: float, T_a: float, T_b: float, VP_a: float, VP_b: float) -> tuple:
        """
        Update heat and mass flux exchange
        
        Parameters:
            SC (float): Screen closure (1:closed, 0:open)
            MV_AirScr (float): Mass flow rate from the main air zone to the screen [kg/s]
            T_a (float): Temperature at port a [K]
            T_b (float): Temperature at port b [K]
            VP_a (float): Vapor pressure at port a [Pa]
            VP_b (float): Vapor pressure at port b [Pa]
            
        Returns:
            tuple: (Q_flow, MV_flow) Heat and mass flow rates [W, kg/s]
        """
        # Update input variables
        self.SC = SC
        self.MV_AirScr = MV_AirScr
        
        # Calculate temperature and pressure differences
        dT = T_a - T_b
        dP = VP_a - VP_b
        
        # Calculate heat exchange coefficient
        self.HEC_ab = self.SC * 1.7 * max(1e-9, abs(dT))**0.33
        
        # Calculate heat flow
        self.Q_flow = self.A * self.HEC_ab * dT
        
        # Calculate mass transfer coefficient and mass flow
        # Modelica: VEC_ab = max(0, min(6.4e-9*HEC_ab, MV_AirScr/A/max(1e-9,dP)))
        self.VEC_ab = max(0, min(6.4e-9 * self.HEC_ab, 
                                self.MV_AirScr / (self.A * max(1e-9, dP))))
        
        # Modelica: MV_flow = max(0, A*VEC_ab*dP)
        self.MV_flow = max(0, self.A * self.VEC_ab * dP)
        
        # Update parent class variables
        super().update()
        
        return self.Q_flow, self.MV_flow
