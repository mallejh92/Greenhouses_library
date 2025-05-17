from typing import List
from .PartialHeatTransfer_IdealFluid import PartialHeatTransfer_IdealFluid

class DummyThermalPort:
    """간단한 열 포트 클래스"""
    def __init__(self, T: float = 293.15):
        self.T = T

class PartialHeatTransferZones_IdealFluid(PartialHeatTransfer_IdealFluid):
    """
    A partial heat transfer model with one ideal nominal HTC for all zones
    
    This model extends PartialHeatTransfer_IdealFluid and defines inputs needed to compute
    the convective heat transfer coefficient for an ideal fluid flow.
    
    Attributes:
        Mdotnom (float): Nominal mass flow rate [kg/s]
        Unom (float): Nominal heat transfer coefficient [W/(m²·K)]
        M_dot (float): Inlet mass flow rate [kg/s]
        T_fluid (float): Temperature of the fluid [K]
    """
    
    def __init__(self, n: int = 1, Mdotnom: float = 0.0, 
                 Unom: float = 0.0, M_dot: float = 0.0,
                 T_fluid: float = 293.15):
        """
        Initialize heat transfer zones model for ideal fluid
        
        Args:
            n (int): Number of nodes
            Mdotnom (float): Nominal mass flow rate [kg/s]
            Unom (float): Nominal heat transfer coefficient [W/(m²·K)]
            M_dot (float): Inlet mass flow rate [kg/s]
            T_fluid (float): Temperature of the fluid [K]
        """
        super().__init__(n)
        if n <= 0:
            raise ValueError("Number of nodes (n) must be greater than zero.")

        # Input parameters
        self.Mdotnom = Mdotnom  # Nominal mass flow rate
        self.Unom = Unom        # Nominal heat transfer coefficient
        self.M_dot = M_dot      # Inlet mass flow rate
        self.T_fluid = T_fluid  # Fluid temperature
        
        # Initialize arrays
        self.q_dot = [0.0] * n
        self.thermalPortL = [DummyThermalPort() for _ in range(n)]
    
    def calculate(self) -> None:
        """
        Calculate heat flux for each segment using ideal fluid heat transfer model
        
        For ideal fluid, the heat transfer coefficient is constant (Unom) and
        the heat flux is calculated as:
        q_dot = Unom * (T_fluid - T_wall)
        where T_wall is the wall temperature from thermalPortL
        """
        for i in range(self.n):
            self.q_dot[i] = self.Unom * (self.T_fluid - self.thermalPortL[i].T)
    
    def __str__(self) -> str:
        """String representation of the heat transfer zones model"""
        return (f"Ideal Fluid Heat Transfer Zones Model\n"
                f"Mdotnom = {self.Mdotnom:.2f} kg/s\n"
                f"Unom = {self.Unom:.2f} W/(m²·K)\n"
                f"M_dot = {self.M_dot:.2f} kg/s\n"
                f"T_fluid = {self.T_fluid:.2f} K")
