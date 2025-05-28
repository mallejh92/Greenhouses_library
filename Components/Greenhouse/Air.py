import numpy as np
from BasicComponents.AirVP import AirVP
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Interfaces.Heat.HeatFluxVectorInput import HeatFluxVectorInput

class Air:
    def __init__(self, A, h_Air=4.0, rho=1.2, c_p=1000.0, T_start=298.0, N_rad=2, steadystate=False, steadystateVP=True):
        # Parameters
        self.A = A
        self.h_Air = h_Air
        self.rho = rho
        self.c_p = c_p
        self.N_rad = N_rad
        self.P_atm = 101325.0
        self.R_a = 287.0
        self.R_s = 461.5
        self.T = T_start
        self.V = self.A * self.h_Air
        
        # Variables
        self.Q_flow = 0.0
        self.P_Air = 0.0
        self.RH = 0.0
        self.w_air = 0.0
        self.VP = 0.0  # Vapor pressure [Pa]
        
        # State flags
        self.steadystate = steadystate
        self.steadystateVP = steadystateVP
        
        # Ports
        self.heatPort = HeatPort_a(T_start=T_start)
        self.massPort = WaterMassPort_a()
        self.R_Air_Glob = HeatFluxVectorInput(N_rad)
        
        # Components
        self.airVP = AirVP(V_air=self.V, steadystate=steadystateVP)
        
        # Connect ports
        self.airVP.port = self.massPort
    
    def compute_power_input(self):
        """Calculate power input from radiation"""
        if len(self.R_Air_Glob.flux) == 0:
            return 0.0
        return np.sum(self.R_Air_Glob.flux) * self.A
    
    def compute_derivatives(self):
        """Calculate temperature derivative"""
        self.P_Air = self.compute_power_input()
        return (self.Q_flow + self.P_Air) / (self.rho * self.c_p * self.V)
    
    def update_humidity(self):
        """Update humidity calculations"""
        # Update VP from massPort
        self.VP = self.massPort.VP
            
        # Calculate humidity ratio
        self.w_air = self.VP * self.R_a / ((self.P_atm - self.VP) * self.R_s)
        
        # Calculate relative humidity using Modelica's MoistAir model approximation
        T_C = self.T - 273.15
        Psat = 610.78 * np.exp(T_C / (T_C + 238.3) * 17.2694)
        self.RH = self.VP / Psat
        self.RH = np.clip(self.RH, 0, 1)
    
    def step(self, dt):
        """Advance simulation by one time step"""
        # Update temperature with stability check
        dTdt = self.compute_derivatives()
        
        # Limit temperature change per step to prevent instability
        max_dT = 1.0  # Maximum temperature change per step [K]
        dT = dTdt * dt
        if abs(dT) > max_dT:
            dT = np.sign(dT) * max_dT
            
        self.T += dT
        
        # Update humidity
        self.update_humidity()
        
        # Update heat port temperature
        self.heatPort.T = self.T
        
        return self.T, self.RH
    
    def set_inputs(self, Q_flow, R_Air_Glob, massPort_VP):
        """Set input values"""
        self.Q_flow = Q_flow
        
        if R_Air_Glob is None or len(R_Air_Glob) == 0:
            self.R_Air_Glob.flux = np.zeros(self.N_rad)
        else:
            self.R_Air_Glob.flux = np.array(R_Air_Glob)
            
        if massPort_VP is not None:
            self.massPort.VP = massPort_VP
            self.VP = massPort_VP  # Update VP directly