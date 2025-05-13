import numpy as np
from .HeatPort import HeatPort

class HeatPorts_a:
    """
    HeatPort connector with filled, large icon to be used for vectors of HeatPorts.
    Equivalent to Modelica's HeatPorts_a connector.
    
    Attributes:
        ports (numpy.ndarray): Array of HeatPort objects
        size (int): Number of ports in the vector
    """
    def __init__(self, size=1, T_start=293.15):
        """
        Initialize vector of heat ports.
        
        Args:
            size (int): Number of ports in the vector
            T_start (float): Initial temperature for all ports [K]
        """
        self.size = size
        # Create array of HeatPort objects
        self.ports = np.array([HeatPort(T_start=T_start) for _ in range(size)])
        
    def connect(self, other_ports):
        """
        Connect to another vector of ports.
        
        Args:
            other_ports (HeatPorts_a): Another vector of ports to connect to
        """
        if not isinstance(other_ports, HeatPorts_a):
            raise TypeError("Can only connect to another HeatPorts_a instance")
            
        if self.size != other_ports.size:
            raise ValueError("Cannot connect ports vectors of different sizes")
            
        # Connect each port pair
        for i in range(self.size):
            self.ports[i].connect(other_ports.ports[i])
            
    def get_temperatures(self):
        """
        Get array of temperatures for all ports.
        
        Returns:
            numpy.ndarray: Array of temperatures [K]
        """
        return np.array([port.T for port in self.ports])
        
    def get_heat_flows(self):
        """
        Get array of heat flows for all ports.
        
        Returns:
            numpy.ndarray: Array of heat flows [W]
        """
        return np.array([port.Q_flow for port in self.ports])
        
    def set_temperatures(self, temperatures):
        """
        Set temperatures for all ports.
        
        Args:
            temperatures (numpy.ndarray): Array of temperatures [K]
        """
        if len(temperatures) != self.size:
            raise ValueError("Temperature array size must match number of ports")
        for i, T in enumerate(temperatures):
            self.ports[i].T = T
            
    def set_heat_flows(self, heat_flows):
        """
        Set heat flows for all ports.
        
        Args:
            heat_flows (numpy.ndarray): Array of heat flows [W]
        """
        if len(heat_flows) != self.size:
            raise ValueError("Heat flow array size must match number of ports")
        for i, Q in enumerate(heat_flows):
            self.ports[i].Q_flow = Q 