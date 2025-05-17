from typing import List
import numpy as np
from Interfaces.Heat.ThermalPortL import ThermalPortL
from .BaseClasses.PartialHeatTransferZones import PartialHeatTransferZones

class Constant(PartialHeatTransferZones):
    """
    Constant heat transfer coefficient model
    
    This model computes a constant heat transfer coefficient as an average between
    the liquid, two-phase, and vapor terms.
    
    Attributes:
        U_0 (float): Heat transfer coefficient [W/(m²·K)]
    """
    
    def __init__(self, n: int = 1, Mdotnom: float = 0.0, 
                 Unom_l: float = 0.0, Unom_tp: float = 0.0, Unom_v: float = 0.0,
                 M_dot: float = 0.0, x: float = 0.0, 
                 T_fluid: List[float] = None):
        """
        Initialize Constant heat transfer model
        
        Args:
            n (int): Number of nodes (default: 1)
            Mdotnom (float): Nominal mass flow rate [kg/s]
            Unom_l (float): Nominal heat transfer coefficient for liquid [W/(m²·K)]
            Unom_tp (float): Nominal heat transfer coefficient for two-phase [W/(m²·K)]
            Unom_v (float): Nominal heat transfer coefficient for vapor [W/(m²·K)]
            M_dot (float): Mass flow rate [kg/s]
            x (float): Vapor quality
            T_fluid (List[float]): Fluid temperature at each node [K]
        """
        super().__init__(n, Mdotnom, Unom_l, Unom_tp, Unom_v, M_dot, x, T_fluid)
        self.U_0 = (Unom_l + Unom_tp + Unom_v) / 3  # Average heat transfer coefficient
    
    def calculate(self) -> None:
        """
        Calculate heat flux for each node
        
        This method implements the Modelica equation:
        q_dot = {U_0*(thermalPortL[i].T - T_fluid[i]) for i in 1:n}
        """
        for i in range(self.n):
            self.q_dot[i] = self.U_0 * (self.thermalPortL[i].T - self.T_fluid[i])
    
    def __str__(self) -> str:
        """String representation of the heat transfer model"""
        return (f"Constant Heat Transfer Model\n"
                f"U_0 = {self.U_0:.2f} W/(m²·K)\n"
                f"q_dot = {self.q_dot} W/m²")
