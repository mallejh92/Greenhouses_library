class HeatPort:
    """
    Base connector for 1-dimensional heat transfer.
    Equivalent to Modelica's HeatPort connector.
    
    Attributes:
        T (float): Port temperature [K]
        Q_flow (float): Heat flow rate [W] (positive if flowing into the component)
    """
    def __init__(self, T_start=293.15):
        self.T = T_start        # Port temperature [K]
        self.Q_flow = 0.0       # Heat flow rate [W]
        self._connected_ports = []

    def connect(self, other_port):
        """
        Connect to another port (emulates Modelica's connect equation).
        """
        if other_port not in self._connected_ports:
            self._connected_ports.append(other_port)
            other_port._connected_ports.append(self)
            # Potential variable: equalize temperature
            other_port.T = self.T
            # Flow variable: sum to zero
            total_flow = self.Q_flow + other_port.Q_flow
            self.Q_flow = total_flow / 2
            other_port.Q_flow = -total_flow / 2 