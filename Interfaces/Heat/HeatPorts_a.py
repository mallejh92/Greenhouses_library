from typing import List, Optional
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort import HeatPort

class HeatPorts_a(HeatPort):
    """
    HeatPort connector with filled, large icon to be used for vectors of HeatPorts
    
    This class implements the Modelica HeatPorts_a connector in Python.
    It extends the basic HeatPort with a filled icon representation.
    
    Note:
        In Modelica, this connector is used for vectors of HeatPorts,
        but in Python we implement it as a single port for simplicity.
    """
    
    def __init__(self, T_start=293.15):
        """
        Initialize HeatPorts_a
        
        Args:
            T_start (float): Initial temperature [K]
        """
        super().__init__(T_start)
        self.ports = [HeatPort(T_start)]  # 기본적으로 하나의 포트로 초기화
    
    def __str__(self):
        """String representation of the heat port"""
        return f"HeatPorts_a(T={self.T:.2f}K, Q_flow={self.Q_flow:.2f}W)"

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

    def add_port(self, T_start=293.15) -> None:
        """
        Add a new heat port to the vector
        
        Args:
            T_start (float): Initial temperature [K] for the new port
        """
        self.ports.append(HeatPort(T_start))
    
    def set_size(self, size: int, T_start=293.15) -> None:
        """
        Set the number of ports in the vector
        
        Args:
            size (int): Number of ports
            T_start (float): Initial temperature [K] for new ports
        """
        self.ports = [HeatPort(T_start) for _ in range(size)] 