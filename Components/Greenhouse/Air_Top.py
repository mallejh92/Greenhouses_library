import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Components.Greenhouse.BasicComponents.AirVP import AirVP
from Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature import PrescribedTemperature
from Modelica.Media.MoistAir.relativeHumidity_pTX import relativeHumidity_pTX
from Modelica.Media.Air.ReferanceAir.Air_pT.density_pT import density_pT

class Air_Top:
    """
    파이썬으로 재구현한 Greenhouses.Components.Greenhouse.Air_Top 모델
    - 상부 공기 구역의 온도(T)와 상대습도(RH)를 계산
    - Modelica와 동일하게, 정적 방정식으로 온도 계산 (열용량이 작아 fast response 가정)
    - 수증기 질량 보존은 AirVP 컴포넌트를 통해 처리
    """

    def __init__(self,
                 A: float = 1e3,
                 h_Top: float = 1.0,
                 T_start: float = 298.0,
                 steadystate: bool = False,
                 steadystateVP: bool = True,
                 c_p: float = 1e3):
        """
        매개변수:
        ----------
        A : float
            온실 바닥 면적 [m²]
        h_Top : float
            상부 공기 구역 높이 [m]
        T_start : float
            초기 온도 [K]
        steadystate : bool
            True이면 초기화 시 온도 미분을 0으로 설정
        steadystateVP : bool
            True이면 초기화 시 VP 미분을 0으로 설정
        c_p : float
            공기의 비열 [J/(kg·K)]
        """

        # 1) 파라미터 저장
        self.A = A
        self.h_Top = h_Top
        self.T = T_start
        self.steadystate = steadystate
        self.steadystateVP = steadystateVP
        self.c_p = c_p

        # 2) 상태 변수 & 상수 초기화
        self.Q_flow = 0.0                  # 열유입(Heat flow rate) [W]
        self.V = A * h_Top                 # 부피 [m³]
        self.P_atm = 101325.0              # 대기압 [Pa]
        self.R_a = 287.0                   # 건조 공기 기체 상수 [J/(kg·K)]
        self.R_s = 461.5                   # 수증기 기체 상수 [J/(kg·K)]
        self.rho = 0.0                     # 공기 밀도 [kg/m³] (step() 시 계산)
        self.RH = 0.9                      # 상대습도 (0~1) - 90%로 설정
        self.w_air = 0.0                   # 공기 중 수증기 비율 [kg_water/kg_dry_air]

        # 3) 포트(Connectors) 생성
        self.heatPort = HeatPort_a(T_start=T_start)
        self.massPort = WaterMassPort_a()

        # 4) PrescribedTemperature 블록 생성 & 연결
        self.preTem = PrescribedTemperature(T_start=T_start)
        self.preTem.connect_port(self.heatPort)

        # 5) AirVP 컴포넌트 생성 & 연결 (Modelica 모델과 동일)
        self.air = AirVP(V_air=self.V, steadystate=steadystateVP)
        self.air.connect(self.massPort)

    def compute_derivatives(self) -> float:
        """
        온도(T)의 미분(dT/dt)을 계산
        - Modelica: rho = Modelica.Media.Air.ReferenceAir.Air_pT.density_pT(1e5, heatPort.T)
                    der(T) = Q_flow / (rho * c_p * V)
        """
        # 1) Modelica와 동일하게 Air_pT.density_pT 사용
        self.rho = density_pT(1e5, self.heatPort.T)

        # 2) 미분 계산
        if self.steadystate:
            return 0.0
        else:
            return self.Q_flow / (self.rho * self.c_p * self.V)

    def update_humidity(self):
        """
        수증기(Humidity) 관련 상태 변수 업데이트
        - Modelica:
            w_air = massPort.VP * R_a / (P_atm - massPort.VP) / R_s
            RH = Modelica.Media.Air.MoistAir.relativeHumidity_pTX(P_atm, heatPort.T, {w_air})
        """
        # 1) 수증기 비율(w_air) 계산 (Modelica와 동일)
        VP = self.massPort.VP
        if VP < self.P_atm:
            self.w_air = VP * self.R_a / ((self.P_atm - VP) * self.R_s)
        else:
            self.w_air = 0.0

        # 2) Modelica와 동일하게 relativeHumidity_pTX 함수 사용
        X = [self.w_air]  # w_air를 직접 전달
        self.RH = relativeHumidity_pTX(self.P_atm, self.heatPort.T, X)

    def step(self, dt: float):
        """
        시뮬레이션 한 스텝 진행
        """
        # 온도 업데이트
        if not self.steadystate:
            dT = self.compute_derivatives()
            
            # 수치적 안정성을 위한 온도 변화율 제한 (한 스텝당 최대 5°C 변화)
            max_dT_per_step = 5.0  # K
            dT_limited = np.clip(dT * dt, -max_dT_per_step, max_dT_per_step)
            
            self.T += dT_limited
            # 온도 범위 제한 (0°C ~ 60°C)
            self.T = np.clip(self.T, 253.15, 333.15)
        
        # 포트 온도 업데이트
        self.heatPort.T = self.T
        self.preTem.T = self.T
        
        # AirVP 컴포넌트 업데이트 (Modelica 모델과 동일)
        self.air.step(dt)

        # 상대습도(RH) 업데이트
        self.update_humidity()

    def set_inputs(self, Q_flow: float, VP_in: float = None):
        """
        외부로부터 입력값을 설정
        - Q_flow: 열유입 [W]
        - VP_in: massPort.VP (수증기 압력) [Pa]
        """
        self.Q_flow = Q_flow
        self.heatPort.Q_flow = Q_flow

        if VP_in is not None:
            self.massPort.VP = VP_in

    def get_state(self) -> dict:
        """
        현재 상태를 딕셔너리 형태로 반환
        """
        return {
            'T_air_top': self.T,         # 현재 온도 [K]
            'RH_air_top': self.RH,       # 상대습도 [0~1]
            'VP_air_top': self.massPort.VP,  # 수증기 압력 [Pa]
            'w_air': self.w_air,         # 수증기 비율 [kg/kg]
            'rho': self.rho              # 공기 밀도 [kg/m³]
        }