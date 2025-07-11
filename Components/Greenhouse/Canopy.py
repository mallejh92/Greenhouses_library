import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Components.Greenhouse.BasicComponents.SurfaceVP import SurfaceVP
from Interfaces.Heat.HeatFluxVectorInput import HeatFluxVectorInput

class Canopy:
    """
    온실 캐노피 컴포넌트 (Modelica Canopy.mo와 동일)
    에너지 밸런스 기반 캐노피 온도 계산:
    - 장파 복사 및 대류 (Q_flow)
    - 단파 태양 복사 (R_Can_Glob)
    - 증발산 잠열 (L_can)
    """

    def __init__(self, A, LAI=1.0, Cap_leaf=1200, N_rad=2,
                 T_start=298.0, steadystate=False):
        # 파라미터 (Modelica parameter와 동일)
        self.A = A                  # 온실 바닥 면적 [m²]
        self.LAI = LAI              # 엽면적지수
        self.Cap_leaf = Cap_leaf    # 잎 단위면적당 열용량 [J/K]
        self.N_rad = N_rad          # 복사 소스 수
        self.latent_heat_vap = 2.45e6  # 증발 잠열 [J/kg]

        # 초기화 파라미터 (Modelica parameter와 동일)
        self.T_start = T_start      # 초기 온도 [K]
        self.steadystate = steadystate  # 정상상태 초기화 옵션
        self._is_initialized = False  # 초기화 완료 여부

        # 상태 변수 (Modelica variable와 동일)
        self.T = T_start            # 온도 [K]
        self.Q_flow = 0.0           # 주변으로부터의 현열 [W]
        self.P_Can = 0.0            # 흡수된 복사 파워 [W]
        self.L_can = 0.0            # 잠열 전달 [W]
        self.FF = 0.0               # 엽면적 계수

        # 입력 연결자 (Modelica connector와 동일)
        self.R_Can_Glob = HeatFluxVectorInput([0.0] * N_rad)  # 단파 복사 입력
        self.massPort_MV_flow = 0.0  # 수증기 질량 유량 [kg/s]

        # 포트 (Modelica connector와 동일)
        self.heatPort = HeatPort_a(T_start=T_start)  # 열 포트
        self.massPort = WaterMassPort_a()            # 질량 포트
        self.surfaceVP = SurfaceVP(T=T_start)        # 표면 증기압
        
        # 포트 연결 (Modelica connect 구문과 동일)
        self.surfaceVP.port = self.massPort

    def compute_derivatives(self):
        """
        Modelica equation 섹션 구현:
        1. FF 계산
        2. R_Can_Glob 처리
        3. P_Can 계산
        4. L_can 계산
        5. 온도 변화율 계산
        """
        # 초기화 중이고 steadystate 옵션이 켜져 있을 때만 dT/dt = 0
        if self.steadystate and not self._is_initialized:
            self._is_initialized = True
            return 0.0

        # R_Can_Glob 처리 (Modelica cardinality 체크와 동일)
        if isinstance(self.R_Can_Glob, list):
            self.R_Can_Glob = HeatFluxVectorInput(self.R_Can_Glob)
        elif len(self.R_Can_Glob) == 0:
            self.R_Can_Glob = HeatFluxVectorInput([0.0] * self.N_rad)
        
        # P_Can 계산 (Modelica equation 섹션과 동일)
        if hasattr(self.R_Can_Glob, 'get_float_values'):
            float_values = self.R_Can_Glob.get_float_values()
            self.P_Can = sum(float_values) * self.A
        else:
            self.P_Can = sum(self.R_Can_Glob) * self.A
        
        # L_can 계산 (Modelica equation 섹션과 동일)
        self.L_can = self.massPort.MV_flow * self.latent_heat_vap
        
        # 온도 변화율 계산 (Modelica equation 섹션과 동일)
        return (self.Q_flow + self.P_Can + self.L_can) / (self.Cap_leaf * self.LAI * self.A)

    def step(self, dt):
        """
        시간 적분 수행 (Modelica와 동일)
        """
        # FF 계산 (Modelica equation 섹션과 동일)
        self.FF = 1 - np.exp(-0.94 * self.LAI)
        
        # 온도 적분 - 안정성을 위해 변화량 제한
        dTdt = self.compute_derivatives()
        max_dT = 5.0  # 한 스텝당 최대 온도 변화 [K]
        dT = dTdt * dt
        if abs(dT) > max_dT:
            dT = np.sign(dT) * max_dT
        self.T += dT
        
        # 포트 업데이트 (Modelica connect 구문과 동일)
        self.heatPort.T = self.T
        self.heatPort.Q_flow = self.Q_flow
        self.surfaceVP.T = self.T
        
        return self.T

    def set_inputs(self, Q_flow, R_Can_Glob, MV_flow=0.0):
        """
        외부 입력 설정 (Modelica와 동일)
        """
        self.Q_flow = Q_flow
        if isinstance(R_Can_Glob, (list, tuple)):
            self.R_Can_Glob = HeatFluxVectorInput(R_Can_Glob)
        
        # massPort.MV_flow 직접 업데이트 (Modelica와 동일)
        self.massPort.MV_flow = MV_flow
        self.massPort_MV_flow = MV_flow
