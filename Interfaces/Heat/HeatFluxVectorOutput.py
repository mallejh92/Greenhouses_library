from typing import Optional, Union, List
from Interfaces.Heat.HeatFluxInput import HeatFlux
from Interfaces.Heat.HeatFluxVectorInput import HeatFluxVectorInput

class HeatFluxVectorOutput:
    """
    Connector class for vector of Heat Flux outputs
    
    This class implements the Modelica HeatFluxVectorOutput connector in Python.
    It provides an interface for sending multiple heat flux values as output,
    typically used in vectorized connections.
    
    Attributes:
        values (List[HeatFlux]): List of output heat flux values (W/m²)
        name (str): Name of the connector (default: "u")
    """
    
    def __init__(self, values: Optional[Union[List[Union[HeatFlux, float]], HeatFlux, float]] = None, 
                 name: str = "u"):
        """
        Initialize the HeatFluxVectorOutput connector
        
        Args:
            values: Can be one of:
                - List of HeatFlux objects or floats
                - Single HeatFlux object
                - Single float value
                - None (creates empty list)
            name (str): Name of the connector
        """
        self.name = name
        
        if values is None:
            self.values: List[HeatFlux] = []
        elif isinstance(values, (list, tuple)):
            self.values = [HeatFlux(float(v)) if isinstance(v, (int, float)) else v for v in values]
        elif isinstance(values, (int, float)):
            self.values = [HeatFlux(float(values))]
        else:
            self.values = [values]  # Single HeatFlux object
    
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
    
    def __setitem__(self, index: int, value: Union[HeatFlux, float]) -> None:
        """Set heat flux value at specified index"""
        if isinstance(value, (int, float)):
            self.values[index] = HeatFlux(float(value))
        else:
            self.values[index] = value
    
    def append(self, value: Union[HeatFlux, float]) -> None:
        """
        Append a new heat flux value to the vector
        
        Args:
            value (Union[HeatFlux, float]): Heat flux value to append
        """
        if isinstance(value, (int, float)):
            self.values.append(HeatFlux(float(value)))
        else:
            self.values.append(value)
    
    def connect(self, other: HeatFluxVectorInput) -> None:
        """
        Connect this vector output connector to a HeatFluxVectorInput
        
        Args:
            other (HeatFluxVectorInput): Input vector connector to connect with
            
        Raises:
            TypeError: If the other connector is not of type HeatFluxVectorInput
            ValueError: If the vectors have different lengths
        """
        if not isinstance(other, HeatFluxVectorInput):
            raise TypeError("Can only connect with HeatFluxVectorInput type connectors")
        if len(self.values) != len(other.values):
            raise ValueError("Cannot connect vectors of different lengths")
        other.values = self.values.copy()  # Note: direction is reversed compared to HeatFluxVectorInput
    
    def to_csv(self, filepath: str, column_name: str = "heat_flux") -> None:
        """
        Save the heat flux values to a CSV file
        
        Args:
            filepath (str): Path to save the CSV file
            column_name (str): Name of the column in CSV file
        """
        import csv
        
        with open(filepath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([column_name])  # Write header
            for value in self.values:
                writer.writerow([value.value])  # Write each heat flux value
    
    def to_pandas(self) -> 'pd.DataFrame':
        """
        Convert the heat flux values to a pandas DataFrame
        
        Returns:
            pd.DataFrame: DataFrame containing the heat flux values
        """
        import pandas as pd
        return pd.DataFrame({
            'heat_flux': [v.value for v in self.values]
        })
