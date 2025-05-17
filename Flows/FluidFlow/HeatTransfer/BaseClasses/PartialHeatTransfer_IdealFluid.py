from typing import List
from .PartialHeatTransfer import PartialHeatTransfer
from Interfaces.Heat.ThermalPortL import ThermalPortL

class PartialHeatTransfer_IdealFluid(PartialHeatTransfer):
    """
    Basic component for partial heat transfer model for ideal fluid
    
    This is the base class for heat transfer models that handle heat transfer
    between an ideal fluid and its boundary through thermal ports.
    
    Attributes:
        n (int): Number of heat transfer segments
        q_dot (List[float]): Heat flux [W/m²]
        thermalPortL (List[ThermalPortL]): Array of thermal ports
    """
    
    def __init__(self, n: int = 1):
        """
        Initialize partial heat transfer model for ideal fluid
        
        Args:
            n (int): Number of heat transfer segments (default: 1)
        """
        super().__init__(n)
        
        # Initialize thermal ports
        self.thermalPortL = [ThermalPortL() for _ in range(n)]
    
    def calculate(self) -> None:
        """
        Calculate heat flux for each segment
        
        For ideal fluid, the heat flux is equal to the heat flow rate (phi)
        from the thermal port.
        """
        for i in range(self.n):
            self.q_dot[i] = self.thermalPortL[i].phi
    
    def __str__(self) -> str:
        """String representation of the heat transfer model"""
        return (f"Ideal Fluid Heat Transfer Model\n"
                f"n = {self.n}\n"
                f"q_dot = {self.q_dot} W/m²")
