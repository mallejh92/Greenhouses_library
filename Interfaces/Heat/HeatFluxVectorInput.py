from typing import Optional, Union, List, Set
from Interfaces.Heat.HeatFluxInput import HeatFlux

class HeatFluxVectorInput:
    """
    Connector class for vector of Heat Flux inputs
    
    This class implements the Modelica HeatFluxVectorInput connector in Python.
    It provides an interface for receiving multiple heat flux values as input,
    typically used in vectorized connections.
    
    Attributes:
        values (List[HeatFlux]): List of input heat flux values (W/m²)
        name (str): Name of the connector (default: "u")
        _connected_ports (Set['HeatFluxVectorInput']): Set of connected ports
    """
    
    def __init__(self, values: Optional[Union[List[Union[HeatFlux, float]], HeatFlux, float]] = None, 
                 name: str = "u"):
        """
        Initialize the HeatFluxVectorInput connector
        
        Args:
            values: Can be one of:
                - List of HeatFlux objects or floats
                - Single HeatFlux object
                - Single float value
                - None (creates empty list)
            name (str): Name of the connector
        """
        self.name = name
        self._connected_ports: Set['HeatFluxVectorInput'] = set()
        
        if values is None:
            self.values: List[HeatFlux] = []
        elif isinstance(values, (list, tuple)):
            self.values = [HeatFlux(float(v)) if isinstance(v, (int, float)) else v for v in values]
        elif isinstance(values, (int, float)):
            self.values = [HeatFlux(float(values))]
        else:
            self.values = [values]  # Single HeatFlux object
    
    def _propagate_values(self) -> None:
        """Propagate values to all connected ports"""
        for port in self._connected_ports:
            port.values = [v.copy() for v in self.values]
    
    def connect(self, other: 'HeatFluxVectorInput') -> None:
        """
        Connect this vector input connector to another HeatFluxVectorInput
        
        Args:
            other (HeatFluxVectorInput): Other vector connector to connect with
            
        Raises:
            TypeError: If the other connector is not of type HeatFluxVectorInput
            ValueError: If the vectors have different lengths
        """
        if not isinstance(other, HeatFluxVectorInput):
            raise TypeError("Can only connect with HeatFluxVectorInput type connectors")
        if len(self.values) != len(other.values):
            raise ValueError("Cannot connect vectors of different lengths")
            
        # 양방향 연결 설정
        self._connected_ports.add(other)
        other._connected_ports.add(self)
        
        # 값 전파
        self._propagate_values()
    
    def disconnect(self, other: 'HeatFluxVectorInput') -> None:
        """
        Disconnect from another HeatFluxVectorInput
        
        Args:
            other (HeatFluxVectorInput): Port to disconnect from
        """
        if other in self._connected_ports:
            self._connected_ports.remove(other)
            other._connected_ports.remove(self)
    
    def __setitem__(self, index: int, value: Union[HeatFlux, float]) -> None:
        """Set heat flux value at specified index and propagate to connected ports"""
        if isinstance(value, (int, float)):
            self.values[index] = HeatFlux(float(value))
        else:
            self.values[index] = value
        self._propagate_values()
    
    def append(self, value: Union[HeatFlux, float]) -> None:
        """
        Append a new heat flux value to the vector and propagate to connected ports
        
        Args:
            value (Union[HeatFlux, float]): Heat flux value to append
        """
        if isinstance(value, (int, float)):
            self.values.append(HeatFlux(float(value)))
        else:
            self.values.append(value)
        self._propagate_values()
    
    def __str__(self) -> str:
        """String representation of the connector"""
        values_str = ", ".join(str(v) for v in self.values)
        return f"{self.name}: [{values_str}]"
    
    def __len__(self) -> int:
        """Return the number of heat flux values"""
        return len(self.values)
    
    def __getitem__(self, index: int) -> HeatFlux:
        """Get heat flux value at specified index"""
        return self.values[index]
