import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature import PrescribedTemperature
from Interfaces.Heat.HeatFluxVectorInput import HeatFluxVectorInput
from Modelica.Blocks.Sources.RealExpression import RealExpression

class Floor:
    """
    Python version of the Greenhouses.Components.Greenhouse.Floor model.
    Computes the floor temperature based on an energy balance:
      - Sensible heat flows (all flows connected to the heat port)
      - Short-wave radiation absorbed from the sun and/or supplementary lighting
    """

    def __init__(self, A, rho=1.0, c_p=2e6, V=0.01, T_start=298.15, steadystate=False, N_rad=2):
        """
        Initialize the Floor model.

        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        rho : float, optional
            Density [kg/m³]
        c_p : float, optional
            Specific heat capacity [J/(kg·K)]
        V : float, optional
            Volume [m³]
        T_start : float, optional
            Initial temperature [K]
        steadystate : bool, optional
            If True, sets dT = 0 during initialization
        N_rad : int, optional
            Number of short-wave radiation inputs (1 for sun only, 2 for sun + illumination)
        """
        # Parameters
        self.A = A
        self.rho = rho
        self.c_p = c_p
        self.V = V
        self.steadystate = steadystate
        self.N_rad = N_rad

        # State variables
        self.T = T_start          # Current floor temperature [K]
        self.Q_flow = 0.0         # Sensible heat flow rate [W]
        self.P_Flr = 0.0          # Total short-wave power to the floor [W]

        # Heat port and temperature control
        # RealExpression outputs the current floor temperature self.T
        self.portT = RealExpression(lambda t: self.T)
        # PrescribedTemperature block to force port temperature = self.T
        self.preTem = PrescribedTemperature(T_start=T_start)
        # HeatPort_a serves as the interface for sensible heat inputs
        self.heatPort = HeatPort_a(T_start=T_start)

        # Connect RealExpression → PrescribedTemperature → HeatPort_a
        self.portT.connect(self.preTem)          # connect(portT.y, preTem.T)
        self.preTem.port.connect(self.heatPort)  # connect(preTem.port, heatPort)

        # Radiation inputs (initially empty vector: cardinality = 0)
        self.R_Flr_Glob = HeatFluxVectorInput([])

    def set_inputs(self, Q_flow=0.0, R_Flr_Glob=None):
        """
        Set input values for the floor.

        Parameters:
        -----------
        Q_flow : float, optional
            Sensible heat flow rate [W] entering through heatPort.
        R_Flr_Glob : list of float, optional
            Short-wave radiation inputs [W/m²]. Length must be N_rad.
            If None, implicitly treat as a zero-vector of length N_rad.
        """
        # 1) Sensible heat input
        self.Q_flow = Q_flow
        self.heatPort.Q_flow = Q_flow

        # 2) Short-wave radiation vector input
        if R_Flr_Glob is not None:
            if len(R_Flr_Glob) != self.N_rad:
                raise ValueError(f"R_Flr_Glob must have length {self.N_rad}")
            # Replace with a new HeatFluxVectorInput of the given values
            self.R_Flr_Glob = HeatFluxVectorInput(R_Flr_Glob)
        else:
            # Cardinality = 0 case: initialize to zero vector of length N_rad
            zero_list = [0.0] * self.N_rad
            self.R_Flr_Glob = HeatFluxVectorInput(zero_list)

    def step(self, dt):
        """
        Update floor state
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        # Calculate total short-wave power
        # HeatFluxVectorInput의 values가 비어있을 수 있으므로 안전하게 처리
        if not hasattr(self.R_Flr_Glob, 'values') or not self.R_Flr_Glob.values:
            self.P_Flr = 0.0
        else:
            # HeatFlux 객체의 value 속성에 접근
            self.P_Flr = sum(flux.value for flux in self.R_Flr_Glob.values if hasattr(flux, 'value')) * self.A
        
        # Update temperature (der(T) = 1/(rho*c_p*V)*(Q_flow + P_Flr))
        if not self.steadystate:
            dT = (self.Q_flow + self.P_Flr) / (self.rho * self.c_p * self.V)
            self.T += dT * dt
        
        # Update port temperature expression and prescribed temperature
        self.portT.step(dt)  # 시간 업데이트 및 연결된 블록에 전파
        
        # heatPort의 온도를 T와 동기화
        self.heatPort.T = self.T
        self.preTem.T = self.T
        
        return self.T

    def get_temperature(self):
        """
        Return the current floor temperature [K].
        """
        return self.T