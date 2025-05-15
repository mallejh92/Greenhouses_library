import numpy as np
from typing import Optional

class Pump_Mdot:
    """
    Pump model with prescribed mass flow rate
    
    This model represents a pump where the mass flow rate is prescribed by an external signal.
    """
    
    def __init__(self, 
                 Mdot_0: float = 1.0,
                 eta_is: float = 1.0,
                 NeglectDELTAh: bool = True):
        """
        Initialize pump model
        
        Parameters:
            Mdot_0 (float): Mass flow if external signal not connected [kg/s]
            eta_is (float): Overall Isentropic efficiency of the pump
            NeglectDELTAh (bool): If true, neglects the enthalpy difference due to the compression
        """
        # Parameters
        self.Mdot_0 = Mdot_0
        self.eta_is = eta_is
        self.NeglectDELTAh = NeglectDELTAh
        
        # State variables
        self.Mdot = Mdot_0  # Mass flow rate [kg/s]
        self.h = 0.0  # Fluid specific enthalpy [J/kg]
        self.p = 0.0  # Inlet pressure [Pa]
        self.rho = 1000.0  # Liquid density [kg/m3]
        self.Wdot = 0.0  # Power Consumption [W]
        
        # Port variables
        self.inlet = {
            'm_flow': 0.0,  # Mass flow rate [kg/s]
            'p': 0.0,  # Pressure [Pa]
            'h_outflow': 0.0  # Specific enthalpy [J/kg]
        }
        
        self.outlet = {
            'm_flow': 0.0,  # Mass flow rate [kg/s]
            'p': 0.0,  # Pressure [Pa]
            'h_outflow': 0.0  # Specific enthalpy [J/kg]
        }
        
    def density_phX(self, p: float, h: float, X: Optional[np.ndarray] = None) -> float:
        """
        Calculate density from pressure, enthalpy and composition
        
        Parameters:
            p (float): Pressure [Pa]
            h (float): Specific enthalpy [J/kg]
            X (np.ndarray, optional): Composition vector
            
        Returns:
            float: Density [kg/m3]
        """
        # Simplified water properties
        return 1000.0  # Constant density for water
        
    def update(self, 
              flow_in: Optional[float] = None,
              inlet_p: float = 0.0,
              inlet_h_outflow: float = 0.0,
              outlet_p: float = 0.0,
              outlet_h_outflow: float = 0.0) -> tuple:
        """
        Update pump model state
        
        Parameters:
            flow_in (float, optional): External mass flow rate signal [kg/s]
            inlet_p (float): Inlet pressure [Pa]
            inlet_h_outflow (float): Inlet specific enthalpy [J/kg]
            outlet_p (float): Outlet pressure [Pa]
            outlet_h_outflow (float): Outlet specific enthalpy [J/kg]
            
        Returns:
            tuple: (Mdot, Wdot) Mass flow rate and power consumption
        """
        # Update mass flow rate
        self.Mdot = flow_in if flow_in is not None else self.Mdot_0
        
        # Update port values
        self.inlet['p'] = inlet_p
        self.inlet['h_outflow'] = inlet_h_outflow
        self.outlet['p'] = outlet_p
        self.outlet['h_outflow'] = outlet_h_outflow
        
        # Calculate enthalpy and pressure based on flow direction
        if self.Mdot <= 0:
            self.h = outlet_h_outflow
            self.p = outlet_p
        else:
            self.h = inlet_h_outflow
            self.p = inlet_p
            
        # Calculate density
        self.rho = self.density_phX(self.p, self.h)
        
        # Calculate power consumption
        self.Wdot = self.Mdot * (self.outlet['p'] - self.inlet['p']) / self.rho / self.eta_is
        
        # Calculate enthalpy difference
        if self.NeglectDELTAh:
            self.outlet['h_outflow'] = self.inlet['h_outflow']
            self.inlet['h_outflow'] = self.outlet['h_outflow']
        else:
            self.outlet['h_outflow'] = self.inlet['h_outflow'] + (self.outlet['p'] - self.inlet['p']) / self.rho / self.eta_is
            self.inlet['h_outflow'] = self.outlet['h_outflow'] + (self.inlet['p'] - self.outlet['p']) / self.rho / self.eta_is
            
        # Update mass flow
        self.inlet['m_flow'] = self.Mdot
        self.outlet['m_flow'] = -self.Mdot
        
        return self.Mdot, self.Wdot
