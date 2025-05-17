class CanopyFreeConvection:
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
        self.A = A
        self.U = U
        self.LAI = LAI
        
    def calculate_heat_transfer(self, T_a, T_b):
        """
        Calculate heat transfer between leaves and air
        
        Parameters:
        -----------
        T_a : float
            Temperature at port a [K]
        T_b : float
            Temperature at port b [K]
            
        Returns:
        --------
        Q_flow : float
            Heat flow rate [W]
        """
        # Calculate heat exchange coefficient
        HEC_ab = 2 * self.LAI * self.U
        
        # Calculate temperature difference
        dT = T_b - T_a
        
        # Calculate heat flow
        Q_flow = self.A * HEC_ab * dT
        
        return Q_flow
