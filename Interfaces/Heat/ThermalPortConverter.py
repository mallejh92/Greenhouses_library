from typing import List
import numpy as np
from Interfaces.Heat.ThermalPort import ThermalPort
from Interfaces.Heat.ThermalPortL import ThermalPortL

class ThermalPortConverter:
    """
    Convert duplicated single thermal ports into one single multi-port
    
    This model converts between a multi-node ThermalPort and an array of single-node ThermalPortL.
    It maintains the connection between temperature and heat flux values, with heat flux direction
    being opposite between the multi-port and single ports.
    
    Attributes:
        N (int): Number of nodes/ports (default: 10)
        multi (ThermalPort): Multi-node thermal port
        single (List[ThermalPortL]): Array of single-node thermal ports
    """
    
    def __init__(self, N: int = 10):
        """
        Initialize ThermalPortConverter
        
        Args:
            N (int): Number of nodes/ports (default: 10)
        """
        self.N = N
        self.multi = ThermalPort(N=N)  # Create multi-node port
        self.single = [ThermalPortL() for _ in range(N)]  # Create array of single-node ports
    
    def update(self) -> None:
        """
        Update the connection between multi-port and single ports
        
        This method implements the Modelica equations:
        - single[i].T = multi.T[i]
        - single[i].phi = -multi.phi[i]
        """
        # Get current values from multi-port
        multi_temps = self.multi.get_temperatures()
        multi_fluxes = self.multi.get_heat_fluxes()
        
        # Update single ports
        for i in range(self.N):
            self.single[i].set_temperature(multi_temps[i])
            # Note the negative sign for heat flux
            self.single[i].set_heat_flux(-multi_fluxes[i].value)
    
    def connect_multi(self, other: ThermalPort) -> None:
        """
        Connect the multi-port to another ThermalPort
        
        Args:
            other (ThermalPort): ThermalPort to connect with
            
        Raises:
            ValueError: If the other port has different number of nodes
        """
        if other.N != self.N:
            raise ValueError(f"Cannot connect ports with different number of nodes (expected {self.N}, got {other.N})")
        self.multi = other
        self.update()
    
    def connect_single(self, index: int, other: ThermalPortL) -> None:
        """
        Connect a single port to another ThermalPortL
        
        Args:
            index (int): Index of the single port to connect
            other (ThermalPortL): ThermalPortL to connect with
            
        Raises:
            IndexError: If index is out of range
        """
        if not 0 <= index < self.N:
            raise IndexError(f"Index {index} out of range (0 to {self.N-1})")
        self.single[index] = other
        self.update()
    
    def __str__(self) -> str:
        """String representation of the converter"""
        return (f"ThermalPortConverter(N={self.N})\n"
                f"Multi-port:\n{self.multi}\n"
                f"Single ports:\n" + 
                "\n".join(f"Port {i}:\n{port}" for i, port in enumerate(self.single))) 