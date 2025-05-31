class WaterMassPort:
    """
    Water mass port for vapor pressure and mass flow rate exchange.
    """
    def __init__(self, VP=None, MV_flow=None):
        """
        Initialize WaterMassPort
        
        Parameters:
        -----------
        VP : float, optional
            Initial vapor pressure [Pa]
        MV_flow : float, optional
            Initial mass flow rate [kg/s]
        """
        self._VP = VP if VP is not None else 0.0
        self._MV_flow = MV_flow if MV_flow is not None else 0.0

    @property
    def VP(self):
        """Get vapor pressure [Pa]"""
        return self._VP

    @VP.setter
    def VP(self, value):
        """Set vapor pressure [Pa]"""
        if value is not None:
            self._VP = float(value)

    @property
    def MV_flow(self):
        """Get mass flow rate [kg/s]"""
        return self._MV_flow

    @MV_flow.setter
    def MV_flow(self, value):
        """Set mass flow rate [kg/s]"""
        if value is not None:
            self._MV_flow = float(value)

    def connect(self, other_port):
        """
        Connect to another port
        
        Parameters:
        -----------
        other_port : WaterMassPort
            Port to connect to
        """
        if other_port is not None:
            # 양방향 연결을 위해 양쪽 포트의 값을 동기화
            self.VP = other_port.VP
            self.MV_flow = other_port.MV_flow
            other_port.VP = self.VP
            other_port.MV_flow = self.MV_flow 