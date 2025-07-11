import numpy as np
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Flows.Sources.Vapour.PrescribedPressure import PrescribedPressure

class AirVP:
    """
    Greenhouse air vapour pressure by numerical integration of the differential equation 
    of the moisture content - exact Python implementation of Modelica AirVP.mo
    """
    
    def __init__(self, V_air=1000.0, VP_start=4000.0, steadystate=True):
        """
        Initialize AirVP component exactly as in Modelica
        
        Parameters (from Modelica):
        -----------
        V_air : float
            Air volume [m³] (default=1000)
        VP_start : float
            Initial vapor pressure [Pa] (default=4000)
        steadystate : bool
            if true, sets derivative of VP to zero during initialization (default=true)
        """
        # Parameters (exactly as in Modelica)
        self.V_air = V_air
        self.VP_start = VP_start
        self.steadystate = steadystate
        
        # Constants (exactly as in Modelica)
        self.R = 8314.0        # Gas constant [J/(kmol·K)]
        self.T = 291.0         # Temperature [K] (default value)
        self.M_H = 18e-3       # Molar mass of water vapor [kg/mol]
        
        # Variables (exactly as in Modelica)
        self.MV_flow = 0.0     # Mass flow rate [kg/s]
        self.VP = VP_start     # Vapor pressure [Pa]
        
        # Modelica initialization flags
        self._initialization_phase = True
        
        # Connectors (exactly as in Modelica)
        self.port = WaterMassPort_a(VP=VP_start)
        self.prescribedPressure = PrescribedPressure()
        
        # Connections (exactly as in Modelica)
        self.prescribedPressure.connect_VP(self.port)
        
        # Initialize port
        self.port.VP = VP_start
    
    def complete_initialization(self):
        """Complete initialization phase (Modelica: initial equation -> equation)"""
        self._initialization_phase = False
        
    def step(self, dt):
        """
        Execute one simulation step
        
        Implements Modelica equations:
        - port.MV_flow = MV_flow
        - der(VP) = 1/(M_H*1e3*V_air/(R*T))*(MV_flow)
        """
        # Update mass flow (Modelica: port.MV_flow = MV_flow)
        self.port.MV_flow = self.MV_flow
        
        # Vapor pressure derivative (Modelica: der(VP) = 1/(M_H*1e3*V_air/(R*T))*(MV_flow))
        if not (self._initialization_phase and self.steadystate):
            # Only integrate if not in steady-state initialization
            if self.T > 0 and self.V_air > 0:
                # Calculate capacity term (exactly as in Modelica)
                capacity = self.M_H * 1e3 * self.V_air / (self.R * self.T)
                
                if capacity > 0:
                    dVP_dt = self.MV_flow / capacity
                    self.VP += dVP_dt * dt
                    
                    # Ensure VP stays positive
                    self.VP = max(0.0, self.VP)
        
        # Update port and prescribed pressure
        self.port.VP = self.VP
        self.prescribedPressure.VP = self.VP
        self.prescribedPressure.update()
    
    def connect(self, external_port):
        """Connect to external mass port"""
        # Synchronize vapor pressures
        external_port.VP = self.VP
        self.port = external_port
    
    def set_prescribed_pressure(self, VP):
        """Set prescribed vapor pressure"""
        self.VP = VP
        self.port.VP = VP
        self.prescribedPressure.VP = VP
    
    def get_state(self):
        """Get current state of the component"""
        return {
            'VP': self.VP,
            'MV_flow': self.MV_flow,
            'T': self.T,
            'V_air': self.V_air
        }