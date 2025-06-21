import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Components.Greenhouse.BasicComponents.SurfaceVP import SurfaceVP
from Interfaces.Heat.HeatFluxVectorInput import HeatFluxVectorInput

class Canopy:
    """
    Python version of the Greenhouses.Components.Greenhouse.Canopy model.
    Computes canopy temperature based on energy balance including:
    - Long-wave radiation and convection (Q_flow)
    - Short-wave solar radiation (R_Can_Glob)
    - Latent heat from transpiration (L_can)
    
    Modelica 원본과 동일하게:
    - FF는 매 스텝마다 equation 섹션에서 계산
    - R_Can_Glob은 HeatFluxVectorInput으로 처리
    - 포트 연결은 직접 연결 방식 사용
    - massPort.MV_flow는 외부 입력과 동기화
    - steadystate는 초기화 시점에만 적용
    """

    def __init__(self, A, LAI=1.0, Cap_leaf=1200, N_rad=2,
                 T_start=298.0, steadystate=False):
        # Parameters (Modelica parameter와 동일)
        self.A = A                  # Greenhouse floor surface area [m²]
        self.LAI = LAI              # Leaf Area Index
        self.Cap_leaf = Cap_leaf    # Heat capacity per m² of leaf [J/K]
        self.N_rad = N_rad          # Number of radiation sources
        self.latent_heat_vap = 2.45e6  # Latent heat of vaporization [J/kg]

        # Initialization parameters (Modelica parameter와 동일)
        self.T_start = T_start      # Initial temperature [K]
        self.steadystate = steadystate  # Steady state initialization option
        self._is_initialized = False  # 초기화 완료 여부 추적

        # State variables (Modelica variable와 동일)
        self.T = T_start            # Temperature [K]
        self.Q_flow = 0.0           # Net sensible heat from surroundings [W]
        self.P_Can = 0.0            # Radiation power absorbed [W]
        self.L_can = 0.0            # Latent heat transfer [W]
        self.FF = 0.0               # Foliage factor

        # Input connectors (Modelica connector와 동일)
        self.R_Can_Glob = HeatFluxVectorInput([0.0] * N_rad)  # Short-wave radiation inputs
        self.massPort_MV_flow = 0.0  # Moisture mass flow rate [kg/s]

        # Ports (Modelica connector와 동일)
        self.heatPort = HeatPort_a(T_start=T_start)  # Heat port
        self.massPort = WaterMassPort_a()            # Mass port
        self.surfaceVP = SurfaceVP(T=T_start)        # Surface vapor pressure
        
        # Connect ports (Modelica connect 구문과 동일)
        self.surfaceVP.port = self.massPort

    def compute_derivatives(self):
        """
        Modelica equation 섹션과 동일하게 구현:
        1. FF 계산
        2. R_Can_Glob 처리
        3. P_Can 계산
        4. L_can 계산
        5. 온도 변화율 계산
        
        Modelica의 initial equation 섹션과 동일하게:
        - steadystate가 True이고 초기화 중일 때만 dT/dt = 0
        """
        # 초기화 중이고 steadystate 옵션이 켜져 있을 때만 dT/dt = 0
        if self.steadystate and not self._is_initialized:
            self._is_initialized = True  # 초기화 완료 표시
            return 0.0

        # R_Can_Glob 처리 (Modelica cardinality 체크와 동일)
        if isinstance(self.R_Can_Glob, list):
            # list인 경우 HeatFluxVectorInput으로 변환
            self.R_Can_Glob = HeatFluxVectorInput(self.R_Can_Glob)
        elif len(self.R_Can_Glob) == 0:
            self.R_Can_Glob = HeatFluxVectorInput([0.0] * self.N_rad)
        
        # P_Can 계산 (Modelica equation 섹션과 동일)
        if hasattr(self.R_Can_Glob, 'get_float_values'):
            # HeatFluxVectorInput의 경우
            float_values = self.R_Can_Glob.get_float_values()
            # 안전하게 float 값으로 변환
            safe_values = []
            for v in float_values:
                if hasattr(v, 'value'):
                    safe_values.append(v.value)
                else:
                    safe_values.append(float(v))
            self.P_Can = sum(safe_values) * self.A
        else:
            # list인 경우 직접 합계 계산
            self.P_Can = sum(self.R_Can_Glob) * self.A
        
        # L_can 계산 (Modelica equation 섹션과 동일)
        # massPort.MV_flow를 직접 사용 (Modelica와 동일)
        self.L_can = self.massPort.MV_flow * self.latent_heat_vap
        
        # 온도 변화율 계산 (Modelica equation 섹션과 동일)
        return (self.Q_flow + self.P_Can + self.L_can) / (self.Cap_leaf * self.LAI * self.A)

    def step(self, dt):
        """
        시간 적분 수행 (Modelica와 동일)
        - 온도 적분
        - 포트 업데이트
        """
        # FF 계산을 먼저 수행 (Modelica equation 섹션과 동일)
        self.FF = 1 - np.exp(-0.94 * self.LAI)
        
        # 온도 적분 - 큰 변화 억제를 위해 제한 적용
        dTdt = self.compute_derivatives()
        max_dT = 5.0  # 한 스텝당 최대 온도 변화 [K]
        dT = dTdt * dt
        if abs(dT) > max_dT:
            dT = np.sign(dT) * max_dT
        self.T += dT
        
        # 포트 업데이트 (Modelica connect 구문과 동일)
        self.heatPort.T = self.T
        self.heatPort.Q_flow = self.Q_flow  # 직접 연결
        self.surfaceVP.T = self.T
        
        return self.T

    def set_inputs(self, Q_flow, R_Can_Glob, MV_flow=0.0):
        """
        외부 입력 설정 (Modelica와 동일)
        - Q_flow: 열유량
        - R_Can_Glob: 단파 복사 입력
        - MV_flow: 수증기 질량 유량 (massPort.MV_flow와 동기화)
        """
        self.Q_flow = Q_flow
        if isinstance(R_Can_Glob, (list, tuple)):
            self.R_Can_Glob = HeatFluxVectorInput(R_Can_Glob)
        # massPort.MV_flow를 직접 업데이트 (Modelica와 동일)
        self.massPort.MV_flow = MV_flow
        self.massPort_MV_flow = MV_flow  # 내부 변수도 동기화
