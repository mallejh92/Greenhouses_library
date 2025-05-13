# Element1D.py
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Interfaces.Vapour.WaterMassPort_b import WaterMassPort_b

class Element1D:
    """
    Partial water mass transfer element with two WaterMassPort connectors.
    Does not store energy.
    Attributes:
        MV_flow (float): Mass flow rate from port_a to port_b [kg/s]
        dP (float): Pressure difference (port_a.VP - port_b.VP) [Pa]
        port_a (WaterMassPort_a): Inlet port
        port_b (WaterMassPort_b): Outlet port
    """
    def __init__(self, VP_a_start=0.04e5, VP_b_start=0.04e5):
        self.port_a = WaterMassPort_a(VP_start=VP_a_start)
        self.port_b = WaterMassPort_b(VP_start=VP_b_start)
        self.MV_flow = 0.0
        self.dP = self.port_a.VP - self.port_b.VP

    def update(self):
        """
        Update pressure difference and enforce flow direction.
        """
        self.dP = self.port_a.VP - self.port_b.VP
        self.port_a.MV_flow = self.MV_flow
        self.port_b.MV_flow = -self.MV_flow
