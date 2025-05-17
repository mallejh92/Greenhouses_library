from typing import List
from .PartialHeatTransfer import PartialHeatTransfer

class PartialHeatTransferZones(PartialHeatTransfer):
    """
    A partial heat transfer model with different HTC for liquid, two-phase and vapour
    
    This model extends PartialHeatTransfer and defines inputs needed to compute
    the convective heat transfer coefficient for a fluid flow.
    
    Attributes:
        Mdotnom (float): Nominal mass flow rate [kg/s]
        Unom_l (float): Nominal heat transfer coefficient liquid side [W/(m²·K)]
        Unom_tp (float): Nominal heat transfer coefficient two phase side [W/(m²·K)]
        Unom_v (float): Nominal heat transfer coefficient vapor side [W/(m²·K)]
        M_dot (float): Mass flow rate [kg/s]
        x (float): Vapor quality
    """
    
    def __init__(self, n: int = 1, Mdotnom: float = 0.0, 
                 Unom_l: float = 0.0, Unom_tp: float = 0.0, Unom_v: float = 0.0,
                 M_dot: float = 0.0, x: float = 0.0, 
                 T_fluid: List[float] = None):
        """
        Initialize heat transfer zones model
        
        Args:
            n (int): Number of nodes
            Mdotnom (float): Nominal mass flow rate [kg/s]
            Unom_l (float): Nominal heat transfer coefficient liquid side [W/(m²·K)]
            Unom_tp (float): Nominal heat transfer coefficient two phase side [W/(m²·K)]
            Unom_v (float): Nominal heat transfer coefficient vapor side [W/(m²·K)]
            M_dot (float): Mass flow rate [kg/s]
            x (float): Vapor quality
            T_fluid (List[float]): Fluid temperature at each node [K]
        """
        super().__init__(n)
        
        # Input parameters
        self.Mdotnom = Mdotnom  # Nominal mass flow rate
        self.Unom_l = Unom_l    # Nominal HTC liquid side
        self.Unom_tp = Unom_tp  # Nominal HTC two phase side
        self.Unom_v = Unom_v    # Nominal HTC vapor side
        self.M_dot = M_dot      # Mass flow rate
        self.x = x              # Vapor quality
        
        # Initialize fluid temperature if provided
        if T_fluid is not None:
            self.T_fluid = T_fluid
    
    def calculate(self) -> None:
        """
        Calculate heat flux for each segment based on fluid phase
        
        The heat transfer coefficient is determined by the vapor quality (x):
        - x < 0: Liquid phase (Unom_l)
        - 0 <= x <= 1: Two-phase (Unom_tp)
        - x > 1: Vapor phase (Unom_v)
        
        Heat flux is calculated as: q_dot = U * (T_fluid - T_wall)
        """
        for i in range(self.n):
            # Determine heat transfer coefficient based on vapor quality
            if self.x < 0:
                U = self.Unom_l
            elif self.x <= 1:
                U = self.Unom_tp
            else:
                U = self.Unom_v
            
            # Calculate heat flux
            self.q_dot[i] = U * (self.T_fluid[i] - self.thermalPortL[i].T)
    
    def calculate_temperature(self, state: dict) -> float:
        """
        Calculate temperature from fluid state
        
        Args:
            state (dict): Thermodynamic state of the fluid containing 'temperature'
            
        Returns:
            float: Temperature [K]
        """
        if 'temperature' not in state:
            raise ValueError("Fluid state must contain 'temperature'")
        return state['temperature']
    
    def __str__(self) -> str:
        """String representation of the heat transfer zones model"""
        return (f"Heat Transfer Zones Model\n"
                f"Mdotnom = {self.Mdotnom:.2f} kg/s\n"
                f"Unom_l = {self.Unom_l:.2f} W/(m²·K)\n"
                f"Unom_tp = {self.Unom_tp:.2f} W/(m²·K)\n"
                f"Unom_v = {self.Unom_v:.2f} W/(m²·K)\n"
                f"M_dot = {self.M_dot:.2f} kg/s\n"
                f"x = {self.x:.2f}")
