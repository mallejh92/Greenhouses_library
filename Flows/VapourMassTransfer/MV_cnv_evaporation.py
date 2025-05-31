from Interfaces.Vapour.Element1D import Element1D

class MV_cnv_evaporation(Element1D):
    """
    Vapour mass transfer (and possible evaporation) caused by convection at a surface.
    The model must be connected as following: surface (filled port) - air (empty port)
    
    This is a Python implementation of Greenhouses.Flows.VapourMassTransfer.MV_cnv_evaporation
    """
    
    def __init__(self, A=1.0):
        """
        Initialize the MV_cnv_evaporation model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        """
        super().__init__()
        
        # Parameters
        self.A = A
        
        # Varying inputs
        self.HEC_ab = 0.0     # Heat transfer coefficient between nodes a and b
        self.VEC_AirScr = 0.0 # Mass transfer coefficient at the lower part of the screen
        self.VP_air = 1e5     # Vapour pressure at the main air zone [Pa]
        
        # Variables
        self.VEC_ab = 0.0     # Mass transfer coefficient [kg/(s·Pa·m²)]
        
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
        # Calculate pressure difference (Modelica: dP = VP_scr - VP_topAir)
        self.dP = self.massPort_a.VP - self.massPort_b.VP
        
        # Calculate mass transfer coefficient and mass flow
        if self.dP > 0:
            # Calculate VEC_ab as the minimum of two values (Modelica equation):
            # 1. Based on heat transfer coefficient
            # 2. Based on screen mass transfer coefficient
            self.VEC_ab = min(
                6.4e-9 * self.HEC_ab,
                self.VEC_AirScr * (self.VP_air - self.massPort_a.VP) / self.dP
            )
            # Calculate mass flow (Modelica: MV_flow = A*VEC_ab*dP)
            self.MV_flow = self.A * self.VEC_ab * self.dP
        else:
            # No evaporation when pressure difference is negative
            # Modelica: VEC_ab = 0; MV_flow = 0
            self.VEC_ab = 0
            self.MV_flow = 0
            
        # Update parent class
        super().update()
        
        return self.MV_flow
