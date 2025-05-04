class AirVP:
    def __init__(self, V_air=1e3, VP_start=0.04e5, steadystate=True, T=291):
        # Parameters
        self.V_air = V_air              # 공기 체적 [m^3]
        self.VP = VP_start              # 초기 수증기압 [Pa]
        self.steadystate = steadystate
        self.T = T                      # 공기 온도 [K]

        # Constants
        self.R = 8314                   # 기체 상수 [J/(kmol·K)]
        self.M_H = 18e-3                # 수증기의 몰 질량 [kg/mol]
        self.MV_flow = 0.0              # 수증기 질량 유량 [kg/s], 외부 입력

    def set_mv_flow(self, mv_flow):
        """수증기 질량 유량 설정 (kg/s)"""
        self.MV_flow = mv_flow

    def update(self, dt=1.0):
        """수증기압 업데이트 (시간 dt: 초 단위)"""
        if not self.steadystate:
            C = self.M_H * 1e3 * self.V_air / (self.R * self.T)  # 단위 일치 위해 1e3 곱함
            dVP_dt = self.MV_flow / C
            self.VP += dVP_dt * dt  # Euler integration
        # else: VP remains constant

    def get_vapor_pressure(self):
        return self.VP

    def get_mv_flow(self):
        return self.MV_flow
