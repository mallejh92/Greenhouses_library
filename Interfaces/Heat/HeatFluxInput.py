from typing import Optional, Union

class HeatFlux:
    """
    Simple class to represent Heat Flux in W/m²
    
    This is a basic implementation to handle heat flux values with units.
    In a real application, you might want to use a proper units library like 'pint'.
    """
    def __init__(self, value: float):
        """
        Initialize HeatFlux with a value in W/m²
        
        Args:
            value (float): Heat flux value in W/m²
        """
        self.value = float(value)
    
    def __str__(self) -> str:
        return f"{self.value}"# W/m²"
    
    def __repr__(self) -> str:
        return f"HeatFlux({self.value})"

class HeatFluxInput:
    """
    Connector class for Heat Flux input
    
    This class implements the Modelica HeatFluxInput connector in Python.
    It provides an interface for receiving heat flux values as input.
    
    Attributes:
        value (HeatFlux): Input heat flux value (W/m²)
        name (str): Name of the connector (default: "I")
    """
    
    def __init__(self, value: Optional[Union[HeatFlux, float]] = None, name: str = "I"):
        """
        Initialize the HeatFluxInput connector
        
        Args:
            value (Optional[Union[HeatFlux, float]]): Initial heat flux value (can be HeatFlux object or float in W/m²)
            name (str): Name of the connector
        """
        self.name = name
        if value is None:
            self.value = HeatFlux(0.0)
        elif isinstance(value, (int, float)):
            self.value = HeatFlux(float(value))
        else:
            self.value = value
    
    def __str__(self) -> str:
        """String representation of the connector"""
        return f"{self.name}: {self.value}"
    
    def connect(self, other: 'HeatFluxInput') -> None:
        """
        Connect this connector to another HeatFluxInput connector
        
        Args:
            other (HeatFluxInput): Other connector to connect with
            
        Raises:
            TypeError: If the other connector is not of type HeatFluxInput
        """
        if not isinstance(other, HeatFluxInput):
            raise TypeError("Can only connect with HeatFluxInput type connectors")
        self.value = other.value
