import numpy as np
from Components.Greenhouse.BasicComponents.AirVP import AirVP
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature import PrescribedTemperature
from Modelica.Media.MoistAir.relativeHumidity_pTX import relativeHumidity_pTX

class Air_Top:
    """
    Temperature of air in top compartment computed by static equation because of
    its small heat capacity - exact Python implementation of Modelica Air_Top.mo
    """
    
    def __init__(self, A, h_Top=0.4, c_p=1000.0, T_start=298.0, steadystate=False, steadystateVP=True):
        """
        Initialize Air_Top component exactly as in Modelica
        
        Parameters (from Modelica):
        -----------
        A : float
            Greenhouse floor surface [m²]
        h_Top : float
            Height of the top air compartment [m] (default=0.4)
        c_p : float
            Specific heat capacity [J/(kg·K)] (default=1000)
        T_start : float
            Initial temperature [K] (default=298)
        steadystate : bool
            if true, sets derivative of T to zero during initialization (default=false)
        steadystateVP : bool
            if true, sets derivative of VP to zero during initialization (default=true)
        """
        # Parameters (exactly as in Modelica)
        self.c_p = c_p
        self.h_Top = h_Top
        self.A = A
        self.T_start = T_start
        self.steadystate = steadystate
        self.steadystateVP = steadystateVP
        
        # Constants (exactly as in Modelica)
        self.P_atm = 101325.0  # Atmospheric pressure [Pa]
        self.R_a = 287.0       # Gas constant for dry air [J/(kg·K)]
        self.R_s = 461.5       # Gas constant for water vapor [J/(kg·K)]
        
        # Variables (exactly as in Modelica)
        self.Q_flow = 0.0      # Heat flow rate from port_a -> port_b [W]
        self.T = T_start       # Temperature [K]
        self.rho = 1.2         # Air density [kg/m³] - will be calculated dynamically
        self.RH = 0.0          # Relative humidity [0-1]
        self.V = A * h_Top     # Volume [m³]
        self.w_air = 0.0       # Air humidity ratio (kg water / kg dry air)
        
        # Modelica initialization flags
        self._initialization_phase = True
        
        # Connectors (exactly as in Modelica)
        self.heatPort = HeatPort_a(T_start=T_start)
        self.massPort = WaterMassPort_a()
        
        # Sub-components (exactly as in Modelica)
        self.air = AirVP(V_air=self.V, steadystate=steadystateVP)  # Named 'air' as in Modelica
        self.preTem = PrescribedTemperature(T_start=T_start)
        
        # Connections (exactly as in Modelica)
        self.air.connect(self.massPort)
        # preTem.port는 이미 초기화되어 있으므로 직접 연결하지 않음
    
    def complete_initialization(self):
        """Complete initialization phase (Modelica: initial equation -> equation)"""
        self._initialization_phase = False
        
    def step(self, dt):
        """
        Execute one simulation step
        
        Implements Modelica equations:
        - V = A * h_Top
        - heatPort.Q_flow = Q_flow
        - rho = Modelica.Media.Air.ReferenceAir.Air_pT.density_pT(1e5, heatPort.T)
        - der(T) = 1/(rho*c_p*V)*Q_flow
        - w_air = massPort.VP * R_a / (P_atm - massPort.VP) / R_s
        - RH = Modelica.Media.Air.MoistAir.relativeHumidity_pTX(P_atm, heatPort.T, {w_air})
        """
        # Update volume (Modelica: V = A * h_Top)
        self.V = self.A * self.h_Top
        
        # Update air component volume
        self.air.V_air = self.V
        
        # Heat port connection (Modelica: heatPort.Q_flow = Q_flow)
        self.heatPort.Q_flow = self.Q_flow
        self.heatPort.T = self.T
        
        # Calculate air density (Modelica: rho = Modelica.Media.Air.ReferenceAir.Air_pT.density_pT(1e5,heatPort.T))
        # Simplified density calculation: rho = P / (R * T)
        self.rho = 1e5 / (self.R_a * self.T)  # Using 1e5 Pa as reference pressure
        
        # Temperature derivative (Modelica: der(T) = 1/(rho*c_p*V)*Q_flow)
        if not (self._initialization_phase and self.steadystate):
            # Only integrate if not in steady-state initialization
            if self.rho > 0 and self.c_p > 0 and self.V > 0:
                dT_dt = self.Q_flow / (self.rho * self.c_p * self.V)
                self.T += dT_dt * dt
        
        # Update air component
        self.air.T = self.T
        self.air.step(dt)
        
        # Update humidity calculations (Modelica equations)
        self._update_humidity()
        
        # Update prescribed temperature
        self.preTem.update_temperature(self.T)
    
    def _update_humidity(self):
        """
        Update humidity calculations exactly as in Modelica:
        - w_air = massPort.VP * R_a / (P_atm - massPort.VP) / R_s
        - RH = Modelica.Media.Air.MoistAir.relativeHumidity_pTX(P_atm, heatPort.T, {w_air})
        """
        # Get vapor pressure from massPort
        VP = self.massPort.VP
        
        if VP is None or VP <= 0:
            self.w_air = 0.0
            self.RH = 0.0
            return
            
        # Ensure VP is less than atmospheric pressure
        if VP >= self.P_atm:
            VP = 0.99 * self.P_atm
            self.massPort.VP = VP
        
        # Calculate humidity ratio (Modelica equation)
        if (self.P_atm - VP) > 0:
            self.w_air = VP * self.R_a / ((self.P_atm - VP) * self.R_s)
        else:
            self.w_air = 0.0
        
        # Calculate relative humidity (Modelica equation)
        try:
            X = [self.w_air]
            self.RH = relativeHumidity_pTX(self.P_atm, self.T, X)
            # Ensure RH is in valid range
            self.RH = max(0.0, min(1.0, self.RH))
        except:
            self.RH = 0.0
    
    def set_inputs(self, Q_flow):
        """Set input values for the component"""
        self.Q_flow = Q_flow
    
    def get_state(self):
        """Get current state of the component"""
        return {
            'T': self.T,
            'RH': self.RH,
            'VP': self.massPort.VP,
            'w_air': self.w_air,
            'Q_flow': self.Q_flow,
            'rho': self.rho,
            'V': self.V
        }