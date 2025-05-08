from dataclasses import dataclass
import numpy as np

@dataclass
class HeatStorageHXCell:
    Vi: float = 0.02  # tank cell volume
    Ai: float = 0.1   # ambient heat exchange area
    A_hx: float = 0.05  # heat exchanger area
    Mdotnom: float = 0.1
    Unom: float = 1.0       # ambient heat transfer coeff
    Unom_hx: float = 4000.0  # heat exchanger transfer coeff
    T: float = 283.15        # initial tank temperature [K]
    T_wall_int: float = 300.0  # internal tank wall temp
    T_wall_hx: float = 330.0  # heat exchanger wall temp
    h: float = 1e5
    p: float = 1e5
    rho: float = 1000.0
    Cp: float = 4186.0
    steadystate: bool = False
    Wdot_direct: float = 0.0

    def update(self):
        # heat flux from ambient
        qdot_amb = self.Unom * (self.T_wall_int - self.T)
        # heat flux from heat exchanger
        qdot_hx = self.Unom_hx * (self.T_wall_hx - self.T)
        # total heat into fluid
        Q_tot = self.Ai * qdot_amb + self.A_hx * qdot_hx + self.Wdot_direct
        dh_dt = Q_tot / (self.rho * self.Vi)
        if not self.steadystate:
            self.h += dh_dt
            self.T = self.h / self.Cp
        return {
            "T": self.T,
            "h": self.h,
            "qdot_amb": qdot_amb,
            "qdot_hx": qdot_hx,
            "Q_tot": Q_tot,
            "dh_dt": dh_dt
        }

# 전체 탱크 구성
def simulate_heat_storage_hx():
    N = 15
    N1 = int(0.3 * N)
    N2 = int(0.6 * N)
    tank_cells = []

    for i in range(N):
        if i < N1 or i >= N2:
            T_wall_hx = 273.15  # no HX
        else:
            T_wall_hx = 330.0

        cell = HeatStorageHXCell(
            T=283.15 + (i / (N-1)) * (60 - 10),  # gradient init
            T_wall_hx=T_wall_hx,
            T_wall_int=310.0,
            Wdot_direct=3000.0 / N  # resistor power
        )
        tank_cells.append(cell)

    results = [cell.update() for cell in tank_cells]
    return results