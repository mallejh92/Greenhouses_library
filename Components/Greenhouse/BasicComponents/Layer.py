from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature import PrescribedTemperature
import numpy as np

class Layer:
    def __init__(self, rho, c_p, A, V=1.0, steadystate=True, T_init=293.15):
        """
        Basic "리버시블" 열 저장소(온도 상승 가능) Layer

        Parameters:
        -----------
        rho : float
            밀도 [kg/m^3]
        c_p : float
            비열 [J/(kg·K)]
        A : float
            면적 [m^2]
        V : float
            부피 [m^3]
        steadystate : bool
            초기화 후 정상상태로 두어 온도 변화 안 시킴 (Modelica와 동일하게 True가 기본값)
        T_init : float
            초기 온도 [K]
        """
        # Parameters
        self.rho = rho                  # 밀도 [kg/m^3]
        self.c_p = c_p                  # 비열 [J/(kg·K)]
        self.A = A                      # 면적 [m^2]
        self.V = V                      # 부피 [m^3]
        self.steadystate = steadystate  # 정상상태 초기화 여부

        # State variables
        self.T = T_init                 # 초기 온도 [K]
        self.Q_flow = 0.0               # 외부에서 주는 열유속 [W]

        # Components (Modelica와 동일하게)
        self.heatPort = HeatPort_a(T_start=self.T)    # 열 포트 (포트 T, Q_flow 속성)
        self.preTem = PrescribedTemperature(T_start=self.T)  # 포트에 연결하여 T를 설정하게 함
        self.preTem.connect_port(self.heatPort)

    def set_heat_flow(self, Q_flow):
        """
        외부 열유속 설정 (Modelica의 Q_flow와 동일)

        Parameters:
        -----------
        Q_flow : float
            이 레이어에 들어오는 열유속 [W]
        """
        self.Q_flow = Q_flow
        self.heatPort.Q_flow = Q_flow

    def update(self, dt):
        """
        시간 dt만큼 에너지 균형으로 온도 업데이트 (Modelica의 der(T) 방정식과 동일)

        Parameters:
        -----------
        dt : float
            타임스텝 [s]
        """
        if not self.steadystate:
            # Modelica의 der(T) = 1/(rho*c_p*V)*(Q_flow) 방정식과 동일
            dT_dt = self.Q_flow / (self.rho * self.c_p * self.V)
            
            # 온도 변화 계산
            new_T = self.T + dT_dt * dt
            
            # 물리적으로 의미 있는 온도 범위로 제한 (절대 영도 이상)
            self.T = np.clip(new_T, 173.15, 373.15)
            
            # 포트 온도 업데이트
            self.preTem.connect_T(self.T)

    def get_temperature(self):
        """
        현재 온도 반환 [K]
        """
        return self.T
