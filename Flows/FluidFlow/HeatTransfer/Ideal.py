from typing import List
from .BaseClasses.PartialHeatTransferZones import PartialHeatTransferZones

class Ideal(PartialHeatTransferZones):
    """
    Ideal heat transfer without thermal resistance
    
    This model extends PartialHeatTransferZones to implement an ideal heat transfer
    model where there is no thermal resistance between the fluid and the wall.
    
    Attributes:
        n (int): Number of nodes
        Mdotnom (float): Nominal mass flow rate [kg/s]
        Unom_l (float): Nominal heat transfer coefficient for liquid [W/(m²·K)]
        Unom_tp (float): Nominal heat transfer coefficient for two-phase [W/(m²·K)]
        Unom_v (float): Nominal heat transfer coefficient for vapor [W/(m²·K)]
        M_dot (float): Mass flow rate [kg/s]
        x (float): Vapor quality
        T_fluid (List[float]): Fluid temperature at each node [K]
    """
    
    def __init__(self, n: int = 1, Mdotnom: float = 0.0, 
                 Unom_l: float = 0.0, Unom_tp: float = 0.0, Unom_v: float = 0.0,
                 M_dot: float = 0.0, x: float = 0.0, 
                 T_fluid: List[float] = None):
        """
        Initialize ideal heat transfer model
        
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
    
    def calculate(self) -> None:
        """
        Calculate heat transfer for ideal case
        
        In the ideal case, the fluid temperature equals the wall temperature
        and there is no thermal resistance.
        """
        for i in range(self.n):
            # In ideal case, fluid temperature equals wall temperature
            self.T_fluid[i] = self.thermalPortL[i].T
            # Heat flux is calculated based on the temperature difference
            self.q_dot[i] = self.thermalPortL[i].phi
    
    def __str__(self) -> str:
        """String representation of the ideal heat transfer model"""
        return (f"Ideal Heat Transfer Model\n"
                f"n = {self.n}\n"
                f"T_fluid = {self.T_fluid} K\n"
                f"q_dot = {self.q_dot} W/m²")
