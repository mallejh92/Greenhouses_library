import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature import PrescribedTemperature
from Modelica.Blocks.Sources.RealExpression import RealExpression
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Components.Greenhouse.BasicComponents.SurfaceVP import SurfaceVP

class ThermalScreen:
    def __init__(self, A, SC=0, rho=0.2e3, c_p=1.8e3, h=0.35e-3, tau_FIR=0.15,
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
            Material density [kg/m³] 
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
        """
        # Parameters 
        self.A = A
        self.SC = SC
        self.rho = rho  # 0.2e3 kg/m³ 
        self.c_p = c_p  # 1.8e3 J/(kg·K) 
        self.h = h
        self.tau_FIR = tau_FIR
        self.steadystate = steadystate
        
        # State variables
        self.T = T_start  # Temperature [K]
        self.Q_flow = 0.0  # Heat flow rate [W]
        self.L_scr = 0.0  # Latent heat flow [W]
        
        # View factors
        self.FF_i = SC  # View factor for radiation
        self.FF_ij = SC * (1 - tau_FIR)  # View factor for FIR
                
        # Components 
        self.heatPort = HeatPort_a(T_start=T_start)
        self.massPort = WaterMassPort_a()
        self.surfaceVP = SurfaceVP(T=T_start)
        
        self.preTem = PrescribedTemperature(T_start=T_start)
        self.portT = RealExpression(y=T_start)
        
        # 컴포넌트 연결 (Modelica connect와 동일)
        self.portT.connect(self.preTem, 'T')  # portT.y -> preTem.T
        # preTem.port는 이미 초기화되어 있으므로 직접 연결하지 않음
        self.surfaceVP.port = self.massPort  # surfaceVP.port -> massPort

        # 초기 steady state 처리
        if self.steadystate:
            # der(T) = 0 조건 적용
            self.Q_flow = 0.0
            self.L_scr = 0.0
        
        # 초기 연결 설정
        self._setup_connections()

    def _setup_connections(self):
        """Set up internal connections like in Modelica"""
        # Modelica 원본과 동일한 연결 구조
        self.surfaceVP.port = self.massPort
        self.surfaceVP.T = self.T
        
        # PrescribedTemperature 연결
        self.portT.connect(self.preTem, 'T')  # portT.y -> preTem.T
        # preTem.port는 이미 초기화되어 있으므로 직접 연결하지 않음
    
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
            # 온도 업데이트 (Modelica 방정식과 정확히 일치)
            # der(T) = 1/(rho*c_p*h*A)*(Q_flow + L_scr)
            dT_dt = (self.Q_flow + self.L_scr) / (self.rho * self.c_p * self.h * self.A)
            
            # 온도 변화율 제한 (물리적 한계 적용)
            max_dT_dt = 1.0  # 최대 온도 변화율 [K/s] - 더 보수적인 값
            if abs(dT_dt) > max_dT_dt:
                dT_dt = max_dT_dt if dT_dt > 0 else -max_dT_dt
            
            # 온도 업데이트
            new_T = self.T + dT_dt * dt
            
            # 온도 범위 제한 (물리적으로 가능한 범위)
            min_T = 273.15 - 50  # -50°C
            max_T = 273.15 + 100  # +100°C
            
            if new_T < min_T:
                new_T = min_T
            elif new_T > max_T:
                new_T = max_T
            
            self.T = new_T
            
            # 디버깅 출력
            # print(f"ThermalScreen: T={self.T-273.15:.1f}°C, Q_flow={self.Q_flow:.1f}W, L_scr={self.L_scr:.1f}W, dT_dt={dT_dt:.3f}K/s")
            
            # Modelica 연결 구조 업데이트
            self.portT.set_expression(self.T)  # Update expression and propagate
        else:
            # Steady state: 온도 변화 없음
            pass
    
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