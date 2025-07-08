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
        self.RH = 0.0                      # 상대습도 (0~1) - 90%로 설정
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
        
        Modelica 원본: "computed by static equation because of its small heat capacity"
        - Modelica 컴파일러는 작은 열용량으로 인해 이 컴포넌트를 자동으로 정적 방정식으로 처리
        - Python에서는 수동으로 이 동작을 구현
        """
        # 1) Modelica와 동일하게 Air_pT.density_pT 사용
        self.rho = density_pT(1e5, self.heatPort.T)

        # 2) 상부공기의 열용량 계산
        thermal_mass = self.rho * self.c_p * self.V  # [J/K]
        
        # 3) Modelica 스타일: 열적 시정수가 매우 작은 경우 정적 방정식 사용
        # 실제 온실에서 상부공기는 1-5초 내에 평형에 도달
        characteristic_heat_transfer = 10.0 * self.A  # [W/K] 특성 열전달
        thermal_time_constant = thermal_mass / characteristic_heat_transfer if characteristic_heat_transfer > 0 else 1.0
        
        # 4) Modelica처럼 작은 시정수에 대해 준정적 처리
        if thermal_time_constant < 2.0:  # 2초 미만이면 준정적 처리
            # 정적 평형 온도 계산 (Q_flow = 0일 때의 평형 온도)
            if abs(self.Q_flow) > 1e-6:  # 열유입이 있으면
                # 매우 빠른 응답으로 근사적 평형 상태로 이동
                # Modelica의 "정적 방정식" 개념 구현
                equilibrium_response_rate = 5.0  # [1/s] 평형으로의 수렴 속도
                return equilibrium_response_rate * self.Q_flow / thermal_mass
            else:
                return 0.0  # 열유입이 없으면 변화 없음
        else:
            # 일반적인 동적 방정식 사용
            if self.steadystate:
                return 0.0
            else:
                if thermal_mass == 0:
                    return 0.0
                
                dT_dt = self.Q_flow / thermal_mass
                
                # 물리적 합리성 제한
                max_rate = 5.0  # 최대 5°C/s 변화율
                if abs(dT_dt) > max_rate:
                    dT_dt = np.sign(dT_dt) * max_rate
                
                return dT_dt

    def update_humidity(self):
        """
        수증기(Humidity) 관련 상태 변수 업데이트
        - Modelica:
            w_air = massPort.VP * R_a / (P_atm - massPort.VP) / R_s
            RH = Modelica.Media.Air.MoistAir.relativeHumidity_pTX(P_atm, heatPort.T, {w_air})
        """
        # Added check for valid VP and T before calculation
        VP = self.massPort.VP
        if VP is None or self.heatPort.T == 0 or VP >= self.P_atm:
            self.w_air = 0.0
            self.RH = 0.0
            return

        # 1) 수증기 비율(w_air) 계산 (Modelica와 동일)
        self.w_air = VP * self.R_a / ((self.P_atm - VP) * self.R_s)

        # 2) Modelica와 동일하게 relativeHumidity_pTX 함수 사용
        X = [self.w_air]  # w_air를 직접 전달
        self.RH = relativeHumidity_pTX(self.P_atm, self.heatPort.T, X)

    def step(self, dt: float):
        """
        시뮬레이션 한 스텝 진행
        
        상부공기의 특별한 처리:
        - 열적 시정수가 매우 작아서 dt≥2초에서 수치적 불안정성 발생
        - 적응적 시간 간격을 사용하여 안정성 확보
        """
        # 온도 업데이트
        if not self.steadystate:
            dT_dt = self.compute_derivatives()
            
            # 상부공기의 열적 시정수 계산 [s]
            thermal_mass = self.rho * self.c_p * self.V
            if thermal_mass > 0:
                typical_heat_transfer_coeff = 10.0  # [W/(m²·K)]
                thermal_time_constant = thermal_mass / (typical_heat_transfer_coeff * self.A)
            else:
                thermal_time_constant = 1.0  # 기본값
            
            # CFL 조건 기반 최대 허용 시간 간격 계산
            # 수치적 안정성을 위해 열적 시정수의 20% 이하로 제한
            max_stable_dt = 0.2 * thermal_time_constant
            
            # 적응적 시간 간격 사용
            if dt > max_stable_dt and max_stable_dt > 0.1:
                # 큰 시간 간격을 여러 개의 작은 간격으로 분할
                n_substeps = int(np.ceil(dt / max_stable_dt))
                sub_dt = dt / n_substeps
                
                # 여러 하위 스텝으로 나누어 계산
                for _ in range(n_substeps):
                    dT_dt_sub = self.compute_derivatives()
                    
                    # 온도 변화량 계산 및 제한
                    dT_sub = dT_dt_sub * sub_dt
                    max_dT_per_substep = 0.5  # K - 하위 스텝당 최대 변화량
                    dT_sub = np.clip(dT_sub, -max_dT_per_substep, max_dT_per_substep)
                    
                    self.T += dT_sub
                    # 온도 범위 제한 (-20°C ~ 80°C)
                    self.T = np.clip(self.T, 253.15, 353.15)
                    
                    # 포트 온도 중간 업데이트 (다음 하위 스텝을 위해)
                    self.heatPort.T = self.T
                    self.preTem.T = self.T
            else:
                # 안정한 시간 간격인 경우 직접 계산
                dT = dT_dt * dt
                max_dT_per_step = 2.0  # K - 일반 스텝당 최대 변화량 (증가)
                dT = np.clip(dT, -max_dT_per_step, max_dT_per_step)
                
                self.T += dT
                # 온도 범위 제한 (-20°C ~ 80°C)
                self.T = np.clip(self.T, 253.15, 353.15)
        
        # 포트 온도 최종 업데이트
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