from typing import List
import numpy as np
from .BaseClasses.PartialHeatTransferZones import PartialHeatTransferZones

class MassFlowDependence(PartialHeatTransferZones):
    """
    Heat transfer model with mass flow rate dependence
    
    This model extends PartialHeatTransferZones and computes the heat transfer
    coefficient based on the mass flow rate ratio raised to the power of 0.8.
    
    Attributes:
        n (int): Number of nodes
        Mdotnom (float): Nominal mass flow rate [kg/s]
        Unom_l (float): Nominal heat transfer coefficient for liquid [W/(m²·K)]
        Unom_tp (float): Nominal heat transfer coefficient for two-phase [W/(m²·K)]
        Unom_v (float): Nominal heat transfer coefficient for vapor [W/(m²·K)]
        M_dot (float): Mass flow rate [kg/s]
        x (float): Vapor quality
        T_fluid (List[float]): Fluid temperature at each node [K]
        FluidState (List[dict]): Fluid thermodynamic state at each node
        Unom (float): Average nominal heat transfer coefficient [W/(m²·K)]
        U (List[float]): Heat transfer coefficients for each node [W/(m²·K)]
    """
    
    def __init__(self, n: int = 1, Mdotnom: float = 0.0, 
                 Unom_l: float = 0.0, Unom_tp: float = 0.0, Unom_v: float = 0.0,
                 M_dot: float = 0.0, x: float = 0.0, 
                 T_fluid: List[float] = None, FluidState: List[dict] = None):
        """
        Initialize mass flow dependent heat transfer model
        
        Args:
            n (int): Number of nodes (default: 1)
            Mdotnom (float): Nominal mass flow rate [kg/s]
            Unom_l (float): Nominal heat transfer coefficient for liquid [W/(m²·K)]
            Unom_tp (float): Nominal heat transfer coefficient for two-phase [W/(m²·K)]
            Unom_v (float): Nominal heat transfer coefficient for vapor [W/(m²·K)]
            M_dot (float): Mass flow rate [kg/s]
            x (float): Vapor quality
            T_fluid (List[float]): Fluid temperature at each node [K]
            FluidState (List[dict]): Fluid thermodynamic state at each node
        """
        super().__init__(n, Mdotnom, Unom_l, Unom_tp, Unom_v, M_dot, x, T_fluid)
        
        # Initialize heat transfer coefficients array
        self.U = [0.0] * n
        self.Unom = (Unom_l + Unom_tp + Unom_v) / 3
        
        # Initialize fluid state
        if FluidState is None:
            self.FluidState = [{} for _ in range(n)]
        else:
            self.FluidState = FluidState
    
    def calculate(self) -> None:
        """
        Calculate heat transfer coefficients and heat flux
        
        The heat transfer coefficient is calculated based on the mass flow rate
        ratio raised to the power of 0.8, with a small offset to prevent zero values.
        """
        for i in range(self.n):
            # Calculate heat transfer coefficient based on mass flow rate
            # Use noEvent equivalent (simple calculation without event handling)
            mass_flow_ratio = abs(self.M_dot / self.Mdotnom) if self.Mdotnom != 0 else 0
            self.U[i] = self.Unom * (0.00001 + mass_flow_ratio ** 0.8)
            
            # Calculate heat flux
            self.q_dot[i] = self.U[i] * (self.thermalPortL[i].T - self.T_fluid[i])
    
    def __str__(self) -> str:
        """String representation of the mass flow dependent heat transfer model"""
        return (f"Mass Flow Dependent Heat Transfer Model\n"
                f"n = {self.n}\n"
                f"M_dot/Mdotnom = {self.M_dot/self.Mdotnom:.2f}\n"
                f"Unom = {self.Unom:.2f} W/(m²·K)\n"
                f"U = {self.U} W/(m²·K)\n"
                f"q_dot = {self.q_dot} W/m²")
