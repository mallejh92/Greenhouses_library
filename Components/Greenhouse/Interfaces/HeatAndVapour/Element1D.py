from Components.Greenhouse.Interfaces.Heat.HeatPort_a import HeatPort_a
from Components.Greenhouse.Interfaces.Heat.HeatPort_b import HeatPort_b
from Components.Greenhouse.Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Components.Greenhouse.Interfaces.Vapour.WaterMassPort_b import WaterMassPort_b

class Element1D:
    """
    Partial water mass and heat transfer element with two ports for each.
    Does not store energy.
    
    Attributes:
        Q_flow (float): Heat flow rate from port_a -> port_b [W]
        dT (float): Temperature difference (port_a.T - port_b.T) [K]
        MV_flow (float): Mass flow rate from port_a -> port_b [kg/s]
        dP (float): Pressure difference (port_a.VP - port_b.VP) [Pa]
        HeatPort_a (HeatPort_a): Inlet heat port
        HeatPort_b (HeatPort_b): Outlet heat port
        MassPort_a (WaterMassPort_a): Inlet mass port
        MassPort_b (WaterMassPort_b): Outlet mass port
    """
    def __init__(self, T_a_start=293.15, T_b_start=293.15, 
                 VP_a_start=0.04e5, VP_b_start=0.04e5):
        # Heat ports
        self.HeatPort_a = HeatPort_a(T_start=T_a_start)
        self.HeatPort_b = HeatPort_b(T_start=T_b_start)
        
        # Mass ports
        self.MassPort_a = WaterMassPort_a(VP_start=VP_a_start)
        self.MassPort_b = WaterMassPort_b(VP_start=VP_b_start)
        
        # Heat transfer variables
        self.Q_flow = 0.0
        self.dT = self.HeatPort_a.T - self.HeatPort_b.T
        
        # Mass transfer variables
        self.MV_flow = 0.0
        self.dP = self.MassPort_a.VP - self.MassPort_b.VP

    def update(self):
        """
        Update temperature and pressure differences and enforce flow directions.
        """
        # Update heat transfer
        self.dT = self.HeatPort_a.T - self.HeatPort_b.T
        self.HeatPort_a.Q_flow = self.Q_flow
        self.HeatPort_b.Q_flow = -self.Q_flow
        
        # Update mass transfer
        self.dP = self.MassPort_a.VP - self.MassPort_b.VP
        self.MassPort_a.MV_flow = self.MV_flow
        self.MassPort_b.MV_flow = -self.MV_flow 