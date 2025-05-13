from typing import Optional, Union
from Interfaces.Heat.HeatFluxInput import HeatFlux, HeatFluxInput  # Import both HeatFlux and HeatFluxInput

class HeatFluxOutput:
    """
    Connector class for Heat Flux output
    
    This class implements the Modelica HeatFluxOutput connector in Python.
    It provides an interface for sending heat flux values as output.
    The main difference from HeatFluxInput is that this is used for output signals.
    
    Attributes:
        value (HeatFlux): Output heat flux value (W/m²)
        name (str): Name of the connector (default: "I")
    """
    
    def __init__(self, value: Optional[Union[HeatFlux, float]] = None, name: str = "I"):
        """
        Initialize the HeatFluxOutput connector
        
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
    
    def connect(self, other: HeatFluxInput) -> None:  # Remove quotes around HeatFluxInput since it's now imported
        """
        Connect this output connector to a HeatFluxInput connector
        
        Args:
            other (HeatFluxInput): Input connector to connect with
            
        Raises:
            TypeError: If the other connector is not of type HeatFluxInput
        """
        if not isinstance(other, HeatFluxInput):
            raise TypeError("Can only connect with HeatFluxInput type connectors")
        other.value = self.value  # Note: direction is reversed compared to HeatFluxInput
