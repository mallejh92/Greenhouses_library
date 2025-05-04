import numpy as np

class HeatingPipe:
    """
    Simplified Python version of Greenhouses.Components.Greenhouse.HeatingPipe
    A model of a 1D discretized incompressible fluid flow heating pipe system.
    This version focuses on geometry and basic energy transfer coefficients.
    """

    def __init__(self, A, d, l, N=2, N_p=1, freePipe=True, Mdotnom=0.528):
        self.A = A              # Greenhouse floor area [m^2]
        self.d = d              # Pipe diameter [m]
        self.l = l              # Total pipe length [m]
        self.N = N              # Number of discretized nodes
        self.N_p = N_p          # Number of parallel loops
        self.Mdotnom = Mdotnom  # Nominal mass flow rate [kg/s]
        self.freePipe = freePipe

        # Constants
        self.pi = np.pi

        # Derived values
        self.c = 0.5 if self.freePipe else 0.49
        self.A_pipe_external = self.N_p * self.pi * self.d * self.l  # [m²]
        self.V = self.pi * ((self.d - 0.004) / 2)**2 * self.l        # pipe fluid volume [m³]
        self.A_PipeFloor = self.A_pipe_external / self.A            # [m² pipe] / [m² floor]
        self.FF = self.A_PipeFloor * self.c                         # effective floor fraction

        # Inlet/Outlet (placeholder, not fully modeled)
        self.T_inlet = 353.15   # [K]
        self.T_outlet = 323.15  # [K]
        self.p_start = 2e5      # [Pa]

    def get_effective_heat_transfer_area(self):
        return self.FF

    def get_inlet_temperature(self):
        return self.T_inlet

    def get_outlet_temperature(self):
        return self.T_outlet
