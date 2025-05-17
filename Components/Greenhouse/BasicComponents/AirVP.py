from Interfaces.Vapour.WaterMassPort import WaterMassPort
from Flows.Sources.Vapour.PrescribedPressure import PrescribedPressure

class AirVP:
    """
    Greenhouse air vapour pressure by numerical integration of the differential equation of the moisture content.
    This model applies the mass balance on the moisture content of the air.
    The water vapour pressure of the air is computed by numerical integration of the differential equation of the moisture content.
    """
    def __init__(self, V_air=1e3, VP_start=0.04e5, steadystate=True, T=291):
        # Parameters
        self.V_air = V_air              # Air volume [m³]
        self.VP = VP_start              # Initial vapor pressure [Pa]
        self.steadystate = steadystate  # Steady state flag
        self.T = T                      # Air temperature [K]

        # Constants
        self.R = 8314                   # Gas constant [J/(kmol·K)]
        self.M_H = 18e-3                # Molar mass of water vapor [kg/mol]
        self.MV_flow = 0.0              # Water vapor mass flow rate [kg/s]

        # Components
        self.port = WaterMassPort(VP_start)
        self.prescribed_pressure = PrescribedPressure()
        self.prescribed_pressure.connect(self.port)

    def set_mv_flow(self, mv_flow):
        """Set water vapor mass flow rate [kg/s]"""
        self.MV_flow = mv_flow
        self.port.MV_flow = mv_flow

    def update(self, dt=1.0):
        """
        Update vapor pressure using Euler integration
        Args:
            dt: Time step [s]
        """
        if not self.steadystate:
            C = self.M_H * 1e3 * self.V_air / (self.R * self.T)  # Multiply by 1e3 for unit consistency
            dVP_dt = self.MV_flow / C
            self.VP += dVP_dt * dt  # Euler integration
            self.port.VP = self.VP  # Update port VP
        # else: VP remains constant

    def get_vapor_pressure(self):
        """Get current vapor pressure [Pa]"""
        return self.VP

    def get_mv_flow(self):
        """Get current mass flow rate [kg/s]"""
        return self.MV_flow

    def set_prescribed_pressure(self, VP):
        """Set prescribed pressure [Pa]"""
        self.prescribed_pressure.set_pressure(VP)
