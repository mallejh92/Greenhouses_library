import numpy as np

class Convection_Evaporation:
    """
    Upward heat exchange by free convection between the thermal screen (filled port) and top air (empty port).
    Mass transfer by evaporation from upper side of the screen to the air at the top compartment
    """
    
    def __init__(self, A: float):
        """
        Initialize convection and evaporation model
        
        Parameters:
            A (float): Floor surface [m2]
        """
        # Parameters
        self.A = A
        
        # Input variables
        self.SC = 0.0  # Screen closure 1:closed, 0:open
        self.MV_AirScr = 0.0  # Mass flow rate from the main air zone to the screen [kg/s]
        
        # State variables
        self.HEC_ab = 0.0  # Heat exchange coefficient [W/(m2.K)]
        self.VEC_ab = 0.0  # Mass transfer coefficient [kg/(s.Pa.m2)]
        self.Q_flow = 0.0  # Heat flow rate [W]
        self.MV_flow = 0.0  # Mass flow rate [kg/s]
        
    def update(self, SC: float, T_a: float, T_b: float, VP_a: float, VP_b: float, 
              MV_AirScr: float = None) -> tuple:
        """
        Update heat and mass flux exchange
        
        Parameters:
            SC (float): Screen closure (1:closed, 0:open)
            T_a (float): Temperature at port a [K]
            T_b (float): Temperature at port b [K]
            VP_a (float): Vapor pressure at port a [Pa]
            VP_b (float): Vapor pressure at port b [Pa]
            MV_AirScr (float, optional): Mass flow rate from main air to screen [kg/s]
            
        Returns:
            tuple: (Q_flow, MV_flow) Heat and mass flow rates [W, kg/s]
        """
        # Update input variables
        self.SC = SC
        if MV_AirScr is not None:
            self.MV_AirScr = MV_AirScr
            
        # Calculate temperature and pressure differences
        dT = T_a - T_b
        dP = VP_a - VP_b
        
        # Calculate heat exchange coefficient and heat flow
        self.HEC_ab = self.SC * 1.7 * max(1e-9, abs(dT))**0.33
        self.Q_flow = self.A * self.HEC_ab * dT
        
        # Calculate mass transfer coefficient and mass flow
        self.VEC_ab = max(0, min(6.4e-9 * self.HEC_ab, 
                                self.MV_AirScr / self.A / max(1e-9, dP)))
        self.MV_flow = max(0, self.A * self.VEC_ab * dP)  # Evaporation fluxes are prohibited from being negative
        
        return self.Q_flow, self.MV_flow
