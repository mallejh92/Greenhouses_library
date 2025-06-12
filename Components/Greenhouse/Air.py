import numpy as np
from Components.Greenhouse.BasicComponents.AirVP import AirVP
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Interfaces.Heat.HeatFluxVectorInput import HeatFluxVectorInput
from Interfaces.Heat.HeatFluxInput import HeatFlux
from Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature import PrescribedTemperature

class Air:
    def __init__(self, A, h_Air=4.0, rho=1.2, c_p=1000.0, T_start=298.0, N_rad=2, steadystate=False, steadystateVP=True):
        """
        Initialize Air component
        
        Parameters:
        -----------
        A : float
            Floor area [m²]
        h_Air : float
            Air layer height [m]
        rho : float
            Air density [kg/m³]
        c_p : float
            Specific heat capacity [J/(kg·K)]
        T_start : float
            Initial temperature [K]
        N_rad : int
            Number of radiation inputs
        steadystate : bool
            Whether to use steady state initialization
        steadystateVP : bool
            Whether to use steady state initialization for vapor pressure
        """
        # Parameters
        self.A = A
        self.h_Air = h_Air
        self.rho = rho
        self.c_p = c_p
        self.V = A * h_Air  # Volume [m³]
        self.N_rad = N_rad
        self.steadystate = steadystate
        self.steadystateVP = steadystateVP
        
        # Constants
        self.R_a = 287.0  # Gas constant for dry air [J/(kg·K)]
        self.R_s = 461.5  # Gas constant for water vapor [J/(kg·K)]
        self.P_atm = 101325.0  # Atmospheric pressure [Pa]
        
        # Components
        self.heatPort = HeatPort_a(T_start=T_start)
        self.massPort = WaterMassPort_a()
        self.R_Air_Glob = HeatFluxVectorInput([HeatFlux(0.0)] * N_rad)
        self.airVP = AirVP(V_air=self.V, steadystate=steadystateVP)
        self.preTem = PrescribedTemperature(T_start=T_start)
        
        # Connect components
        self.airVP.connect(self.massPort)
        self.preTem.connect_port(self.heatPort)
        
        # State variables
        self.T = T_start  # Temperature [K]
        self._VP = None  # VP는 setter를 통해 설정
        self.RH = 0.5    # Relative humidity [-]
        self.w_air = 0.0 # Humidity ratio [kg/kg]
        
        # Calculate initial vapor pressure based on T_start and RH_out
        T_C = T_start - 273.15
        Psat = 610.78 * np.exp(17.269 * T_C / (T_C + 237.3))
        self.VP = 0.5 * Psat  # 초기 RH를 50%로 설정
        
        # Input variables
        self.Q_flow = 0.0  # Heat flow rate [W]
        self.P_Air = 0.0   # Power from radiation [W]
        
        # Initialize radiation port
        self.R_Air_Glob.flux = np.zeros(N_rad)
        self.R_Air_Glob.values = [HeatFlux(0.0) for _ in range(N_rad)]
        
        # 초기 습도 계산
        self.update_humidity()
    
    @property
    def VP(self):
        """Get vapor pressure"""
        return self._VP

    @VP.setter
    def VP(self, value):
        """Set vapor pressure and update components"""
        self._VP = value
        if hasattr(self, 'massPort'):
            self.massPort.VP = value
            self.airVP.set_prescribed_pressure(value)
        self.update_humidity()

    @property
    def massPort_VP(self):
        """Get massPort vapor pressure"""
        return self.massPort.VP if hasattr(self, 'massPort') else None

    @massPort_VP.setter
    def massPort_VP(self, value):
        """Set massPort vapor pressure"""
        if hasattr(self, 'massPort'):
            self._VP = value
            self.massPort.VP = value
            self.airVP.set_prescribed_pressure(value)
            self.VP = value
            self.update_humidity()

    def compute_power_input(self):
        """Calculate power input from radiation"""
        if len(self.R_Air_Glob.values) == 0:
            return 0.0
        # Sum numeric heat flux values
        total_flux = sum(hf.value for hf in self.R_Air_Glob.values)
        self.P_Air = total_flux * self.A
        return self.P_Air
    
    def compute_derivatives(self):
        """Compute temperature derivative"""
        if self.steadystate:
            return 0.0
        
        # Update density based on current temperature
        self.rho = self.P_atm / (self.R_a * self.T)
        
        # Compute temperature derivative (Modelica equation)
        return (self.Q_flow + self.P_Air) / (self.rho * self.c_p * self.V)
    
    def update_humidity(self):
        """Update humidity calculations"""
        if self._VP is None:
            return
            
        # Calculate humidity ratio (Modelica equation)
        self.w_air = self._VP * self.R_a / ((self.P_atm - self._VP) * self.R_s)
        
        # Calculate relative humidity using Modelica's MoistAir model
        T_C = self.T - 273.15
        Psat = 610.78 * np.exp(T_C / (T_C + 238.3) * 17.2694)
        self.RH = self._VP / Psat if Psat > 0 else 0.0
        self.RH = np.clip(self.RH, 0, 1)
            
    def step(self, dt):
        """
        Advance simulation by one time step
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        # Update temperature with stability check
        dTdt = self.compute_derivatives()
        
        # Limit temperature change per step to prevent instability
        max_dT = 1.0  # Maximum temperature change per step [K]
        dT = dTdt * dt
        if abs(dT) > max_dT:
            dT = np.sign(dT) * max_dT
            
        self.T += dT
        
        # Update prescribed temperature
        self.preTem.connect_T(self.T)
        self.preTem.calculate()
        
        # Integrate vapour pressure
        self.airVP.step(dt)
        
        # Update air component
        self.airVP.step(dt)

        # Synchronize local VP variable and update humidity
        self._VP = self.airVP.VP
        self.massPort.VP = self._VP
        self.update_humidity()
        
        return self.T, self.RH
    
    def set_inputs(self, Q_flow, R_Air_Glob=None, massPort_VP=None):
        """
        Set input values
        
        Parameters:
        -----------
        Q_flow : float
            Heat flow rate [W]
        R_Air_Glob : list, optional
            List of radiation inputs [W/m²]
        massPort_VP : float, optional
            Vapor pressure [Pa]
        """
        self.Q_flow = Q_flow
        self.heatPort.Q_flow = Q_flow
        
        if R_Air_Glob is not None:
            # HeatFluxOutput 객체인 경우 value 속성을 사용
            self.R_Air_Glob.values = [HeatFlux(v.value if hasattr(v, 'value') else v) for v in R_Air_Glob]
            self.compute_power_input()
            
        if massPort_VP is not None and hasattr(self, 'massPort'):
            self.massPort_VP = massPort_VP
