import numpy as np
from .HeatPorts_a import HeatPorts_a
from .HeatPorts_b import HeatPorts_b

class Element1D_discretized:
    """
    Partial heat transfer element with two HeatPort connectors that does not store energy
    
    This class implements the discretized heat transfer interface in Python.
    It provides basic heat transfer functionality with multiple heat ports.
    """
    
    def __init__(self, nNodes=2):
        """
        Initialize Element1D_discretized
        
        Parameters:
        -----------
        nNodes : int, optional
            Number of discrete flow volumes, default is 2
        """
        if nNodes < 1:
            raise ValueError("nNodes must be greater than or equal to 1")
            
        self.nNodes = nNodes
        
        # Initialize heat ports
        self.heatPorts_a = HeatPorts_a(nNodes)  # Vector of heat ports a
        self.heatPorts_b = HeatPorts_b(nNodes)  # Vector of heat ports b
        
        # Initialize arrays
        self.Q_flow = np.zeros(nNodes)  # Heat flow rate from port_a -> port_b
        
    @property
    def dT(self):
        """Temperature difference between ports (heatPorts_a.T - heatPorts_b.T)"""
        return np.array([self.heatPorts_a[i].T - self.heatPorts_b[i].T 
                        for i in range(self.nNodes)])
        
    def calculate(self):
        """
        Calculate heat transfer and update heat flows
        
        This method updates the Q_flow values in the heat ports directly,
        similar to the Modelica implementation.
        """
        # Update heat flows
        for i in range(self.nNodes):
            self.heatPorts_a[i].Q_flow = self.Q_flow[i]
            self.heatPorts_b[i].Q_flow = -self.Q_flow[i]  # Negative sign as in original Modelica code
