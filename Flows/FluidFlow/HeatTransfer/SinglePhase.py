from typing import List
from .BaseClasses.PartialHeatTransferZones import PartialHeatTransferZones
from .BaseClasses.PartialSinglePhaseCorrelation import PartialSinglePhaseCorrelation

class SinglePhase(PartialHeatTransferZones):
    """
    Single phase heat transfer correlation model
    
    This model extends PartialHeatTransferZones and uses a single phase correlation
    to compute the heat transfer coefficient for each node.
    
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
        liquidCorrelation (PartialSinglePhaseCorrelation): Liquid phase correlation model
    """
    
    def __init__(self, n: int = 1, Mdotnom: float = 0.0, 
                 Unom_l: float = 0.0, Unom_tp: float = 0.0, Unom_v: float = 0.0,
                 M_dot: float = 0.0, x: float = 0.0, 
                 T_fluid: List[float] = None,
                 liquidCorrelation: PartialSinglePhaseCorrelation = None):
        """
        Initialize single phase heat transfer model
        
        Args:
            n (int): Number of nodes (default: 1)
            Mdotnom (float): Nominal mass flow rate [kg/s]
            Unom_l (float): Nominal heat transfer coefficient for liquid [W/(m²·K)]
            Unom_tp (float): Nominal heat transfer coefficient for two-phase [W/(m²·K)]
            Unom_v (float): Nominal heat transfer coefficient for vapor [W/(m²·K)]
            M_dot (float): Mass flow rate [kg/s]
            x (float): Vapor quality
            T_fluid (List[float]): Fluid temperature at each node [K]
            liquidCorrelation (PartialSinglePhaseCorrelation): Liquid phase correlation model
        """
        super().__init__(n, Mdotnom, Unom_l, Unom_tp, Unom_v, M_dot, x, T_fluid)
        
        # Initialize heat transfer coefficients array
        self.U = [0.0] * n
        
        # Set up liquid correlation model
        self.liquidCorrelation = liquidCorrelation
        if self.liquidCorrelation is not None:
            self.liquidCorrelation.state = self.FluidState[0]
            self.liquidCorrelation.m_dot = self.M_dot
            self.liquidCorrelation.q_dot = self.q_dot[0]
    
    def calculate(self) -> None:
        """
        Calculate heat transfer coefficients and heat flux
        
        The heat transfer coefficient is calculated using the liquid correlation model
        for each node.
        """
        # Update liquid correlation model parameters
        if self.liquidCorrelation is not None:
            self.liquidCorrelation.state = self.FluidState[0]
            self.liquidCorrelation.m_dot = self.M_dot
            self.liquidCorrelation.q_dot = self.q_dot[0]
            
            # Calculate heat transfer coefficient using correlation
            self.liquidCorrelation.calculate()
            
            # Apply the same heat transfer coefficient to all nodes
            for i in range(self.n):
                self.U[i] = self.liquidCorrelation.U
                self.q_dot[i] = self.U[i] * (self.thermalPortL[i].T - self.T_fluid[i])
    
    def __str__(self) -> str:
        """String representation of the single phase heat transfer model"""
        return (f"Single Phase Heat Transfer Model\n"
                f"n = {self.n}\n"
                f"U = {self.U} W/(m²·K)\n"
                f"q_dot = {self.q_dot} W/m²")
