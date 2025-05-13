from typing import Optional
from Interfaces.Heat.HeatFluxInput import HeatFlux
from Interfaces.Heat.HeatPorts_a import HeatPorts_a
import numpy as np

class ThermalPortL:
    """
    Implementation of ThermalPortL interface
    
    This is a placeholder class that will be implemented later.
    For now, it just provides the basic structure for thermal port interface.
    
    Attributes:
        T (float): Temperature in Kelvin
        phi (HeatFlux): Heat flux in W/m²
    """
    pass

class HeatPortConverter:
    """
    Convert thermal port into heat port
    
    This class implements the Modelica HeatPortConverter model in Python.
    It converts between Modelica's HeatPort and ThermalPortL interfaces.
    
    Attributes:
        N (int): Number of ports (default: 10)
        A (float): Heat exchange area in m² (default: 1.0)
        heatPorts (HeatPorts_a): Input heat ports
        thermalPortL (ThermalPortL): Output thermal port
    """
    
    def __init__(self, 
                 N: int = 10,
                 A: float = 1.0,
                 T_start: float = 293.15):
        """
        Initialize the HeatPortConverter
        
        Args:
            N (int): Number of ports
            A (float): Heat exchange area in m²
            T_start (float): Initial temperature in Kelvin
        """
        self.N = N
        self.A = A
        self.heatPorts = HeatPorts_a(size=N, T_start=T_start)
        # TODO: Implement proper ThermalPortL initialization when the class is fully implemented
        self.thermalPortL = ThermalPortL()
        self.thermalPortL.T = T_start
        self.thermalPortL.phi = HeatFlux(0.0)
    
    def update(self) -> None:
        """
        Update the thermal port based on heat port values
        
        This method implements the equations from the Modelica model:
        thermalPortL.T = heatPort.T
        thermalPortL.phi = -heatPort.Q_flow/A
        
        For multiple ports, it uses the average values.
        """
        # Get average temperature and heat flow from all ports
        avg_T = np.mean(self.heatPorts.get_temperatures())
        avg_Q_flow = np.mean(self.heatPorts.get_heat_flows())
        
        # Update temperature
        self.thermalPortL.T = avg_T
        
        # Update heat flux (convert from heat flow rate to heat flux)
        heat_flux_value = -avg_Q_flow / self.A
        self.thermalPortL.phi = HeatFlux(heat_flux_value)
    
    def connect_heat_ports(self, other_ports: HeatPorts_a) -> None:
        """
        Connect external heat ports
        
        Args:
            other_ports (HeatPorts_a): External heat ports to connect
        """
        self.heatPorts.connect(other_ports)
        self.update()
    
    def get_thermal_port(self) -> ThermalPortL:
        """
        Get the current thermal port values
        
        Returns:
            ThermalPortL: Current thermal port state
        """
        return self.thermalPortL
    
    def __str__(self) -> str:
        """String representation of the converter"""
        temps = self.heatPorts.get_temperatures()
        flows = self.heatPorts.get_heat_flows()
        return (f"HeatPortConverter(N={self.N}, A={self.A} m²)\n"
                f"Heat Ports: T_avg={np.mean(temps):.2f} K, Q_flow_avg={np.mean(flows):.2f} W\n"
                f"Thermal Port: T={self.thermalPortL.T:.2f} K, phi={self.thermalPortL.phi}")
