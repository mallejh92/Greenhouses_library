import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.Element1D import Element1D

class Convection_Condensation(Element1D):
    """
    Upward or downward heat exchange by free convection from an horizontal or inclined surface.
    Mass transfer by condensation from the air (filled port) to the cover/screen (empty port).
    If studying heat exchange of Air-Floor: connect the filled port to the floor and the unfilled port to the air.
    """
    
    def __init__(self, phi: float, A: float, floor: bool = False, 
                 thermalScreen: bool = False, Air_Cov: bool = True, topAir: bool = False,
                 SC: float = 0.0):
        """
        Initialize convection and condensation model
        
        Parameters:
            phi (float): Inclination of the surface (0 if horizontal, 25 for typical cover) [rad]
            A (float): Floor surface [m2]
            floor (bool): True if floor, false if cover or thermal screen heat flux
            thermalScreen (bool): Presence of a thermal screen in the greenhouse
            Air_Cov (bool): True if heat exchange air-cover, False if heat exchange air-screen
            topAir (bool): False if MainAir-Cov; True for: TopAir-Cov
            SC (float): Screen closure (1:closed, 0:open), default is 0.0
        """
        # Initialize parent class
        super().__init__()
        
        # Parameters
        self.phi = phi
        self.A = A
        self.floor = floor
        self.thermalScreen = thermalScreen
        self.Air_Cov = Air_Cov
        self.topAir = topAir
        
        # Constants
        self.s = 11.0  # Slope of the differentiable switch function for vapour pressure differences
        
        # Input variables
        self.SC = SC  # Screen closure 1:closed, 0:open
        
        # State variables
        self.HEC_ab = 0.0  # Heat exchange coefficient [W/(m2.K)]
        self.VEC_ab = 0.0  # Mass transfer coefficient [kg/(s.Pa.m2)]
        self.HEC_up_flr = 0.0  # Upward heat exchange coefficient [W/(m2.K)]
        self.HEC_down_flr = 0.0  # Downward heat exchange coefficient [W/(m2.K)]
        
        # Mass transfer ports
        self.MassPort_a = type('MassPort', (), {'VP': 0.0, 'P': 0.0})()
        self.MassPort_b = type('MassPort', (), {'VP': 0.0, 'P': 0.0})()
        self.massPort_a = self.MassPort_a
        self.massPort_b = self.MassPort_b
        # Heat transfer ports (상위 클래스에 정의되어 있다고 가정)
        if not hasattr(self, 'heatPort_a'):
            self.heatPort_a = type('HeatPort', (), {'T': 293.15, 'Q_flow': 0.0})()
        if not hasattr(self, 'heatPort_b'):
            self.heatPort_b = type('HeatPort', (), {'T': 293.15, 'Q_flow': 0.0})()
        
    def step(self) -> None:
        """
        Update heat and mass flux exchange for one time step
        """
        # Update heat and mass flux exchange
        self.update(
            SC=self.SC,
            T_a=self.heatPort_a.T,
            T_b=self.heatPort_b.T,
            VP_a=self.massPort_a.VP,
            VP_b=self.massPort_b.VP
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
        
        # Calculate temperature and pressure differences
        dT = T_a - T_b
        dP = VP_a - VP_b
        
        # Calculate heat exchange coefficient based on conditions
        if not self.floor:
            if self.thermalScreen:
                if self.Air_Cov:
                    if not self.topAir:
                        # Exchange main air-cover (with screen)
                        # 스크린이 닫혀있을 때(SC=1)와 열려있을 때(SC=0)의 대류 열전달을 모두 고려
                        self.HEC_ab = (1 - self.SC) * 1.7 * max(1e-9, abs(dT))**0.33 * (np.cos(self.phi))**(-0.66) + \
                                    self.SC * 0.5 * 1.7 * max(1e-9, abs(dT))**0.33 * (np.cos(self.phi))**(-0.66)
                    else:
                        # Exchange top air-cover
                        # 스크린이 닫혀있을 때만 상부 공기-커버 간 대류 열전달 발생
                        self.HEC_ab = self.SC * 1.7 * max(1e-9, abs(dT))**0.33 * (np.cos(self.phi))**(-0.66)
                else:
                    # Exchange air-screen
                    # 스크린이 닫혀있을 때만 공기-스크린 간 대류 열전달 발생
                    self.HEC_ab = self.SC * 1.7 * max(1e-9, abs(dT))**0.33
            else:
                # Exchange main air-cover (no screen)
                self.HEC_ab = 1.7 * max(1e-9, abs(dT))**0.33 * (np.cos(self.phi))**(-0.66)
            self.HEC_up_flr = 0.0  # dummy
            self.HEC_down_flr = 0.0
        else:
            # Calculate heat exchange coefficients using differentiable switch function
            self.HEC_up_flr = 1/(1 + np.exp(-self.s * dT)) * 1.7 * abs(dT)**0.33  # Used for dT>0
            self.HEC_down_flr = 1/(1 + np.exp(self.s * dT)) * 1.3 * abs(dT)**0.25  # Used for dT<0
            self.HEC_ab = self.HEC_up_flr + self.HEC_down_flr
            
        # Calculate heat flow
        self.Q_flow = self.A * self.HEC_ab * dT
        
        # Calculate mass transfer coefficient and mass flow
        self.VEC_ab = max(0, 6.4e-9 * self.HEC_ab)
        self.MV_flow = max(0, self.A * self.VEC_ab * dP)  # Condensation fluxes are prohibited from being negative
        
        # Update parent class variables
        super().update()
        
        return self.Q_flow, self.MV_flow
