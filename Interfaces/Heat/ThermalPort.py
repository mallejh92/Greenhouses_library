import numpy as np
from typing import Optional, Union, List
from Interfaces.Heat.HeatFluxInput import HeatFlux

class ThermalPort:
    """
    Distributed Heat Terminal connector
    
    This class implements the Modelica ThermalPort connector in Python.
    It represents a distributed heat terminal with multiple nodes.
    
    Attributes:
        N (int): Number of nodes (minimum 1, default 2)
        T (numpy.ndarray): Temperature array at the nodes [K]
        phi (List[HeatFlux]): Heat flux array at the nodes [W/m²]
    """
    
    def __init__(self, N: int = 2, T_start: float = 293.15):
        """
        Initialize ThermalPort
        
        Args:
            N (int): Number of nodes (minimum 1)
            T_start (float): Initial temperature for all nodes [K]
            
        Raises:
            ValueError: If N is less than 1
        """
        if N < 1:
            raise ValueError("Number of nodes (N) must be at least 1")
            
        self.N = N
        self.T = np.full(N, T_start)  # Initialize all nodes with T_start
        self.phi = [HeatFlux(0.0) for _ in range(N)]  # Initialize all heat fluxes to zero
    
    def set_temperatures(self, temperatures: Union[np.ndarray, List[float]]) -> None:
        """
        Set temperatures for all nodes
        
        Args:
            temperatures (Union[np.ndarray, List[float]]): Array of temperatures [K]
            
        Raises:
            ValueError: If the length of temperatures doesn't match N
        """
        if len(temperatures) != self.N:
            raise ValueError(f"Temperature array length must match number of nodes (N={self.N})")
        self.T = np.array(temperatures, dtype=float)
    
    def set_heat_fluxes(self, heat_fluxes: Union[np.ndarray, List[Union[float, HeatFlux]]]) -> None:
        """
        Set heat fluxes for all nodes
        
        Args:
            heat_fluxes (Union[np.ndarray, List[Union[float, HeatFlux]]]): Array of heat fluxes [W/m²]
            
        Raises:
            ValueError: If the length of heat_fluxes doesn't match N
        """
        if len(heat_fluxes) != self.N:
            raise ValueError(f"Heat flux array length must match number of nodes (N={self.N})")
        
        self.phi = [HeatFlux(float(phi)) if isinstance(phi, (int, float)) else phi 
                   for phi in heat_fluxes]
    
    def get_temperatures(self) -> np.ndarray:
        """
        Get temperatures for all nodes
        
        Returns:
            numpy.ndarray: Array of temperatures [K]
        """
        return self.T.copy()
    
    def get_heat_fluxes(self) -> List[HeatFlux]:
        """
        Get heat fluxes for all nodes
        
        Returns:
            List[HeatFlux]: List of heat fluxes [W/m²]
        """
        return self.phi.copy()
    
    def connect(self, other: 'ThermalPort') -> None:
        """
        Connect this thermal port to another thermal port
        
        Args:
            other (ThermalPort): Other thermal port to connect with
            
        Raises:
            TypeError: If the other connector is not of type ThermalPort
            ValueError: If the ports have different number of nodes
        """
        if not isinstance(other, ThermalPort):
            raise TypeError("Can only connect with ThermalPort type connectors")
        if self.N != other.N:
            raise ValueError("Cannot connect thermal ports with different number of nodes")
            
        # Connect temperatures and heat fluxes
        self.T = other.T.copy()
        self.phi = other.phi.copy()
    
    def __str__(self) -> str:
        """String representation of the thermal port"""
        temps_str = ", ".join(f"{t:.2f}" for t in self.T)
        fluxes_str = ", ".join(str(phi) for phi in self.phi)
        return (f"ThermalPort(N={self.N})\n"
                f"T = [{temps_str}] K\n"
                f"phi = [{fluxes_str}] W/m²")
