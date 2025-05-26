from typing import Optional, Union

class HeatPort:
    """
    Thermal port for 1-dim. heat transfer
    
    Attributes:
        T (float): Port temperature [K]
        Q_flow (float): Heat flow rate (positive if flowing from outside into the component) [W]
    """
    def __init__(self, T_start: float = 293.15):
        """
        Initialize heat port
        
        Args:
            T_start (float): Initial temperature [K]
        """
        self.T = T_start  # Port temperature [K]
        self.Q_flow = 0.0  # Heat flow rate [W]
    
    def connect(self, other: 'HeatPort') -> None:
        """
        Connect this heat port to another heat port
        
        Args:
            other (HeatPort): Other heat port to connect with
        """
        if not isinstance(other, HeatPort):
            raise TypeError("Can only connect with HeatPort type connectors")
        
        # In Modelica, the sum of Q_flow at a connection point must be zero
        # This is handled automatically by the solver in Modelica
        # In Python, we need to handle this manually
        self.Q_flow = -other.Q_flow
    
    def __str__(self) -> str:
        """String representation of the heat port"""
        return f"HeatPort(T={self.T:.2f}K, Q_flow={self.Q_flow:.2f}W)" 