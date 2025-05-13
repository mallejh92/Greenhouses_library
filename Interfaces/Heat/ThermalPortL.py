from typing import Optional, Union
from Interfaces.Heat.HeatFluxInput import HeatFlux

class ThermalPortL:
    """
    Distributed Heat Terminal connector (single node)
    
    This class implements the Modelica ThermalPortL connector in Python.
    It represents a distributed heat terminal with a single node.
    
    Attributes:
        T (float): Temperature in Kelvin
        phi (HeatFlux): Heat flux in W/m²
    """
    
    def __init__(self, T: float = 293.15, phi: Optional[Union[HeatFlux, float]] = None):
        """
        Initialize ThermalPortL
        
        Args:
            T (float): Initial temperature in Kelvin (default: 293.15)
            phi (Optional[Union[HeatFlux, float]]): Initial heat flux in W/m² (default: 0.0)
        """
        self.T = float(T)
        if phi is None:
            self.phi = HeatFlux(0.0)
        elif isinstance(phi, (int, float)):
            self.phi = HeatFlux(float(phi))
        else:
            self.phi = phi
    
    def set_temperature(self, T: float) -> None:
        """
        Set temperature
        
        Args:
            T (float): Temperature in Kelvin
        """
        self.T = float(T)
    
    def set_heat_flux(self, phi: Union[HeatFlux, float]) -> None:
        """
        Set heat flux
        
        Args:
            phi (Union[HeatFlux, float]): Heat flux in W/m²
        """
        if isinstance(phi, (int, float)):
            self.phi = HeatFlux(float(phi))
        else:
            self.phi = phi
    
    def get_temperature(self) -> float:
        """
        Get temperature
        
        Returns:
            float: Temperature in Kelvin
        """
        return self.T
    
    def get_heat_flux(self) -> HeatFlux:
        """
        Get heat flux
        
        Returns:
            HeatFlux: Heat flux in W/m²
        """
        return self.phi
    
    def connect(self, other: 'ThermalPortL') -> None:
        """
        Connect this thermal port to another thermal port
        
        Args:
            other (ThermalPortL): Other thermal port to connect with
            
        Raises:
            TypeError: If the other connector is not of type ThermalPortL
        """
        if not isinstance(other, ThermalPortL):
            raise TypeError("Can only connect with ThermalPortL type connectors")
        
        # Connect temperature and heat flux
        self.T = other.T
        self.phi = other.phi
    
    def __str__(self) -> str:
        """String representation of the thermal port"""
        return (f"ThermalPortL\n"
                f"T = {self.T:.2f} K\n"
                f"phi = {self.phi} W/m²") 