from typing import List
from Interfaces.Heat.HeatPorts_a import HeatPorts_a
from Interfaces.Heat.ThermalPort import ThermalPort
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
        heatPorts (List[HeatPorts_a]): List of heat ports for Modelica
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
        self.heatPorts = [HeatPorts_a() for _ in range(N)]
    
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
            # ThermalPort 단순화: fluxes는 이제 numpy.ndarray이므로 직접 사용
            self.heatPorts[i].Q_flow = -fluxes[i] * self.A / self.N * self.Nt
    
    def connect_heat_ports(self, other_ports: List[HeatPorts_a]) -> None:
        """
        Connect external heat ports
        
        Args:
            other_ports (List[HeatPorts_a]): External heat ports to connect
        """
        if len(other_ports) != self.N:
            raise ValueError(f"Expected {self.N} heat ports, got {len(other_ports)}")
        
        for i in range(self.N):
            self.heatPorts[i].connect(other_ports[i])
        self.update()
    
    def __str__(self) -> str:
        """String representation of the converter"""
        temps = [port.T for port in self.heatPorts]
        flows = [port.Q_flow for port in self.heatPorts]
        return (f"HeatPortConverter_ThermoCycle_Modelica(N={self.N}, A={self.A} m², Nt={self.Nt})\n"
                f"Heat Ports: T_avg={np.mean(temps):.2f} K, Q_flow_avg={np.mean(flows):.2f} W")
