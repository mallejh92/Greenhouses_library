import numpy as np


class HeatPumpConsoClim:
    """
    A simplified Python translation of the Modelica model: Greenhouses.Components.HVAC.HeatPump_ConsoClim
    This model simulates the behavior of a heat pump with control input for electrical power.
    """

    def __init__(self,
                 V=0.005,                # m³, internal volume
                 A=10,                   # m², heat exchange area
                 COP_n=3.9505,
                 Q_dot_cd_n=10020,       # W
                 T_su_ev_n=280.15,       # K, 7°C
                 T_ex_cd_n=308.15,       # K, 35°C
                 C0=0.949, C1=-8.05, C2=111.09,
                 D0=0.968, D1=0.0226, D2=-0.0063,
                 K1=0, K2=0.67,
                 a=0.7701, b=0.2299,
                 tau=60,                 # s, startup time constant
                 Variable_Compressor_Speed=False,
                 T_ex_cd_sensor=308.15,  # K, exhaust condenser temp sensor
                 on_off=True):
        # Parameters
        self.V = V
        self.A = A
        self.COP_n = COP_n
        self.Q_dot_cd_n = Q_dot_cd_n
        self.T_su_ev_n = T_su_ev_n
        self.T_ex_cd_n = T_ex_cd_n
        self.C0, self.C1, self.C2 = C0, C1, C2
        self.D0, self.D1, self.D2 = D0, D1, D2
        self.K1, self.K2 = K1, K2
        self.a, self.b = a, b
        self.tau = tau
        self.Variable_Compressor_Speed = Variable_Compressor_Speed
        self.on_off = on_off

        # State Variables (initial values)
        self.T_su_ev = T_su_ev_n
        self.T_ex_cd = T_ex_cd_sensor
        self.Q_dot_cd = 0
        self.W_dot_cp = 0
        self.COP = 0

    def update(self, W_dot_set, m_dot_ev, h_su_ev, h_ex_ev):
        """
        Updates the heat pump state based on input conditions.
        """
        if not self.on_off or W_dot_set <= 0:
            self.Q_dot_cd = 0
            self.W_dot_cp = 0
            self.COP = 0
            return

        # Evaporator thermal power
        Q_dot_ev = m_dot_ev * (h_su_ev - h_ex_ev)

        # Condenser temp from sensor (assumed input)
        DELTA_T = self.T_su_ev / self.T_ex_cd - (self.T_su_ev_n / self.T_ex_cd_n)

        # Efficiency and part-load factors
        EIRFT = self.C0 + self.C1 * DELTA_T + self.C2 * DELTA_T**2
        COP_fl = self.COP_n / EIRFT

        CAPFT = self.D0 + self.D1 * (self.T_su_ev - self.T_su_ev_n) + self.D2 * (self.T_ex_cd - self.T_ex_cd_n)
        Q_dot_cd_fl = CAPFT * self.Q_dot_cd_n
        W_dot_fl = Q_dot_cd_fl / COP_fl
        PLR = np.clip(self.Q_dot_cd / Q_dot_cd_fl if Q_dot_cd_fl > 0 else 0, 0, 1)
        EIRFPLR = W_dot_set / W_dot_fl if W_dot_fl > 0 else 0

        # Reference PLR=0.3 for ON/OFF switching
        PLR_30 = 0.3
        EIRFPLR_30 = self.K1 + (self.K2 - self.K1) * PLR_30 + (1 - self.K2) * PLR_30**2
        W_dot_30 = (self.Q_dot_cd_n / self.COP_n) * EIRFT * CAPFT * EIRFPLR_30
        Q_dot_30 = PLR_30 * Q_dot_cd_fl
        COP_30 = Q_dot_30 / W_dot_30 if W_dot_30 > 0 else 0

        if not self.Variable_Compressor_Speed:
            if W_dot_set <= W_dot_fl and W_dot_set > 0:
                self.W_dot_cp = W_dot_set
                if W_dot_set >= W_dot_30:
                    # PLR >= 0.3
                    PLR = 0.017575812 + 1.36394 * EIRFPLR - 0.531124 * EIRFPLR**2 + 0.1495 * EIRFPLR**3
                    self.Q_dot_cd = PLR * Q_dot_cd_fl
                else:
                    # PLR < 0.3
                    self.Q_dot_cd = max(0, (W_dot_set * COP_30 - self.b * Q_dot_cd_fl * 0.3) / self.a)
                self.COP = self.Q_dot_cd / self.W_dot_cp if self.W_dot_cp > 0 else 0
            else:
                self.W_dot_cp = W_dot_fl
                self.COP = COP_fl
                self.Q_dot_cd = Q_dot_cd_fl
        else:
            if W_dot_set <= W_dot_fl and W_dot_set > 0:
                self.W_dot_cp = W_dot_set
                self.Q_dot_cd = max(0, (W_dot_set * COP_fl - self.b * Q_dot_cd_fl) / self.a)
                self.COP = self.Q_dot_cd / self.W_dot_cp if self.W_dot_cp > 0 else 0
            else:
                self.W_dot_cp = W_dot_fl
                self.COP = COP_fl
                self.Q_dot_cd = Q_dot_cd_fl

    def get_outputs(self):
        """
        Returns the key output values.
        """
        return {
            "Q_dot_cd": self.Q_dot_cd,
            "W_dot_cp": self.W_dot_cp,
            "COP": self.COP
        }
