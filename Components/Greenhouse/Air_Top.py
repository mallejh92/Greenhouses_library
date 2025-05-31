import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Components.Greenhouse.BasicComponents.AirVP import AirVP
from Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature import PrescribedTemperature

class Air_Top:
    """
    파이썬으로 재구현한 Greenhouses.Components.Greenhouse.Air_Top 모델
    - 상부 공기 구역의 온도(T)와 상대습도(RH)를 계산
    - Modelica와 동일하게, 정적 방정식으로 온도 계산 (열용량이 작아 fast response 가정)
    - 수증기 질량 보존 방정식을 간략화하여 AirVP 클래스로 대체
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
        self.RH = 0.0                      # 상대습도 (0~1)
        self.w_air = 0.0                   # 공기 중 수증기 비율 [kg_water/kg_dry_air]

        # 3) 포트(Connectors) 생성
        #    - heatPort: 온도(T)와 열유량(Q_flow) 교환용
        #    - massPort: 수증기 압력(VP) 교환용
        self.heatPort = HeatPort_a(T_start=T_start)
        self.massPort = WaterMassPort_a()

        # 4) PrescribedTemperature 블록 생성 & 연결
        #    Modelica: portT → preTem.T → heatPort
        self.preTem = PrescribedTemperature(T_start=T_start)
        self.preTem.connect_port(self.heatPort)

        # 5) 내부 AirVP(수증기 역학) 인스턴스 생성 & 연결
        self.air = AirVP(V_air=self.V, steadystate=steadystateVP)
        self.air.connect(self.massPort)

    def compute_derivatives(self) -> float:
        """
        온도(T)의 미분(dT/dt)을 계산
        - Modelica: rho = density_pT(1e5, heatPort.T)
                    der(T) = Q_flow / (rho * c_p * V)
        - Python: 이상기체 관계식으로 rho 계산 및 미분 산출
        """
        # 1) 밀도를 현재 열 포트의 온도(heatPort.T)에 맞추어 이상기체 식으로 계산
        #    rho = P_atm / (R_a * T_port)
        T_port = self.heatPort.T
        self.rho = self.P_atm / (self.R_a * T_port)

        # 2) 미분 계산
        #    dT/dt = Q_flow / (rho * c_p * V)
        if self.steadystate:
            return 0.0
        else:
            return self.Q_flow / (self.rho * self.c_p * self.V)

    def update_humidity(self):
        """
        수증기(Humidity) 관련 상태 변수 업데이트
        - Modelica:
            w_air = massPort.VP * R_a / ((P_atm - massPort.VP) * R_s)
            RH = relativeHumidity_pTX(P_atm, heatPort.T, {w_air})
        - Python:
            동일한 w_air 식 사용 + Tetens 공식으로 RH 계산
        """
        # 1) 수증기 비율(w_air) 계산
        VP = self.massPort.VP
        if VP < self.P_atm:
            self.w_air = VP * self.R_a / ((self.P_atm - VP) * self.R_s)
        else:
            # 비정상적인 값 방지를 위해, P_atm 이상일 경우 약속된 최대값 부여
            self.w_air = 0.0

        # 2) 포화 증기압(VP_sat) 계산 (Tetens 공식)
        T_C = self.heatPort.T - 273.15
        if T_C + 237.3 != 0:
            VP_sat = 610.78 * np.exp((17.27 * T_C) / (T_C + 237.3))
        else:
            VP_sat = 0.0

        # 3) 상대습도(RH) 산정
        if VP_sat > 0:
            self.RH = np.clip(VP / VP_sat, 0.0, 1.0)
        else:
            self.RH = 0.0

    def step(self, dt: float):
        """
        한 시뮬레이션 스텝만큼 진행
        - dt: 시간 간격 [s]
        1) 내부 AirVP의 수증기 역학 업데이트
        2) 온도 미분 계산 후 적분
        3) 포트 온도(heatPort.T) 동기화
        4) 상대습도(RH) 업데이트
        """
        # 1) AirVP 내부 수증기 역학 업데이트
        #    - massPort.VP는 외부에서 set 해둔 값을 참조함
        #    - 여기서는 AirVP.step(dt)를 호출해 내부 동역학을 수행하도록 함
        self.air.step(dt)

        # 2) 온도 미분(dT/dt) 계산 및 적분
        dTdt = self.compute_derivatives()
        if not self.steadystate:
            # 최대 변화량 제한(필요 시 설정)
            # max_dT_per_step = 1.0  # 예: dt 동안 최대 1K 변화 제한
            # dT = np.sign(dTdt) * min(abs(dTdt)*dt, max_dT_per_step)
            dT = dTdt * dt
            self.T += dT

        # 3) heatPort.T에 내부 상태 T 동기화 (PrescribedTemperature 역할)
        self.preTem.connect_T(self.T)
        self.preTem.calculate()  # 내부적으로 heatPort.T = self.T

        # 4) 상대습도(RH) 업데이트
        self.update_humidity()

    def set_inputs(self, Q_flow: float, VP_in: float = None):
        """
        외부로부터 입력값을 설정
        - Q_flow: 열유입 [W]
        - VP_in: massPort.VP (수증기 압력) [Pa] (필요 시 넘겨줄 것)
        """
        self.Q_flow = Q_flow
        self.heatPort.Q_flow = Q_flow

        # 수증기 압력 입력이 주어지면 massPort.VP에도 반영
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