class WaterMassPort:
    """
    Base connector for 1-dimensional water vapour mass transfer.
    Equivalent to Modelica's partial connector WaterMassPort.
    Attributes:
        VP (float): Port vapour pressure [Pa]
        MV_flow (float): Mass flow rate [kg/s] (positive if flowing into the component)
    """
    def __init__(self, VP_start=0.04e5):
        self.VP = VP_start
        self.MV_flow = 0.0
        self._connected_ports = []

    def connect(self, other_port):
        """
        Connect to another port (emulates Modelica's connect equation).
        """
        if other_port not in self._connected_ports:
            self._connected_ports.append(other_port)
            other_port._connected_ports.append(self)
            # Potential variable: equalize pressure
            other_port.VP = self.VP
            # Flow variable: sum to zero
            total_flow = self.MV_flow + other_port.MV_flow
            self.MV_flow = total_flow / 2
            other_port.MV_flow = -total_flow / 2 