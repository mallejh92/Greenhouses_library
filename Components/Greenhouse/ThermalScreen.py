import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature import PrescribedTemperature
from Modelica.Blocks.Sources.RealExpression import RealExpression
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Components.Greenhouse.BasicComponents.SurfaceVP import SurfaceVP

class ThermalScreen:
    def __init__(self, A, SC=0, rho=0.89e3, c_p=1.2e3, h=0.35e-3, tau_FIR=0.15,
                 T_start=298.15, steadystate=False):
        """
        Initialize ThermalScreen component
        
        Parameters:
        -----------
        A : float
            Screen area [m²]
        SC : float
            Screen closure [0-1]
        rho : float
            Material density [kg/m³] - 수정: 0.2 kg/m³ (매우 가벼운 스크린 재질)
        c_p : float
            Specific heat capacity [J/(kg·K)]
        h : float
            Material thickness [m]
        tau_FIR : float
            Far-infrared transmittance [-]
        T_start : float
            Initial temperature [K]
        steadystate : bool
            Whether to use steady state initialization
        # steadystateVP : bool
        #     Whether to use steady state initialization for vapor pressure
        """
        # Parameters
        self.A = A
        self.SC = SC
        self.rho = rho
        self.c_p = c_p
        self.h = h
        self.tau_FIR = tau_FIR
        self.steadystate = steadystate
        # self.steadystateVP = steadystateVP
        
        # State variables
        self.T = T_start  # Temperature [K]
        self.Q_flow = 0.0  # Heat flow rate [W]
        self.L_scr = 0.0  # Latent heat flow [W]
        
        # View factors
        self.FF_i = SC  # View factor for radiation
        self.FF_ij = SC * (1 - tau_FIR)  # View factor for FIR
                
        # Components (Modelica 구조와 동일)
        self.heatPort = HeatPort_a(T_start=T_start)
        self.massPort = WaterMassPort_a()
        self.surfaceVP = SurfaceVP(T=T_start)
        
        # Modelica 원본과 동일한 구조 추가
        self.preTem = PrescribedTemperature(T_start=T_start)
        self.portT = RealExpression(y=T_start)
        
        # Connect surfaceVP to massPort
        self.surfaceVP.port = self.massPort

        # 초기 steady state 처리
        if self.steadystate:
            # der(T) = 0 조건 적용
            pass
        
        # 초기 연결 설정
        self._setup_connections()

    def _setup_connections(self):
        """Set up internal connections like in Modelica"""
        # Modelica 원본과 동일한 연결 구조
        self.surfaceVP.port = self.massPort
        self.surfaceVP.T = self.T
        
        # PrescribedTemperature 연결
        self.portT.connect(self.preTem, 'T')  # portT.y -> preTem.T
        self.preTem.connect_port(self.heatPort)  # preTem.port -> heatPort
    
    def step(self, dt):
        """Update with proper connections"""
        # 뷰 팩터 업데이트
        self.FF_i = self.SC
        self.FF_ij = self.SC * (1 - self.tau_FIR)
        
        # 표면 증기압 업데이트 (SurfaceVP 연결)
        self.surfaceVP.T = self.T
        self.surfaceVP.step(dt)  # SurfaceVP 업데이트
        
        # 잠열 계산
        self.L_scr = self.massPort.MV_flow * 2.45e6
        
        if not self.steadystate:
            # 온도 업데이트 (Modelica 방정식과 동일)
            dT_dt = (self.Q_flow + self.L_scr) / (self.rho * self.c_p * self.h * self.A)
            self.T += dT_dt * dt
            
            # Modelica 연결 구조 업데이트
            self.portT.set_expression(self.T)  # Update expression and propagate
    
    def get_temperature(self):
        """Return the current temperature"""
        return self.T
    
    def get_latent_heat_flow(self):
        """Return the latent heat flow"""
        return self.L_scr
    
    def get_radiative_factors(self):
        """Return the radiative view factors"""
        return self.FF_i, self.FF_ij
    
    def set_inputs(self, Q_flow=0.0):
        """
        Set heat flow input
        
        Parameters:
        -----------
        Q_flow : float
            Heat flow rate [W]
        """
        self.Q_flow = Q_flow
        self.heatPort.Q_flow = Q_flow

    def set_screen_closure(self, SC):
        """Set screen closure position [0-1]"""
        self.SC = max(0, min(1, SC))  # 0-1 범위로 제한
        self.FF_i = self.SC
        self.FF_ij = self.SC * (1 - self.tau_FIR)
        
    def update_heat_port(self):
        """Update heat port like Modelica's prescribed temperature"""
        # Modelica의 preTem.T = T 연결 구현
        self.heatPort.T = self.T