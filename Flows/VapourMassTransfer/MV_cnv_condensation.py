class MV_cnv_condensation:
    """
    Vapour mass transfer (and possible condensation) caused by convection at a surface.
    The model must be connected as following: air (filled port) - surface (empty port)
    
    This is a Python implementation of Greenhouses.Flows.VapourMassTransfer.MV_cnv_condensation
    """
    
    def __init__(self, A=1.0):
        """
        Initialize the MV_cnv_condensation model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        """
        self.A = A
        self.HEC_ab = 0.0  # Heat transfer coefficient between nodes a and b
        self.VEC_ab = 0.0  # Mass transfer coefficient [kg/(s.Pa.m²)]
        self.MV_flow = 0.0  # Mass flow rate [kg/s]
        self.dP = 0.0      # Pressure difference [Pa]
        
        # Modelica-style mass port names
        if not hasattr(self, 'massPort_a'):
            self.massPort_a = type('MassPort', (), {'VP': 0.0, 'P': 1e5})()
        if not hasattr(self, 'massPort_b'):
            self.massPort_b = type('MassPort', (), {'VP': 0.0, 'P': 1e5})()
        
    def step(self, dP):
        """
        Calculate the mass transfer rate
        
        Parameters:
        -----------
        dP : float
            Pressure difference between nodes a and b [Pa]
            
        Returns:
        --------
        MV_flow : float
            Mass flow rate [kg/s]
        """
        self.dP = dP
        
        if self.dP > 0:
            # Calculate mass transfer coefficient based on heat transfer coefficient
            self.VEC_ab = 6.4e-9 * self.HEC_ab
            # Calculate mass flow rate
            self.MV_flow = self.A * self.VEC_ab * self.dP
        else:
            # No condensation when pressure difference is negative
            self.VEC_ab = 0
            self.MV_flow = 0
            
        return self.MV_flow
