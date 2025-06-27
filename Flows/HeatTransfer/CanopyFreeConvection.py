from Modelica.Thermal.HeatTransfer.Interfaces.Element1D import Element1D

class CanopyFreeConvection(Element1D):
    """
    Leaves heat exchange by free convection with air
    
    This class implements the heat transfer model for free convection between
    leaves and air in a greenhouse system.
    """
    
    def __init__(self, A, LAI=1, U=5):
        """
        Initialize the CanopyFreeConvection model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        LAI : float, optional
            Leaf Area Index, default is 1
        U : float, optional
            Leaves heat transfer coefficient [W/(m²·K)], default is 5
        """
        super().__init__()
        self.A = A
        self.U = U
        self.LAI = LAI
        self.HEC_ab = 0.0  # Heat exchange coefficient
        
    def step(self):
        """
        Calculate heat transfer between leaves and air
        """
        # Calculate heat exchange coefficient (Modelica 원본과 정확히 일치)
        self.HEC_ab = 2 * self.LAI * self.U
        
        # Calculate heat flow (dT는 property로 자동 계산됨)
        self.Q_flow = self.A * self.HEC_ab * self.dT
        
        # Element1D의 update() 호출하여 포트 열유량 업데이트
        self.update()

        return self.Q_flow
