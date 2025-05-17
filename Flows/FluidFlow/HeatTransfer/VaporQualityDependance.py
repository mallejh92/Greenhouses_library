from typing import List
import math
from .BaseClasses.PartialHeatTransferZones import PartialHeatTransferZones

class VaporQualityDependance(PartialHeatTransferZones):
    """
    Heat transfer model with smooth transition based on vapor quality
    
    This model extends PartialHeatTransferZones and smooths the value of the heat
    transfer coefficient between the liquid, two-phase and vapor nominal heat
    transfer coefficients using a smooth transition function based on the vapor quality.
    
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
    """
    
    def __init__(self, n: int = 1, Mdotnom: float = 0.0, 
                 Unom_l: float = 0.0, Unom_tp: float = 0.0, Unom_v: float = 0.0,
                 M_dot: float = 0.0, x: float = 0.0, 
                 T_fluid: List[float] = None):
        """
        Initialize vapor quality dependent heat transfer model
        
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
        
        # Transition width parameter
        self.width = 0.1
        
        # Initialize heat transfer coefficients array
        self.U = [0.0] * n
    
    def calculate(self) -> None:
        """
        Calculate heat transfer coefficients and heat flux
        
        The heat transfer coefficient is smoothly transitioned between liquid,
        two-phase, and vapor regions based on the vapor quality.
        """
        for i in range(self.n):
            # Calculate heat transfer coefficient based on vapor quality
            if self.x < -self.width/2:
                self.U[i] = self.Unom_l
            elif self.x < self.width/2:
                # Smooth transition from liquid to two-phase
                self.U[i] = self.Unom_l + (self.Unom_tp - self.Unom_l) * \
                           (1 + math.sin(self.x * math.pi / self.width)) / 2
            elif self.x < 1 - self.width/2:
                self.U[i] = self.Unom_tp
            elif self.x < 1 + self.width/2:
                # Smooth transition from two-phase to vapor
                self.U[i] = self.Unom_tp + (self.Unom_v - self.Unom_tp) * \
                           (1 + math.sin((self.x - 1) * math.pi / self.width)) / 2
            else:
                self.U[i] = self.Unom_v
            
            # Calculate heat flux
            self.q_dot[i] = self.U[i] * (self.thermalPortL[i].T - self.T_fluid[i])
    
    def __str__(self) -> str:
        """String representation of the vapor quality dependent heat transfer model"""
        return (f"Vapor Quality Dependent Heat Transfer Model\n"
                f"n = {self.n}\n"
                f"x = {self.x:.2f}\n"
                f"U = {self.U} W/(m²·K)\n"
                f"q_dot = {self.q_dot} W/m²")
