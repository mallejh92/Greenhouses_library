"""
Modelica ThermalPort connector implementation
Original Modelica: connector ThermalPort "Distributed Heat Terminal"
"""
import numpy as np
from typing import Union, List

class ThermalPort:
    """
    Distributed Heat Terminal connector - exact match to Modelica original
    
    Modelica original:
    connector ThermalPort "Distributed Heat Terminal"
      parameter Integer N(min=1)=2 "Number of nodes";
      Modelica.SIunits.Temperature T[N] "Temperature at the nodes";
      flow Modelica.SIunits.HeatFlux phi[N] "Heat flux at the nodes";
    """
    
    def __init__(self, N: int = 2, T_start: float = 293.15):
        """
        Initialize ThermalPort exactly as in Modelica
        
        Args:
            N (int): Number of nodes (minimum 1, default 2)
            T_start (float): Initial temperature for all nodes [K]
        """
        if N < 1:
            raise ValueError("Number of nodes (N) must be at least 1")
            
        self.N = N
        # Modelica: Modelica.SIunits.Temperature T[N]
        self.T = np.full(N, T_start, dtype=float)
        # Modelica: flow Modelica.SIunits.HeatFlux phi[N]
        self.phi = np.zeros(N, dtype=float)
    
    def set_temperatures(self, temperatures: Union[np.ndarray, List[float]]) -> None:
        """Set temperatures for all nodes"""
        if len(temperatures) != self.N:
            raise ValueError(f"Temperature array length must match number of nodes (N={self.N})")
        self.T = np.array(temperatures, dtype=float)
    
    def set_heat_fluxes(self, heat_fluxes: Union[np.ndarray, List[float]]) -> None:
        """Set heat fluxes for all nodes"""
        if len(heat_fluxes) != self.N:
            raise ValueError(f"Heat flux array length must match number of nodes (N={self.N})")
        self.phi = np.array(heat_fluxes, dtype=float)
    
    def get_temperatures(self) -> np.ndarray:
        """Get temperatures for all nodes"""
        return self.T.copy()
    
    def get_heat_fluxes(self) -> np.ndarray:
        """Get heat fluxes for all nodes"""
        return self.phi.copy()
    
    def __str__(self) -> str:
        """String representation of the thermal port"""
        temps_str = ", ".join(f"{t:.2f}" for t in self.T)
        fluxes_str = ", ".join(f"{phi:.2f}" for phi in self.phi)
        return (f"ThermalPort(N={self.N})\n"
                f"T = [{temps_str}] K\n"
                f"phi = [{fluxes_str}] W/m²")
