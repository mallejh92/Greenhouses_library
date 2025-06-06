from Interfaces.Vapour.WaterMassPort import WaterMassPort
from Flows.Sources.Vapour.PrescribedPressure import PrescribedPressure

class AirVP:
    """
    Greenhouse air vapour pressure by numerical integration of the differential equation of the moisture content.
    This model applies the mass balance on the moisture content of the air.
    The water vapour pressure of the air is computed by numerical integration of the differential equation of the moisture content.
    """
    def __init__(self, V_air=1e3, VP_start=0.04e5, steadystate=True, T=291):
        """
        Initialize AirVP component
        
        Parameters:
        -----------
        V_air : float
            Air volume [m³]
        VP_start : float
            Initial vapor pressure [Pa]
        steadystate : bool
            Whether to use steady state initialization
        T : float
            Air temperature [K]
        """
        # Parameters
        self.V_air = V_air              # Air volume [m³]
        self.steadystate = steadystate  # Steady state flag
        self.T = T                      # Air temperature [K]

        # Constants
        self.R = 8314                   # Gas constant [J/(kmol·K)]
        self.M_H = 18e-3                # Molar mass of water vapor [kg/mol]
        self.MV_flow = 0.0              # Water vapor mass flow rate [kg/s]

        # Components
        self.port = WaterMassPort()  # VP는 나중에 설정
        self.prescribed_pressure = PrescribedPressure()
        
        # Connect components
        self.prescribed_pressure.connect_port(self.port)
        
        # Set initial VP after components are initialized
        self._VP = None  # VP는 setter를 통해 설정
        if VP_start is not None:
            self.VP = VP_start

    @property
    def VP(self):
        """Get vapor pressure"""
        return self._VP

    @VP.setter
    def VP(self, value):
        """Set vapor pressure and update components"""
        self._VP = value
        if hasattr(self, 'port'):
            self.port.VP = value
            self.prescribed_pressure.connect_VP(value)
            self.prescribed_pressure.calculate()

    def step(self, dt=1.0):
        """
        Update the vapor pressure using numerical integration
        Args:
            dt: Time step [s]
        """
        if not self.steadystate and hasattr(self, 'port'):
            # Euler integration of the differential equation
            # der(VP) = 1/(M_H*1e3*V_air/(R*T))*(MV_flow)
            dVP = (1.0 / (self.M_H * 1e3 * self.V_air / (self.R * self.T))) * self.MV_flow
            self.VP += dVP * dt

    def get_vapor_pressure(self):
        """Get current vapor pressure [Pa]"""
        return self.VP

    def get_mv_flow(self):
        """Get current mass flow rate [kg/s]"""
        return self.MV_flow

    def set_mv_flow(self, mv_flow):
        """Set water vapor mass flow rate [kg/s]"""
        self.MV_flow = mv_flow
        if hasattr(self, 'port'):
            self.port.MV_flow = mv_flow

    def set_prescribed_pressure(self, VP):
        """Set prescribed pressure [Pa]"""
        if hasattr(self, 'prescribed_pressure'):
            self.prescribed_pressure.connect_VP(VP)
            self.prescribed_pressure.calculate()
            self.VP = VP

    def connect(self, port):
        """Connect to another port"""
        if port is not None:
            self.port = port
            self.prescribed_pressure.connect_port(port)
            if self._VP is not None:
                self.prescribed_pressure.connect_VP(self._VP)
                self.prescribed_pressure.calculate()