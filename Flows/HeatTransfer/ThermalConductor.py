from Interfaces.Heat.Element1D import Element1D

class ThermalConductor(Element1D):
    """
    Lumped thermal element transporting heat without storing it
    
    This class implements the thermal conductor model that transports heat
    without storing it, inheriting from Element1D.
    
    The thermal conductance G may be calculated for different geometries:
    
    1. Box geometry (heat flows along box length):
       G = k*A/L
       where:
       k: Thermal conductivity (material constant)
       A: Area of box
       L: Length of box
    
    2. Cylindrical geometry (heat flows from inside to outside radius):
       G = 2*pi*k*L/log(r_out/r_in)
       where:
       pi: 3.14159...
       k: Thermal conductivity (material constant)
       L: Length of cylinder
       r_out: Outer radius of cylinder
       r_in: Inner radius of cylinder
    
    Typical values for k at 20 degC in W/(m.K):
      aluminium   220
      concrete      1
      copper      384
      iron         74
      silver      407
      steel        45 .. 15 (V2A)
      wood         0.1 ... 0.2
    """
    
    def __init__(self, G=1.0):
        """
        Initialize the ThermalConductor model
        
        Parameters:
        -----------
        G : float, optional
            Constant thermal conductance of material [W/K], default is 1.0
        """
        super().__init__()  # Initialize Element1D
        
        self.G = G  # Thermal conductance of material
        
    def calculate(self):
        """
        Calculate heat transfer through the thermal conductor
        
        Returns:
        --------
        Q_flow : float
            Heat flow rate [W]
        """
        # Calculate heat flow using Q_flow = G * dT
        self.Q_flow = self.G * self.dT
        
        return self.Q_flow
