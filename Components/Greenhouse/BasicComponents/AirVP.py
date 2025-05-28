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
        self.prescribed_pressure.connect_port(self.port)
        self.prescribed_pressure.connect_VP(VP_start)

    def step(self, dt=1.0):
        """
        Update the vapor pressure using numerical integration
        Args:
            dt: Time step [s]
        """
        if not self.steadystate:
            # Euler integration of the differential equation
            # der(VP) = 1/(M_H*1e3*V_air/(R*T))*(MV_flow)
            dVP = (1.0 / (self.M_H * 1e3 * self.V_air / (self.R * self.T))) * self.MV_flow
            self.VP += dVP * dt
            
            # Update port and prescribed pressure
            self.port.VP = self.VP
            self.prescribed_pressure.connect_VP(self.VP)
            self.prescribed_pressure.calculate()

    def get_vapor_pressure(self):
        """Get current vapor pressure [Pa]"""
        return self.VP

    def get_mv_flow(self):
        """Get current mass flow rate [kg/s]"""
        return self.MV_flow

    def set_mv_flow(self, mv_flow):
        """Set water vapor mass flow rate [kg/s]"""
        self.MV_flow = mv_flow
        self.port.MV_flow = mv_flow

    def set_prescribed_pressure(self, VP):
        """Set prescribed pressure [Pa]"""
        self.prescribed_pressure.connect_VP(VP)
        self.prescribed_pressure.calculate()
        self.VP = VP
        self.port.VP = VP

    def connect(self, port):
        """Connect to another port"""
        self.port = port
        self.prescribed_pressure.connect_port(port)
        self.prescribed_pressure.connect_VP(self.VP)
        self.prescribed_pressure.calculate()