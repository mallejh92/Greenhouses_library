from Interfaces.CO2.Element1D import Element1D

class MC_ventilation2(Element1D):
    """
    CO2 mass flow accompanying an air flow caused by ventilation processes
    
    This model extends Element1D and implements the Modelica equation:
    MC_flow = f_vent * dC
    """
    
    def __init__(self, f_vent=0.0):
        """
        Initialize ventilation CO2 mass flow model
        
        Parameters:
            f_vent (float): Air exchange rate [m3/(m2.s)], default is 0.0
        """
        # Call parent constructor to initialize Element1D
        super().__init__()
        
        # Input variable
        self.f_vent = f_vent  # Air exchange rate [m3/(m2.s)]
        
    def step(self) -> float:
        """
        Calculate CO2 mass flow (Modelica equation: MC_flow = f_vent * dC)
        
        Returns:
            float: CO2 mass flow rate [mg/(m2.s)]
        """
        # Modelica 원본 방정식: MC_flow = f_vent * dC
        self.update()  # dC 계산 (port_a.CO2 - port_b.CO2)
        self.MC_flow = self.f_vent * self.dC
        
        # 포트에 MC_flow 설정
        self.port_a.MC_flow = self.MC_flow
        self.port_b.MC_flow = -self.MC_flow
        
        return self.MC_flow
