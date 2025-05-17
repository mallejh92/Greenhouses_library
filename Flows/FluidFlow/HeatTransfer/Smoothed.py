from typing import List
from .BaseClasses.PartialHeatTransferSmoothed import PartialHeatTransferSmoothed

class Smoothed(PartialHeatTransferSmoothed):
    """
    Smoothed heat transfer model with transitions between different zones
    
    This model extends PartialHeatTransferSmoothed and calculates the heat
    transfer coefficient based on the nominal value and mass flow factor.
    
    Attributes:
        n (int): Number of nodes
        Mdotnom (float): Nominal mass flow rate [kg/s]
        Unom_l (float): Nominal heat transfer coefficient for liquid [W/(m²·K)]
        Unom_tp (float): Nominal heat transfer coefficient for two-phase [W/(m²·K)]
        Unom_v (float): Nominal heat transfer coefficient for vapor [W/(m²·K)]
        M_dot (float): Mass flow rate [kg/s]
        x (float): Vapor quality
        T_fluid (List[float]): Fluid temperature at each node [K]
        U (List[float]): Heat transfer coefficients for each node [W/(m²·K)]
        U_nom (float): Nominal heat transfer coefficient [W/(m²·K)]
        massFlowFactor (float): Mass flow rate factor
    """
    
    def __init__(self, n: int = 1, Mdotnom: float = 0.0, 
                 Unom_l: float = 0.0, Unom_tp: float = 0.0, Unom_v: float = 0.0,
                 M_dot: float = 0.0, x: float = 0.0, 
                 T_fluid: List[float] = None):
        """
        Initialize smoothed heat transfer model
        
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
        
        # Initialize heat transfer coefficients array
        self.U = [0.0] * n
    
    def calculate(self) -> None:
        """
        Calculate heat transfer coefficients and heat flux
        
        The heat transfer coefficient is calculated as:
        U[i] = U_nom * massFlowFactor
        where U_nom is the smoothed heat transfer coefficient from PartialHeatTransferSmoothed
        and massFlowFactor is the mass flow rate factor.
        """
        # Call parent class calculate method to compute U_nom and massFlowFactor
        super().calculate()
        
        # Calculate heat flux for each node
        for i in range(self.n):
            self.q_dot[i] = self.U[i] * (self.thermalPortL[i].T - self.T_fluid[i])
    
    def __str__(self) -> str:
        """String representation of the smoothed heat transfer model"""
        return (f"Smoothed Heat Transfer Model\n"
                f"n = {self.n}\n"
                f"U_nom = {self.U_nom:.1f} W/(m²·K)\n"
                f"massFlowFactor = {self.massFlowFactor:.1f}\n"
                f"U = [{', '.join([f'{u:.1f}' for u in self.U])}] W/(m²·K)\n"
                f"q_dot = [{', '.join([f'{q:.1f}' for q in self.q_dot])}] W/m²")
