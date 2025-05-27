from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a

class Layer:
    def __init__(self, rho, c_p, A, V=1.0, steadystate=True, T_init=298.0):
        # Parameters
        self.rho = rho                  # 밀도 [kg/m^3]
        self.c_p = c_p                  # 비열 [J/kg·K]
        self.A = A                      # 면적 [m^2]
        self.V = V                      # 부피 [m^3]
        self.steadystate = steadystate  # 정상상태 초기화 여부
        self.T = T_init                 # 초기 온도 [K]

        # State
        self.Q_flow = 0.0               # 열유속 [W]
        self.heatPort = HeatPort_a(T_start=T_init)

    def set_heat_flow(self, Q_flow):
        """외부 열유속을 설정 (W)"""
        self.Q_flow = Q_flow
        self.heatPort.Q_flow = Q_flow

    def update(self, dt):
        """시간 dt만큼 에너지 균형으로 온도 업데이트"""
        if not self.steadystate:
            dT_dt = self.Q_flow / (self.rho * self.c_p * self.V)
            self.T += dT_dt * dt
            self.heatPort.T = self.T
        else:
            self.heatPort.T = self.T

    def get_temperature(self):
        return self.T
