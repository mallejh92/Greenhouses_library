from .HeatPorts_a import HeatPorts_a
from .HeatPorts_b import HeatPorts_b

class Element1D:
    """
    Base class for one-dimensional heat transfer elements
    
    This class implements the Modelica Element1D interface in Python.
    It provides basic heat transfer functionality with two heat ports.
    """
    
    def __init__(self):
        """Initialize Element1D with two heat ports"""
        self.heatPort_a = HeatPorts_a(1)[0]  # First heat port
        self.heatPort_b = HeatPorts_b(1)[0]  # Second heat port
        
    @property
    def dT(self):
        """Temperature difference between ports (heatPort_a.T - heatPort_b.T)"""
        return self.heatPort_a.T - self.heatPort_b.T
        
    @property
    def Q_flow(self):
        """Heat flow rate between ports"""
        return self.heatPort_a.Q_flow 