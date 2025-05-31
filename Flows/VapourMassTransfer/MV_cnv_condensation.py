from Interfaces.Vapour.Element1D import Element1D

class MV_cnv_condensation(Element1D):
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
        super().__init__()
        
        # Parameters
        self.A = A
        
        # Varying inputs
        self.HEC_ab = 0.0  # Heat transfer coefficient between nodes a and b
        
        # Variables
        self.VEC_ab = 0.0  # Mass transfer coefficient [kg/(s.Pa.m²)]
        self.MV_flow = 0.0  # Mass flow rate [kg/s]
        self.dP = 0.0      # Pressure difference [Pa]
        
        # Modelica-style mass port names
        if not hasattr(self, 'massPort_a'):
            self.massPort_a = type('MassPort', (), {'VP': 0.0, 'P': 1e5})()
        if not hasattr(self, 'massPort_b'):
            self.massPort_b = type('MassPort', (), {'VP': 0.0, 'P': 1e5})()
        
    def step(self, dt=None):
        """
        Calculate the mass transfer rate
        
        Parameters:
        -----------
        dt : float, optional
            Time step [s]. Not used in calculations but included for compatibility.
            
        Returns:
        --------
        MV_flow : float
            Mass flow rate [kg/s]
        """
        # Calculate pressure difference (Modelica: dP = port_a.VP - port_b.VP)
        self.dP = self.massPort_a.VP - self.massPort_b.VP
        
        if self.dP > 0:
            # Calculate mass transfer coefficient based on heat transfer coefficient
            # Modelica: VEC_ab = 6.4e-9*HEC_ab
            self.VEC_ab = 6.4e-9 * self.HEC_ab
            # Calculate mass flow rate (Modelica: MV_flow = A*VEC_ab*dP)
            self.MV_flow = self.A * self.VEC_ab * self.dP
        else:
            # No condensation when pressure difference is negative
            # Modelica: VEC_ab = 0; MV_flow = 0
            self.VEC_ab = 0
            self.MV_flow = 0
            
        # Update parent class
        super().update()
        
        return self.MV_flow
