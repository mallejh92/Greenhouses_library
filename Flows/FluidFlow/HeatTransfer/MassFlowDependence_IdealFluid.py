from typing import List
import numpy as np
from .BaseClasses.PartialHeatTransferZones_IdealFluid import PartialHeatTransferZones_IdealFluid

class MassFlowDependence_IdealFluid(PartialHeatTransferZones_IdealFluid):
    """
    Heat transfer model with mass flow rate dependence for ideal fluid
    
    This model extends PartialHeatTransferZones_IdealFluid and computes the heat
    transfer coefficient based on the mass flow rate ratio raised to the power of 0.8.
    
    Attributes:
        Mdotnom (float): Nominal mass flow rate [kg/s]
        Unom_l (float): Nominal heat transfer coefficient for liquid [W/(m²·K)]
        Unom_tp (float): Nominal heat transfer coefficient for two-phase [W/(m²·K)]
        Unom_v (float): Nominal heat transfer coefficient for vapor [W/(m²·K)]
        M_dot (float): Mass flow rate [kg/s]
        x (float): Vapor quality
        T_fluid (float): Fluid temperature [K]
        Unom (float): Average nominal heat transfer coefficient [W/(m²·K)]
        U (float): Heat transfer coefficient [W/(m²·K)]
    """
    
    def __init__(self, Mdotnom: float = 0.0, 
                 Unom_l: float = 0.0, Unom_tp: float = 0.0, Unom_v: float = 0.0,
                 M_dot: float = 0.0, x: float = 0.0):
        """
        Initialize mass flow dependent heat transfer model for ideal fluid
        
        Args:
            Mdotnom (float): Nominal mass flow rate [kg/s]
            Unom_l (float): Nominal heat transfer coefficient for liquid [W/(m²·K)]
            Unom_tp (float): Nominal heat transfer coefficient for two-phase [W/(m²·K)]
            Unom_v (float): Nominal heat transfer coefficient for vapor [W/(m²·K)]
            M_dot (float): Mass flow rate [kg/s]
            x (float): Vapor quality
        """
        # Calculate average nominal heat transfer coefficient
        Unom = (Unom_l + Unom_tp + Unom_v) / 3
        
        # Call parent class constructor
        super().__init__(n=1, Mdotnom=Mdotnom, Unom=Unom, M_dot=M_dot)
        
        # Store additional parameters
        self.Unom_l = Unom_l
        self.Unom_tp = Unom_tp
        self.Unom_v = Unom_v
        self.x = x
        
        # Initialize heat transfer coefficient
        self.U = 0.0
        self.Unom = Unom
    
    def calculate(self) -> None:
        """
        Calculate heat transfer coefficient and heat flux
        
        The heat transfer coefficient is calculated based on the mass flow rate
        ratio raised to the power of 0.8, with a small offset to prevent zero values.
        """
        # Calculate heat transfer coefficient based on mass flow rate
        self.U = self.Unom * (0.00001 + abs(self.M_dot / self.Mdotnom) ** 0.8)
        
        # Calculate heat flux for each node
        for i in range(self.n):
            self.q_dot[i] = self.U * (self.thermalPortL[i].T - self.T_fluid)
    
    def __str__(self) -> str:
        """String representation of the mass flow dependent heat transfer model for ideal fluid"""
        return (f"Mass Flow Dependent Heat Transfer Model (Ideal Fluid)\n"
                f"M_dot/Mdotnom = {self.M_dot/self.Mdotnom:.2f}\n"
                f"Unom = {self.Unom:.2f} W/(m²·K)\n"
                f"U = {self.U:.2f} W/(m²·K)\n"
                f"q_dot = {self.q_dot} W/m²")
