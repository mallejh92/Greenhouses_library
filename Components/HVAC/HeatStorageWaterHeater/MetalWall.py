import numpy as np
from dataclasses import dataclass

@dataclass
class MetalWall:
    N: int = 10  # Number of segments
    Aext: float = 1.0  # External heat exchange area [m^2]
    Aint: float = 1.0  # Internal heat exchange area [m^2]
    M_wall: float = 10.0  # Mass of the metal wall [kg]
    c_wall: float = 500.0  # Specific heat capacity [J/kg/K]
    Tstart_wall_1: float = 293.15  # Initial temp at bottom [K]
    Tstart_wall_end: float = 303.15  # Initial temp at top [K]
    steadystate_T_wall: bool = False  # Whether to hold wall temp constant

    def __post_init__(self):
        self.T_wall = np.linspace(self.Tstart_wall_1, self.Tstart_wall_end, self.N)
        self.Aext_i = self.Aext / self.N
        self.Aint_i = self.Aint / self.N
        self.der_T_wall = np.zeros(self.N)

    def update(self, phi_ext: np.ndarray, phi_int: np.ndarray):
        """Update metal wall temperatures given heat fluxes from external and internal sides."""
        Q_tot_ext = self.Aext * np.sum(phi_ext) / self.N
        Q_tot_int = self.Aint * np.sum(phi_int) / self.N

        if not self.steadystate_T_wall:
            self.der_T_wall = (self.Aext_i * phi_ext + self.Aint_i * phi_int) / ((self.M_wall / self.N) * self.c_wall)
            self.T_wall += self.der_T_wall  # Euler step
        else:
            self.der_T_wall = np.zeros(self.N)

        return {
            "T_wall": self.T_wall,
            "der_T_wall": self.der_T_wall,
            "Q_tot_ext": Q_tot_ext,
            "Q_tot_int": Q_tot_int
        }

