from typing import List, Optional
from .HeatPort import HeatPort

class HeatPorts_a:
    """
    HeatPort connector with filled, large icon to be used for vectors of HeatPorts
    
    This class implements the Modelica HeatPorts_a connector in Python.
    It represents a vector of heat ports, each with temperature and heat flow rate.
    
    Attributes:
        ports (List[HeatPort]): List of heat ports
    """
    
    def __init__(self, size: int = 1):
        """
        Initialize HeatPorts_a
        
        Args:
            size (int): Number of heat ports in the vector (default: 1)
        """
        self.ports = [HeatPort() for _ in range(size)]
    
    def __getitem__(self, index: int) -> HeatPort:
        """
        Get heat port at specified index
        
        Args:
            index (int): Index of the heat port
            
        Returns:
            HeatPort: Heat port at the specified index
        """
        return self.ports[index]
    
    def __setitem__(self, index: int, port: HeatPort) -> None:
        """
        Set heat port at specified index
        
        Args:
            index (int): Index of the heat port
            port (HeatPort): Heat port to set
        """
        if not isinstance(port, HeatPort):
            raise TypeError("Can only set HeatPort type")
        self.ports[index] = port
    
    def __len__(self) -> int:
        """
        Get number of heat ports
        
        Returns:
            int: Number of heat ports
        """
        return len(self.ports)
    
    def connect(self, other: 'HeatPorts_a') -> None:
        """
        Connect this heat ports vector to another heat ports vector
        
        Args:
            other (HeatPorts_a): Other heat ports vector to connect with
            
        Raises:
            TypeError: If the other connector is not of type HeatPorts_a
            ValueError: If the vectors have different sizes
        """
        if not isinstance(other, HeatPorts_a):
            raise TypeError("Can only connect with HeatPorts_a type connectors")
        if len(self) != len(other):
            raise ValueError("Cannot connect heat port vectors of different sizes")
        
        # Connect each port
        for i in range(len(self)):
            self.ports[i].connect(other.ports[i])
    
    def __str__(self) -> str:
        """String representation of the heat ports vector"""
        return (f"HeatPorts_a (size: {len(self)})\n" +
                "\n".join(f"Port {i}: {port}" for i, port in enumerate(self.ports))) 