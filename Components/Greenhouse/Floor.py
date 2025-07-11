import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Heat.HeatFluxVectorInput import HeatFluxVectorInput

class Floor:
    """
    온실 바닥 컴포넌트 (Modelica Floor.mo와 동일)
    에너지 밸런스 기반 바닥 온도 계산:
    - 현열 유동 (heatPort를 통한 모든 유동)
    - 태양 및 보조 조명으로부터의 단파 복사
    """

    def __init__(self, A, rho=1.0, c_p=2e6, V=0.01, T_start=298.15, steadystate=False, N_rad=2):
        """
        Floor 모델 초기화
        
        Args:
            A (float): 바닥 표면적 [m²]
            rho (float): 밀도 [kg/m³]
            c_p (float): 비열 [J/(kg·K)]
            V (float): 체적 [m³]
            T_start (float): 초기 온도 [K]
            steadystate (bool): 정상상태 초기화 여부
            N_rad (int): 단파 복사 입력 수 (1: 태양만, 2: 태양+조명)
        """
        # 파라미터 (Modelica parameter와 동일)
        self.A = A
        self.rho = rho
        self.c_p = c_p
        self.V = V
        self.steadystate = steadystate
        self.N_rad = N_rad
        self._is_initialized = False  # 초기화 완료 여부

        # 상태 변수 (Modelica variable와 동일)
        self.T = T_start          # 온도 [K]
        self.Q_flow = 0.0         # 현열 유량 [W]
        self.P_Flr = 0.0          # 바닥으로의 총 단파 파워 [W]

        # 열 포트 (Modelica HeatPort_a와 동일)
        self.heatPort = HeatPort_a(T_start=T_start)

        # 복사 입력 (Modelica HeatFluxVectorInput와 동일)
        self.R_Flr_Glob = HeatFluxVectorInput([0.0] * N_rad)

    def set_inputs(self, Q_flow=0.0, R_Flr_Glob=None):
        """
        바닥 입력값 설정
        
        Args:
            Q_flow (float): heatPort를 통한 현열 유량 [W]
            R_Flr_Glob (list): 단파 복사 입력 [W/m²]
        """
        # 현열 입력
        self.Q_flow = Q_flow
        self.heatPort.Q_flow = Q_flow

        # 단파 복사 벡터 입력 (Modelica cardinality 체크와 동일)
        if R_Flr_Glob is not None:
            if len(R_Flr_Glob) != self.N_rad:
                raise ValueError(f"R_Flr_Glob 길이는 {self.N_rad}이어야 함")
            self.R_Flr_Glob = HeatFluxVectorInput(R_Flr_Glob)
        else:
            # cardinality = 0인 경우: 0으로 설정 (Modelica와 동일)
            self.R_Flr_Glob = HeatFluxVectorInput([0.0] * self.N_rad)

    def step(self, dt: float) -> None:
        """
        바닥 상태 업데이트 (Modelica equation 섹션과 동일)
        
        Args:
            dt (float): 시간 스텝 [s]
        """
        # P_Flr 계산 (Modelica: P_Flr = sum(R_Flr_Glob)*A)
        if hasattr(self.R_Flr_Glob, 'values') and self.R_Flr_Glob.values:
            self.P_Flr = sum(self.R_Flr_Glob.values) * self.A
        else:
            self.P_Flr = 0.0
        
        # 온도 업데이트 (Modelica: der(T) = 1/(rho*c_p*V)*(Q_flow + P_Flr))
        # initial equation: if steadystate then der(T)=0; end if;
        if self.steadystate and not self._is_initialized:
            # 초기화 시점에서만 der(T) = 0 적용
            self._is_initialized = True
            # 온도 변화 없음
        else:
            # 정상적인 온도 적분
            dT = (self.Q_flow + self.P_Flr) / (self.rho * self.c_p * self.V)
            self.T += dT * dt
        
        # heatPort 온도 동기화 (Modelica connect와 동일)
        self.heatPort.T = self.T
        
        return self.T

    def get_temperature(self):
        """현재 바닥 온도 반환 [K]"""
        return self.T