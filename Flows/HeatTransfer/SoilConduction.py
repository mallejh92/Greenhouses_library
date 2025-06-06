import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature import PrescribedTemperature
from Flows.HeatTransfer.ThermalConductor import ThermalConductor
from Components.Greenhouse.BasicComponents.Layer import Layer

class SoilConduction:
    def __init__(self, A, N_c=2, N_s=5, lambda_c=1.7, lambda_s=0.85, steadystate=False):
        self.A = A
        self.N_c = N_c
        self.N_s = N_s
        self.lambda_c = lambda_c
        self.lambda_s = lambda_s
        self.steadystate = steadystate

        # Floor 입력 포트
        self.port_a = HeatPort_a()
        # 심토양 온도원
        self.soil = PrescribedTemperature()
        self.T_soil_sp = 283.15  # 사용자가 외부에서 바꿀 수 있음

        # 두께 및 전도도 배열 초기화
        self.th_s = np.zeros(N_s)
        self.G_s = np.zeros(N_s)
        self.th_c = np.zeros(max(0, N_c - 1))
        self.G_c = np.zeros(max(0, N_c - 1))
        self.G_cc = 0.0
        self.G_ss = 0.0

        # 두께·전도도 계산
        self._calculate_parameters()
        # 컴포넌트 생성 및 포트 연결
        self._initialize_components()

    def _calculate_parameters(self):
        # 1) Soil 첫 두께
        if self.N_c == 0:
            self.th_s[0] = 0.05
        else:
            self.th_s[0] = 0.05 * (2 ** (self.N_c - 1))

        # 2) Soil 나머지 층 두께
        for i in range(1, self.N_s):
            self.th_s[i] = self.th_s[0] * (2 ** i)

        # 3) Concrete 층 두께 (N_c > 1일 때)
        if self.N_c > 1:
            self.th_c[0] = 0.02
            for i in range(1, self.N_c - 1):
                self.th_c[i] = self.th_c[0] * (2 ** i)

        # 4) 전도도 계산
        if self.N_c == 0:
            # Concrete 없을 때
            for i in range(self.N_s):
                self.G_s[i] = (self.lambda_s * self.A) / (self.th_s[i] * 0.75)
            self.G_cc = 0.0
        else:
            if self.N_c == 1:
                self.G_cc = (self.lambda_c * self.A) / 0.005
            else:
                for i in range(self.N_c - 1):
                    self.G_c[i] = (self.lambda_c * self.A) / (self.th_c[i] * 0.75)
                self.G_cc = (self.lambda_c * self.A) / (self.th_c[-1] * 0.5)

            for i in range(self.N_s):
                self.G_s[i] = (self.lambda_s * self.A) / (self.th_s[i] * 0.75)

        # 마지막 Soil층 ↔ 심토양 전도도
        self.G_ss = (self.lambda_s * self.A) / (self.th_s[-1] * 0.5)

    def _initialize_components(self):
        # --- Soil용 ThermalConductor & Layer 생성 ---
        self.TC_s = [ThermalConductor(G=g) for g in self.G_s]
        self.Layer_s = [
            Layer(rho=1, c_p=1.73e6, A=self.A, V=self.A * th, steadystate=self.steadystate)
            for th in self.th_s
        ]
        self.TC_ss = ThermalConductor(G=self.G_ss)

        # --- Concrete용 ThermalConductor & Layer 생성 (N_c > 0일 때) ---
        if self.N_c > 0:
            self.TC_cc = ThermalConductor(G=self.G_cc)
            if self.N_c > 1:
                self.TC_c = [ThermalConductor(G=g) for g in self.G_c]
                self.Layer_c = [
                    Layer(rho=1, c_p=2e6, A=self.A, V=self.A * th, steadystate=self.steadystate)
                    for th in self.th_c
                ]

        # --- 포트 연결 로직 ---
        # (1) 콘크리트가 전혀 없는 경우
        if self.N_c == 0:
            # floor(port_a) ↔ 첫 번째 Soil 전도체
            self.TC_s[0].port_a = self.port_a

        else:
            # (2) 콘크리트가 1겹 있는 경우
            if self.N_c == 1:
                # floor(port_a) ↔ TC_cc.port_a
                self.TC_cc.port_a = self.port_a
                # TC_cc.port_b ↔ TC_s[0].port_a
                self.TC_s[0].port_a = self.TC_cc.port_b

            # (3) 콘크리트 2겹 이상인 경우
            else:
                # - 첫 번째 Concrete 전도체 TC_c[0].port_a ↔ floor(port_a)
                self.TC_c[0].port_a = self.port_a
                # - TC_c[0].port_b ↔ Layer_c[0].heatPort
                self.TC_c[0].port_b = self.Layer_c[0].heatPort

                # - 중간 Concrete층들 연결 (j = 1,2,...,N_c-2)
                #   TC_c[j].port_a ↔ Layer_c[j-1].heatPort
                #   TC_c[j].port_b ↔ Layer_c[j].heatPort
                for j in range(1, self.N_c - 1):
                    self.TC_c[j].port_a = self.Layer_c[j-1].heatPort
                    self.TC_c[j].port_b = self.Layer_c[j].heatPort

                # - 마지막 Concrete층 Layer_c[-1] ↔ TC_cc ↔ Soil 첫 전도체
                #   TC_cc.port_a ↔ Layer_c[-1].heatPort
                self.TC_cc.port_a = self.Layer_c[-1].heatPort
                #   TC_cc.port_b ↔ TC_s[0].port_a
                self.TC_s[0].port_a = self.TC_cc.port_b

        # --- Soil층 연결 (공통) ---
        # TC_s[0].port_b ↔ Layer_s[0].heatPort
        self.TC_s[0].port_b = self.Layer_s[0].heatPort
        # TC_s[i].port_a ↔ Layer_s[i-1].heatPort, TC_s[i].port_b ↔ Layer_s[i].heatPort (i=1..N_s-1)
        for i in range(1, self.N_s):
            self.TC_s[i].port_a = self.Layer_s[i-1].heatPort
            self.TC_s[i].port_b = self.Layer_s[i].heatPort

        # --- 마지막 Soil층 ↔ 심토양 연결 ---
        # TC_ss.port_a ↔ Layer_s[-1].heatPort
        self.TC_ss.port_a = self.Layer_s[-1].heatPort
        # TC_ss.port_b ↔ soil.port
        self.TC_ss.port_b = self.soil.port

    def calculate(self):
        """
        수정된 calculate():
        1) 모든 Conductor 계산값을 리스트에 저장
        2) 각 Layer가 받아야 할 순열유속(net Q)을 계산하여 set_heat_flow() 호출
        3) 총 Q_flow를 반환
        """
        # (0) 심토양 온도 설정
        self.soil.T = self.T_soil_sp

        # (1) 콘크리트가 없는 경우 (N_c == 0)
        if self.N_c == 0:
            Q_list_s = [tc.calculate() for tc in self.TC_s]  # Soil 전도체들
            Q_ss = self.TC_ss.calculate()

            # Soil층 순열유속 계산
            for i in range(self.N_s):
                if i == 0:
                    net_Q = Q_list_s[0] - (Q_list_s[1] if self.N_s > 1 else 0.0)
                elif i < self.N_s - 1:
                    net_Q = Q_list_s[i] - Q_list_s[i+1]
                else:
                    net_Q = Q_list_s[-1] - Q_ss
                self.Layer_s[i].set_heat_flow(net_Q)

            Q_flow = sum(Q_list_s) + Q_ss
            return Q_flow

        # (2) 콘크리트 1겹인 경우 (N_c == 1)
        if self.N_c == 1:
            Q_cc = self.TC_cc.calculate()
            Q_list_s = [tc.calculate() for tc in self.TC_s]
            Q_ss = self.TC_ss.calculate()

            # Soil층 순열유속 계산
            for i in range(self.N_s):
                if i == 0:
                    net_Q = Q_list_s[0] - (Q_list_s[1] if self.N_s > 1 else 0.0)
                elif i < self.N_s - 1:
                    net_Q = Q_list_s[i] - Q_list_s[i+1]
                else:
                    net_Q = Q_list_s[-1] - Q_ss
                self.Layer_s[i].set_heat_flow(net_Q)

            Q_flow = Q_cc + sum(Q_list_s) + Q_ss
            return Q_flow

        # (3) 콘크리트 2겹 이상인 경우 (N_c > 1)
        Q_list_c = [tc.calculate() for tc in self.TC_c]  # Concrete 전도체들
        Q_cc = self.TC_cc.calculate()
        Q_list_s = [tc.calculate() for tc in self.TC_s]  # Soil 전도체들
        Q_ss = self.TC_ss.calculate()

        # (3-1) Concrete층 순열유속 계산
        for i in range(self.N_c - 1):
            if i == 0:
                net_Q_c = Q_list_c[0] - (Q_list_c[1] if self.N_c - 1 > 1 else 0.0)
            elif i < self.N_c - 2:
                net_Q_c = Q_list_c[i] - Q_list_c[i+1]
            else:
                net_Q_c = Q_list_c[-1] - Q_cc
            self.Layer_c[i].set_heat_flow(net_Q_c)

        # (3-2) Soil층 순열유속 계산
        for i in range(self.N_s):
            if i == 0:
                net_Q_s = Q_list_s[0] - (Q_list_s[1] if self.N_s > 1 else 0.0)
            elif i < self.N_s - 1:
                net_Q_s = Q_list_s[i] - Q_list_s[i+1]
            else:
                net_Q_s = Q_list_s[-1] - Q_ss
            self.Layer_s[i].set_heat_flow(net_Q_s)

        Q_flow = sum(Q_list_c) + Q_cc + sum(Q_list_s) + Q_ss
        return Q_flow

    def step(self, dt):
        Q_flow = self.calculate()

        if not self.steadystate:
            if self.N_c > 1:
                for layer in self.Layer_c:
                    layer.update(dt)
            for layer in self.Layer_s:
                layer.update(dt)

        return Q_flow