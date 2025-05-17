from typing import List
import numpy as np
from Interfaces.Heat.ThermalPortL import ThermalPortL

class PartialHeatTransfer:
    """
    Basic component for partial heat transfer model
    
    This is the base class for heat transfer models that handle heat transfer
    between a fluid and its boundary through thermal ports.
    
    Attributes:
        n (int): Number of heat transfer segments
        FluidState (List[dict]): Thermodynamic states of flow segments
        q_dot (List[float]): Heat flux [W/m²]
        T_fluid (List[float]): Temperature of the fluid [K]
        thermalPortL (List[ThermalPortL]): Array of thermal ports
    """
    
    def __init__(self, n: int = 1):
        """
        Initialize partial heat transfer model
        
        Args:
            n (int): Number of heat transfer segments (default: 1)
        """
        self.n = n
        
        # Initialize arrays
        self.FluidState = [{} for _ in range(n)]  # Thermodynamic states
        self.q_dot = [0.0] * n  # Heat flux
        self.T_fluid = [293.15] * n  # Fluid temperature
        self.thermalPortL = [ThermalPortL() for _ in range(n)]  # Thermal ports
    
    def update_fluid_state(self, fluid_states: List[dict]) -> None:
        """
        Update fluid states and calculate fluid temperature
        
        Args:
            fluid_states (List[dict]): Thermodynamic states of flow segments
        """
        if len(fluid_states) != self.n:
            raise ValueError(f"Expected {self.n} fluid states, got {len(fluid_states)}")
        
        self.FluidState = fluid_states
        # Calculate fluid temperature from states
        self.T_fluid = [self.calculate_temperature(state) for state in fluid_states]
    
    def calculate_temperature(self, state: dict) -> float:
        """
        Calculate temperature from fluid state
        
        This method should be overridden by subclasses to calculate
        temperature based on the specific medium properties.
        
        Args:
            state (dict): Thermodynamic state of the fluid
            
        Returns:
            float: Temperature [K]
        """
        raise NotImplementedError("Subclasses must implement calculate_temperature() method")
    
    def calculate(self) -> None:
        """
        Calculate heat flux for each segment
        
        This method should be overridden by subclasses to define
        the relationship between heat flux, fluid temperature, and
        boundary temperature.
        """
        raise NotImplementedError("Subclasses must implement calculate() method")
    
    def __str__(self) -> str:
        """String representation of the heat transfer model"""
        return (f"Partial Heat Transfer\n"
                f"n = {self.n}\n"
                f"T_fluid = {self.T_fluid} K\n"
                f"q_dot = {self.q_dot} W/m²")
