from typing import Optional
from Interfaces.Heat.HeatFluxInput import HeatFlux
from Interfaces.Heat.HeatPorts_a import HeatPorts_a
from Interfaces.Heat.ThermalPort import ThermalPort
from Interfaces.Heat.ThermalPortL import ThermalPortL
import numpy as np

class HeatPortConverter_ThermoCycle_Modelica:
    """
    Heat port converter from the Modelica Library to the ThermoCycle Library heat port models
    
    This class implements the Modelica HeatPortConverter_ThermoCycle_Modelica model in Python.
    It converts between Modelica's HeatPort and ThermalPort interfaces.
    
    Attributes:
        N (int): Number of ports in series
        A (float): Heat transfer area [m²]
        Nt (int): Number of cells in parallel
        thermocyclePort (ThermalPort): Thermal port for ThermoCycle
        heatPorts (HeatPorts_a): Heat ports for Modelica
    """
    
    def __init__(self, N: int = 2, A: float = 1.0, Nt: int = 1):
        """
        Initialize the HeatPortConverter_ThermoCycle_Modelica
        
        Args:
            N (int): Number of ports in series (default: 2)
            A (float): Heat transfer area in m² (default: 1.0)
            Nt (int): Number of cells in parallel (default: 1)
        """
        self.N = N
        self.A = A
        self.Nt = Nt
        self.thermocyclePort = ThermalPort(N=N)
        self.heatPorts = HeatPorts_a(size=N)
    
    def update(self) -> None:
        """
        Update the heat ports based on thermal port values
        
        This method implements the equations from the Modelica model:
        heatPorts[i].T = thermocyclePort.T[i]
        heatPorts[i].Q_flow = -thermocyclePort.phi[i]*A/N*Nt
        """
        # Get current values from thermal port
        temps = self.thermocyclePort.get_temperatures()
        fluxes = self.thermocyclePort.get_heat_fluxes()
        
        # Update heat ports
        for i in range(self.N):
            self.heatPorts[i].T = temps[i]
            self.heatPorts[i].Q_flow = -fluxes[i].value * self.A / self.N * self.Nt
    
    def connect_heat_ports(self, other_ports: HeatPorts_a) -> None:
        """
        Connect external heat ports
        
        Args:
            other_ports (HeatPorts_a): External heat ports to connect
        """
        self.heatPorts.connect(other_ports)
        self.update()
    
    def __str__(self) -> str:
        """String representation of the converter"""
        temps = self.heatPorts.get_temperatures()
        flows = self.heatPorts.get_heat_flows()
        return (f"HeatPortConverter_ThermoCycle_Modelica(N={self.N}, A={self.A} m², Nt={self.Nt})\n"
                f"Heat Ports: T_avg={np.mean(temps):.2f} K, Q_flow_avg={np.mean(flows):.2f} W")
