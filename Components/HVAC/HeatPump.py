class HeatPump:
    def __init__(self):
        self.V = 0.005
        self.A = 10
        self.eta_II = 0.4
        self.tau = 60
        self.Qdot_nom = 10000
        self.Th_nom = 35 + 273.15
        self.Tc_nom = 273.15
        self.M_wall = 69
        self.c_wall = 500
        self.Th = 35 + 273.15
        self.Tmax = 373.15
        self.first_order_y = 0.0
        self.Qdot = 0.0
        self.Wdot = 0.0

    def update(self, dt, T_source, on_off=True):
        self.T_source = T_source
        COP_nom = self.eta_II * self.Th_nom / (self.Th_nom - self.Tc_nom)
        Wdot_nom = self.Qdot_nom / COP_nom

        COP = self.eta_II * self.Th / (self.Th - self.T_source) if (self.Th - self.T_source) != 0 else 1e-6
        Qdot = self.Qdot_nom * self.T_source / self.Tc_nom
        Wdot = Qdot / COP

        u = 1.0 if on_off else 0.0
        dy = (u - self.first_order_y) * dt / self.tau
        self.first_order_y += dy

        self.Qdot = self.first_order_y * Qdot
        self.Wdot = self.first_order_y * Wdot

        if self.Th >= self.Tmax:
            raise ValueError("Maximum temperature reached at heat pump outlet")

        return {
            "Qdot": self.Qdot,
            "Wdot": self.Wdot,
            "COP": COP,
            "Qdot_nom": self.Qdot_nom,
            "Wdot_nom": Wdot_nom,
            "T_source": self.T_source,
            "Th": self.Th,
            "first_order_y": self.first_order_y
        }
