from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_b import HeatPort_b
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Interfaces.Vapour.WaterMassPort_b import WaterMassPort_b

class Element1D:
    """
    Partial model for a water mass transfer element with two WaterMassPort connectors.
    This model is used as a base class for all elements that transfer water mass.
    
    Attributes:
        MassPort_a (WaterMassPort_a): Inlet mass port
        MassPort_b (WaterMassPort_b): Outlet mass port
        HeatPort_a (HeatPort_a): Inlet heat port
        HeatPort_b (HeatPort_b): Outlet heat port
        MV_flow (float): Mass vapor flow rate [kg/s]
        Q_flow (float): Heat flow rate [W]
        dP (float): Pressure difference between ports [Pa]
        dT (float): Temperature difference between ports [K]
    """
    def __init__(self, VP_a_start=None, VP_b_start=None, T_a_start=293.15, T_b_start=293.15):
        """
        Initialize Element1D
        
        Parameters:
        -----------
        VP_a_start : float, optional
            Initial vapor pressure at MassPort_a [Pa]
        VP_b_start : float, optional
            Initial vapor pressure at MassPort_b [Pa]
        T_a_start : float, optional
            Initial temperature at HeatPort_a [K], defaults to 293.15K (20°C)
        T_b_start : float, optional
            Initial temperature at HeatPort_b [K], defaults to 293.15K (20°C)
        """
        self.MassPort_a = WaterMassPort_a(VP=VP_a_start)
        self.MassPort_b = WaterMassPort_b(VP=VP_b_start)
        self.HeatPort_a = HeatPort_a(T_start=T_a_start)
        self.HeatPort_b = HeatPort_b(T_start=T_b_start)
        self.MV_flow = 0.0
        self.Q_flow = 0.0
        self.dP = self.MassPort_a.VP - self.MassPort_b.VP if (VP_a_start is not None and VP_b_start is not None) else 0.0
        self.dT = self.HeatPort_a.T - self.HeatPort_b.T

    def update(self):
        """
        Update pressure and temperature differences and enforce flow direction.
        Called after each simulation step to ensure consistency.
        """
        self.dP = self.MassPort_a.VP - self.MassPort_b.VP
        self.dT = self.HeatPort_a.T - self.HeatPort_b.T
        
        # Mass vapor flow: positive when flowing from a to b
        self.MassPort_a.MV_flow = self.MV_flow
        self.MassPort_b.MV_flow = -self.MV_flow
        
        # Heat flow: positive when flowing from a to b
        self.HeatPort_a.Q_flow = self.Q_flow  # Positive Q_flow means heat flowing into port_a
        self.HeatPort_b.Q_flow = -self.Q_flow  # Negative Q_flow means heat flowing out of port_b

    def step(self, dt):
        """
        Update the element state for one time step.
        
        Parameters:
        -----------
        dt : float
            Time step [s]
            
        Returns:
        --------
        tuple
            (MV_flow, Q_flow) Mass vapor flow rate and heat flow rate
        """
        self.update()
        return self.MV_flow, self.Q_flow 