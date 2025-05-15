import numpy as np
from typing import Optional
from Functions.Enumerations.PressureDrops import PressureDrops
from Functions.TestRig.PressureDropCorrelation_HP import PressureDropCorrelation_HP
from Functions.TestRig.PressureDropCorrelation_LP import PressureDropCorrelation_LP

class Pdrop:
    """
    Linear pressure drop model
    
    This model calculates the pressure drop in a fluid flow system based on the selected pressure drop type.
    """
    
    def __init__(self, 
                 DPtype: PressureDrops = PressureDrops.UD,
                 p_su_start: float = 1e5,
                 DELTAp_start: float = 10000,
                 Mdot_start: float = 0.1,
                 Mdot_max: float = 0.1,
                 DELTAp_max: float = 20e5):
        """
        Initialize pressure drop model
        
        Parameters:
            DPtype (PressureDrops): Type of pressure drop model
            p_su_start (float): Inlet pressure start value [Pa]
            DELTAp_start (float): Start value for the pressure drop [Pa]
            Mdot_start (float): Mass flow rate initial value [kg/s]
            Mdot_max (float): Flow rate at DELTAp_max [kg/s]
            DELTAp_max (float): Pressure drop at Mdot_max [Pa]
        """
        # Parameters
        self.DPtype = DPtype
        self.p_su_start = p_su_start
        self.DELTAp_start = DELTAp_start
        self.Mdot_start = Mdot_start
        self.Mdot_max = Mdot_max
        self.DELTAp_max = DELTAp_max
        
        # State variables
        self.Mdot = Mdot_start  # Mass flow rate [kg/s]
        self.DELTAp = DELTAp_start  # Pressure drop [Pa]
        
        # Port variables
        self.InFlow = {
            'm_flow': 0.0,  # Mass flow rate [kg/s]
            'p': p_su_start,  # Pressure [Pa]
            'h_outflow': 0.0  # Specific enthalpy [J/kg]
        }
        
        self.OutFlow = {
            'm_flow': 0.0,  # Mass flow rate [kg/s]
            'p': p_su_start - DELTAp_start,  # Pressure [Pa]
            'h_outflow': 0.0  # Specific enthalpy [J/kg]
        }
        
    def update(self, 
              InFlow_p: float,
              InFlow_h_outflow: float,
              OutFlow_p: float,
              OutFlow_h_outflow: float) -> tuple:
        """
        Update pressure drop model state
        
        Parameters:
            InFlow_p (float): Inlet pressure [Pa]
            InFlow_h_outflow (float): Inlet specific enthalpy [J/kg]
            OutFlow_p (float): Outlet pressure [Pa]
            OutFlow_h_outflow (float): Outlet specific enthalpy [J/kg]
            
        Returns:
            tuple: (Mdot, DELTAp) Mass flow rate and pressure drop
        """
        # Update port values
        self.InFlow['p'] = InFlow_p
        self.InFlow['h_outflow'] = InFlow_h_outflow
        self.OutFlow['p'] = OutFlow_p
        self.OutFlow['h_outflow'] = OutFlow_h_outflow
        
        # Calculate pressure drop based on type
        if self.DPtype == PressureDrops.ORCnextHP:
            self.Mdot = self.InFlow['m_flow']
            self.DELTAp = PressureDropCorrelation_HP(M_flow=self.Mdot)
            self.OutFlow['p'] = self.InFlow['p'] - self.DELTAp
            
        elif self.DPtype == PressureDrops.ORCnextLP:
            self.Mdot = self.InFlow['m_flow']
            self.DELTAp = PressureDropCorrelation_LP(M_flow=self.Mdot)
            self.OutFlow['p'] = self.InFlow['p'] - self.DELTAp
            
        else:  # User defined
            self.DELTAp = self.InFlow['p'] - self.OutFlow['p']
            self.Mdot = self.Mdot_max * self.DELTAp / self.DELTAp_max
            
        # Mass balance
        self.OutFlow['m_flow'] = -self.InFlow['m_flow']
        
        # Enthalpy balance
        self.InFlow['h_outflow'] = self.OutFlow['h_outflow']
        self.OutFlow['h_outflow'] = self.InFlow['h_outflow']
        
        return self.Mdot, self.DELTAp
