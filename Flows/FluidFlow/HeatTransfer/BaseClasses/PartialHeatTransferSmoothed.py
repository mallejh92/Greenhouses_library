from typing import List
import numpy as np
from .PartialHeatTransferZones import PartialHeatTransferZones

class PartialHeatTransferSmoothed(PartialHeatTransferZones):
    """
    A partial heat transfer model that provides smooth transitions between the HTC 
    for liquid, two-phase and vapour
    
    This model extends PartialHeatTransferZones and smoothes the value of the heat 
    transfer coefficient between the liquid, two-phase and vapour nominal values 
    using transition factors based on the vapour quality value of the fluid flow.
    
    Attributes:
        smoothingRange (float): Vapour quality smoothing range (0 to 1)
        massFlowExp (float): Mass flow correction term (0 to 1)
        forcePhase (int): Phase forcing option (0: Disabled, 1: Liquid, 2: Two-phase, 3: Gaseous)
        U (List[float]): Heat transfer coefficient for each node [W/(m²·K)]
        U_nom_LTP (float): Nominal HTC between liquid and two-phase
        U_nom_TPV (float): Nominal HTC between two-phase and vapour
        U_nom (float): Nominal HTC
        LTP (float): Transition factor between liquid and two-phase
        TPV (float): Transition factor between two-phase and vapour
        LV (float): Transition factor between liquid and vapour
        massFlowFactor (float): Mass flow correction factor
        x_L (float): Lower liquid quality limit
        x_LTP (float): Upper liquid quality limit
        x_TPV (float): Lower vapour quality limit
        x_V (float): Upper vapour quality limit
    """
    
    def __init__(self, n: int = 1, Mdotnom: float = 0.0, 
                 Unom_l: float = 0.0, Unom_tp: float = 0.0, Unom_v: float = 0.0,
                 M_dot: float = 0.0, x: float = 0.0, 
                 T_fluid: List[float] = None,
                 smoothingRange: float = 0.2,
                 massFlowExp: float = 0.8,
                 forcePhase: int = 0):
        """
        Initialize smoothed heat transfer model
        
        Args:
            n (int): Number of nodes
            Mdotnom (float): Nominal mass flow rate [kg/s]
            Unom_l (float): Nominal heat transfer coefficient for liquid [W/(m²·K)]
            Unom_tp (float): Nominal heat transfer coefficient for two-phase [W/(m²·K)]
            Unom_v (float): Nominal heat transfer coefficient for vapour [W/(m²·K)]
            M_dot (float): Mass flow rate [kg/s]
            x (float): Vapor quality
            T_fluid (List[float]): Fluid temperature at each node [K]
            smoothingRange (float): Vapour quality smoothing range (0 to 1)
            massFlowExp (float): Mass flow correction term (0 to 1)
            forcePhase (int): Phase forcing option
        """
        super().__init__(n, Mdotnom, Unom_l, Unom_tp, Unom_v, M_dot, x, T_fluid)
        
        # Parameters
        self.smoothingRange = max(0, min(1, smoothingRange))
        self.massFlowExp = max(0, min(1, massFlowExp))
        self.forcePhase = forcePhase
        
        # Initialize arrays
        self.U = [0.0] * n
        self.U_nom_LTP = 0.0
        self.U_nom_TPV = 0.0
        self.U_nom = 0.0
        
        # Transition factors
        self.LTP = 0.0
        self.TPV = 0.0
        self.LV = 0.0
        self.massFlowFactor = 0.0
        
        # Quality limits
        self.divisor = 10
        self.x_L = 0 - self.smoothingRange/self.divisor
        self.x_LTP = 0 + self.smoothingRange/self.divisor
        self.x_TPV = 1 - self.smoothingRange/self.divisor
        self.x_V = 1 + self.smoothingRange/self.divisor
    
    def transition_factor_alt(self, switch: int, trans: float, position: float) -> float:
        """
        Alternative transition factor calculation
        
        Args:
            switch (int): Switch point (0 or 1)
            trans (float): Transition range
            position (float): Current position
            
        Returns:
            float: Transition factor
        """
        if switch == 0:  # Liquid to two-phase transition
            return max(0, min(1, (position - self.x_L) / (self.x_LTP - self.x_L)))
        else:  # Two-phase to vapour transition
            return max(0, min(1, (position - self.x_TPV) / (self.x_V - self.x_TPV)))
    
    def transition_factor(self, start: float, stop: float, position: float) -> float:
        """
        Standard transition factor calculation
        
        Args:
            start (float): Start position
            stop (float): Stop position
            position (float): Current position
            
        Returns:
            float: Transition factor
        """
        return max(0, min(1, (position - start) / (stop - start)))
    
    def calculate(self) -> None:
        """
        Calculate heat transfer coefficients and transition factors
        """
        # Calculate transition factors based on forcePhase
        if self.forcePhase == 0:
            self.LTP = self.transition_factor_alt(0, self.smoothingRange, self.x)
            self.TPV = self.transition_factor_alt(1, self.smoothingRange, self.x)
            self.LV = self.transition_factor(0, 1, self.x)
        elif self.forcePhase == 1:  # liquid only
            self.LTP = 0
            self.TPV = 1
            self.LV = 0
        elif self.forcePhase == 2:  # two-phase only
            self.LTP = 1
            self.TPV = 0
            self.LV = self.transition_factor(0, 1, self.x)
        elif self.forcePhase == 3:  # gas only
            self.LTP = 0
            self.TPV = 1
            self.LV = 1
        else:
            # Set default values before raising error
            self.LTP = 0.5
            self.TPV = 0.5
            self.LV = 0.5
            raise ValueError("Error in phase determination")
        
        # Calculate nominal heat transfer coefficients
        self.U_nom_LTP = (1 - self.LTP) * self.Unom_l + self.LTP * self.Unom_tp
        self.U_nom_TPV = (1 - self.TPV) * self.Unom_tp + self.TPV * self.Unom_v
        self.U_nom = (1 - self.LV) * self.U_nom_LTP + self.LV * self.U_nom_TPV
        
        # Calculate mass flow correction factor
        self.massFlowFactor = abs(self.M_dot/self.Mdotnom) ** self.massFlowExp
        
        # Calculate final heat transfer coefficients for each node
        for i in range(self.n):
            self.U[i] = self.U_nom * self.massFlowFactor
    
    def __str__(self) -> str:
        """String representation of the heat transfer model"""
        return (f"Smoothed Heat Transfer Model\n"
                f"smoothingRange = {self.smoothingRange:.2f}\n"
                f"massFlowExp = {self.massFlowExp:.2f}\n"
                f"forcePhase = {self.forcePhase}\n"
                f"U_nom = {self.U_nom:.2f} W/(m²·K)\n"
                f"massFlowFactor = {self.massFlowFactor:.2f}")
