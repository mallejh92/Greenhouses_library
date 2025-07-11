import numpy as np
from Components.Greenhouse.BasicComponents.AirVP import AirVP
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Modelica.Media.MoistAir.relativeHumidity_pTX import relativeHumidity_pTX

class Air:
    """
    온실 공기 컴포넌트 (Modelica Air.mo와 동일)
    공기에 대한 에너지 및 수분 질량 밸런스 적용
    """
    
    def __init__(self, A, h_Air=4.0, rho=1.2, c_p=1000.0, T_start=298.0, 
                 N_rad=2, steadystate=False, steadystateVP=True):
        """
        Air 컴포넌트 초기화 (Modelica와 동일)
        
        Parameters:
        -----------
        A : float - 온실 바닥 면적 [m²]
        h_Air : float - 주 공기 구역 높이 [m] (기본값=4)
        rho : float - 공기 밀도 [kg/m³] (기본값=1.2, 고정값)
        c_p : float - 비열 [J/(kg·K)] (기본값=1000)
        T_start : float - 초기 온도 [K] (기본값=298)
        N_rad : int - 복사 입력 수 (기본값=2)
        steadystate : bool - 초기화 시 dT/dt=0 설정 (기본값=false)
        steadystateVP : bool - 초기화 시 dVP/dt=0 설정 (기본값=true)
        """
        # 파라미터 (Modelica와 동일)
        self.N_rad = N_rad
        self.rho = rho  # 고정값 (온도 의존성 없음)
        self.c_p = c_p
        self.A = A
        self.h_Air = h_Air
        self.T_start = T_start
        self.steadystate = steadystate
        self.steadystateVP = steadystateVP
        
        # 상수 (Modelica와 동일)
        self.P_atm = 101325.0  # 대기압 [Pa]
        self.R_a = 287.0       # 건조공기 기체상수 [J/(kg·K)]
        self.R_s = 461.5       # 수증기 기체상수 [J/(kg·K)]
        
        # 변수 (Modelica와 동일)
        self.Q_flow = 0.0      # 열유량 [W]
        self.T = T_start       # 온도 [K]
        self.P_Air = 0.0       # 복사 파워 [W]
        self.RH = 0.0          # 상대습도 [0-1]
        self.V = A * h_Air     # 체적 [m³]
        self.w_air = 0.0       # 공기 습도비 (kg water / kg dry air)
        
        # 초기화 플래그
        self._initialization_phase = True
        
        # 연결자 (Modelica와 동일)
        self.heatPort = HeatPort_a(T_start=T_start)
        self.massPort = WaterMassPort_a()
        
        # 복사 입력 (Modelica: HeatFluxVectorInput R_Air_Glob[N_rad])
        self.R_Air_Glob = [0.0] * N_rad  # 단순한 float 리스트
        
        # 서브 컴포넌트 (Modelica와 동일)
        self.airVP = AirVP(V_air=self.V, steadystate=steadystateVP)
        
        # 연결 (Modelica와 동일)
        self.airVP.connect(self.massPort)
    
    def complete_initialization(self):
        """초기화 단계 완료"""
        self._initialization_phase = False
        
    def step(self, dt):
        """
        시뮬레이션 스텝 실행 (Modelica 방정식 구현)
        
        Modelica 방정식:
        - V = A * h_Air
        - heatPort.Q_flow = Q_flow  
        - der(T) = 1/(rho*c_p*V)*(Q_flow + P_Air)
        - w_air = massPort.VP * R_a / (P_atm - massPort.VP) / R_s
        - RH = relativeHumidity_pTX(P_atm, heatPort.T, {w_air})
        """
        # 체적 업데이트 (Modelica: V = A * h_Air)
        self.V = self.A * self.h_Air
        self.airVP.V_air = self.V
        
        # 열 포트 연결 (Modelica: heatPort.Q_flow = Q_flow)
        self.heatPort.Q_flow = self.Q_flow
        self.heatPort.T = self.T
        
        # 복사 파워 계산 (Modelica: P_Air = sum(R_Air_Glob)*A)
        # 원본 Modelica: if cardinality(R_Air_Glob)==0 then R_Air_Glob[i]=0; end if;
        if len(self.R_Air_Glob) == 0:
            self.P_Air = 0.0
        else:
            self.P_Air = sum(self.R_Air_Glob) * self.A
        
        # 온도 미분 (Modelica: der(T) = 1/(rho*c_p*V)*(Q_flow + P_Air))
        if not (self._initialization_phase and self.steadystate):
            if self.rho > 0 and self.c_p > 0 and self.V > 0:
                dT_dt = (self.Q_flow + self.P_Air) / (self.rho * self.c_p * self.V)
                self.T += dT_dt * dt
        
        # AirVP 컴포넌트 업데이트
        self.airVP.T = self.T
        self.airVP.step(dt)
        
        # 습도 계산 업데이트
        self._update_humidity()
    
    def _update_humidity(self):
        """
        습도 계산 업데이트 (Modelica 방정식과 동일)
        - w_air = massPort.VP * R_a / (P_atm - massPort.VP) / R_s
        - RH = relativeHumidity_pTX(P_atm, heatPort.T, {w_air})
        """
        VP = self.massPort.VP
        
        if VP is None or VP <= 0:
            self.w_air = 0.0
            self.RH = 0.0
            return
            
        # VP가 대기압보다 작도록 보장
        if VP >= self.P_atm:
            VP = 0.99 * self.P_atm
            self.massPort.VP = VP
        
        # 습도비 계산 (Modelica 방정식)
        if (self.P_atm - VP) > 0:
            self.w_air = VP * self.R_a / ((self.P_atm - VP) * self.R_s)
        else:
            self.w_air = 0.0
        
        # 상대습도 계산 (Modelica 방정식)
        try:
            X = [self.w_air]
            self.RH = relativeHumidity_pTX(self.P_atm, self.T, X)
            self.RH = max(0.0, min(1.0, self.RH))
        except:
            self.RH = 0.0
    
    def set_inputs(self, Q_flow, R_Air_Glob=None):
        """입력값 설정 (Modelica와 동일)"""
        self.Q_flow = Q_flow
        
        if R_Air_Glob is not None:
            if isinstance(R_Air_Glob, (list, tuple)):
                self.R_Air_Glob = [float(v) for v in R_Air_Glob]
            else:
                self.R_Air_Glob = [float(R_Air_Glob)]
        else:
            # cardinality=0인 경우 모든 값을 0으로 설정 (Modelica와 동일)
            self.R_Air_Glob = [0.0] * self.N_rad
    
    def get_state(self):
        """현재 상태 반환"""
        return {
            'T': self.T,
            'RH': self.RH,
            'VP': self.massPort.VP,
            'w_air': self.w_air,
            'Q_flow': self.Q_flow,
            'P_Air': self.P_Air,
            'V': self.V
        }