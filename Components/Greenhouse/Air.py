import numpy as np
from BasicComponents.AirVP import AirVP

class Air:
    def __init__(self, A, h_Air=4.0, rho=1.2, c_p=1000.0, T_start=298.0, N_rad=2, steadystate=False, steadystateVP=False):
        self.A = A
        self.h_Air = h_Air
        self.rho = rho
        self.c_p = c_p
        self.N_rad = N_rad
        self.P_atm = 101325.0
        self.R_a = 287.0
        self.R_s = 461.5
        self.T = T_start
        self.V = self.A * self.h_Air
        self.Q_flow = 0.0
        self.R_Air_Glob = np.zeros(N_rad)
        self.massPort_VP = 0.0
        self.w_air = 0.0
        self.RH = 0.0
        self.steadystate = steadystate
        self.steadystateVP = steadystateVP
        self.airVP = AirVP(V_air=self.V, steadystate=steadystateVP)

    def compute_power_input(self):
        return np.sum(self.R_Air_Glob) * self.A

    def compute_derivatives(self):
        if self.steadystate:
            dTdt = 0.0
        else:
            P_Air = self.compute_power_input()
            dTdt = (self.Q_flow + P_Air) / (self.rho * self.c_p * self.V)
        return dTdt

    def update_humidity(self):
        if self.steadystateVP:
            return
        VP = self.airVP.VP
        self.w_air = VP * self.R_a / ((self.P_atm - VP) * self.R_s)
        T_C = self.T - 273.15
        Psat = 610.78 * np.exp(T_C / (T_C + 238.3) * 17.2694)
        self.RH = VP / Psat
        self.RH = np.clip(self.RH, 0, 1)
        print(f"Debug - VP: {VP}, Psat: {Psat}, RH: {self.RH}")

    def set_outside_conditions(self, T_out=None, RH_out=None):
        self.T_out = T_out
        self.RH_out = RH_out

    def step(self, dt):
        dTdt = self.compute_derivatives()
        self.T += dTdt * dt
        self.update_humidity()
        return self.T, self.RH

    def set_inputs(self, Q_flow, R_Air_Glob, massPort_VP):
        self.Q_flow = Q_flow
        if R_Air_Glob is None or len(R_Air_Glob) == 0:
            self.R_Air_Glob = np.zeros(self.N_rad)
        else:
            self.R_Air_Glob = np.array(R_Air_Glob)
        self.massPort_VP = massPort_VP
        if massPort_VP is not None:
            self.airVP.VP = massPort_VP  # 여기서만 VP를 세팅