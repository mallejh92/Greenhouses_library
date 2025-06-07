from Modelica.Thermal.HeatTransfer.Interfaces.Element1D import Element1D

class CanopyFreeConvection(Element1D):
    """
    Leaves heat exchange by free convection with air
    
    This class implements the heat transfer model for free convection between
    leaves and air in a greenhouse system.
    """
    
    def __init__(self, A, LAI=1, U=5, u=0, h_Air=3.8):
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
        u : float, optional
            Wind speed [m/s], default is 0
        h_Air : float, optional
            Air height [m], default is 3.8
        """
        super().__init__()
        self.A = A
        self.U = U
        self.LAI = LAI
        self.u = u
        self.h_Air = h_Air
        self.HEC_ab = 0.0  # Heat exchange coefficient
        # Modelica-style port names are now inherited from Element1D (port_a/b)
        
    def step(self):
        """
        Calculate heat transfer between leaves and air
        """
        # Calculate heat exchange coefficient (풍속과 높이 반영)
        self.HEC_ab = 2 * self.LAI * self.U * (1 + 0.1 * self.u) * (self.h_Air / 3.8)**0.5
        
        # Calculate heat flow (dT는 property로 자동 계산됨)
        self.Q_flow = self.A * self.HEC_ab * self.dT
        
        # Element1D의 update() 호출하여 포트 열유량 업데이트
        self.update()

        return self.Q_flow
