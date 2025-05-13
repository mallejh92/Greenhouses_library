class WaterMassPort:
    """
    Water mass port for 1-dim. water vapour mass transfer
    Equivalent to Modelica's partial connector WaterMassPort
    
    Attributes:
        VP (float): Port vapour pressure [Pa]
        MV_flow (float): Mass flow rate (positive if flowing from outside into the component) [kg/s]
    """
    def __init__(self, VP_start=0.04e5):
        # Port variables (equivalent to Modelica's connector variables)
        self.VP = VP_start      # Port vapour pressure [Pa]
        self.MV_flow = 0.0      # Mass flow rate [kg/s]
        
        # Internal variables for connection handling
        self._connected_ports = []  # List of connected ports

    def connect(self, other_port):
        """
        Connect to another port (equivalent to Modelica's connect equation)
        Note: In Modelica, connections are handled by the system, but in Python we need to manage them
        """
        if other_port not in self._connected_ports:
            self._connected_ports.append(other_port)
            other_port._connected_ports.append(self)
            
            # Update flow variables (equivalent to Modelica's flow variable handling)
            # In Modelica, flow variables sum to zero at connections
            total_flow = self.MV_flow + other_port.MV_flow
            self.MV_flow = total_flow / 2
            other_port.MV_flow = -total_flow / 2  # Opposite direction
            
            # Update potential variables (equivalent to Modelica's potential variable handling)
            # In Modelica, potential variables are equal at connections
            other_port.VP = self.VP 