import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Components.Greenhouse.BasicComponents.SurfaceVP import SurfaceVP
from Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature import PrescribedTemperature
from Modelica.Blocks.Sources.RealExpression import RealExpression

class Cover:
    """
    온실 커버 컴포넌트 (Modelica Cover.mo와 동일)
    온실 커버의 에너지 밸런스 계산:
    - 현열 유동 (대류, 복사)
    - 응축으로부터의 잠열
    - 흡수된 태양 복사
    """

    def __init__(self, A, phi, rho=2600, c_p=840, h_cov=1e-3,
                 T_start=298.0, steadystate=False):
        """
        Cover 컴포넌트 초기화
        
        Args:
            A (float): 바닥 표면적 [m²]
            phi (float): 지붕 경사 [rad]
            rho (float): 커버 밀도 [kg/m³]
            c_p (float): 비열 [J/(kg·K)]
            h_cov (float): 커버 두께 [m]
            T_start (float): 초기 온도 [K]
            steadystate (bool): 정상상태 초기화 여부
        """
        # 파라미터
        self.A = A                      # 바닥 표면적 [m²]
        self.phi = phi                  # 지붕 경사 [rad]
        self.h_cov = h_cov              # 커버 두께 [m]
        self.rho = rho                  # 커버 밀도 [kg/m³]
        self.c_p = c_p                  # 비열 [J/(kg·K)]
        self.latent_heat_vap = 2.45e6   # 증발 잠열 [J/kg]

        # 옵션
        self.steadystate = steadystate

        # 상태 변수
        self.T = T_start                # 온도 [K]
        self.Q_flow = 0.0               # 순 열유량 [W]
        self.R_SunCov_Glob = 0.0        # 태양 복사 [W/m²]
        self.MV_flow = 0.0              # 수분 유량 [kg/s]

        # 유도 변수
        self.V = self.h_cov * self.A / np.cos(self.phi)  # 체적 [m³]
        self.P_SunCov = 0.0             # 흡수 파워 [W]
        self.L_cov = 0.0                # 잠열 [W]

        # 컴포넌트들
        self.heatPort = HeatPort_a(T_start=T_start)
        self.massPort = WaterMassPort_a()
        self.surfaceVP = SurfaceVP(T=T_start)
        self.preTem = PrescribedTemperature(T_start=T_start)
        
        # RealExpression for port temperature
        self.portT = RealExpression(y=T_start)
        
        # 컴포넌트 연결 (Modelica connect와 동일)
        self.portT.connect(self.preTem, 'T')  # portT.y -> preTem.T
        # preTem.port는 이미 초기화되어 있으므로 직접 연결하지 않음
        self.surfaceVP.port = self.massPort  # surfaceVP.port -> massPort

    def compute_power_input(self):
        """태양 복사로부터 흡수된 파워 계산"""
        self.P_SunCov = self.R_SunCov_Glob * self.A

    def compute_latent_heat(self):
        """응축으로부터의 잠열 계산"""
        self.L_cov = self.MV_flow * self.latent_heat_vap

    def compute_derivatives(self):
        """온도 도함수 계산"""
        if self.steadystate:
            return 0.0
            
        self.compute_power_input()
        self.compute_latent_heat()
        
        # Modelica 방정식: der(T) = 1/(rho*c_p*V)*(Q_flow + P_SunCov + L_cov)
        return (self.Q_flow + self.P_SunCov + self.L_cov) / (self.rho * self.c_p * self.V)

    def step(self, dt):
        """
        한 시간 스텝만큼 시뮬레이션 진행
        
        Args:
            dt (float): 시간 스텝 [s]
        """
        # 온도 업데이트
        dTdt = self.compute_derivatives()
        self.T += dTdt * dt
        
        # 컴포넌트 업데이트
        self.heatPort.T = self.T
        self.surfaceVP.T = self.T
        
        # PrescribedTemperature 업데이트
        self.preTem.update_temperature(self.T)
        
        # RealExpression 업데이트
        self.portT.set_expression(self.T)
        
        return self.T

    def set_inputs(self, Q_flow, R_SunCov_Glob, MV_flow=0.0):
        """
        입력값 설정
        
        Args:
            Q_flow (float): 커버로의 총 열유량 [W]
            R_SunCov_Glob (float): 커버에 대한 전체 태양 복사 [W/m²]
            MV_flow (float): 질량 증기 유량 [kg/s]
        """
        self.Q_flow = Q_flow
        self.R_SunCov_Glob = R_SunCov_Glob
        self.MV_flow = MV_flow
        self.heatPort.Q_flow = Q_flow
