from Interfaces.Vapour.WaterMassPort import WaterMassPort

class WaterMassPort_b(WaterMassPort):
    """
    Water mass port for 1-dim. water vapour mass transfer (unfilled rectangular icon).
    Functionally identical to WaterMassPort, only icon differs in Modelica.
    
    According to the Modelica sign convention, a positive mass flow rate MV_flow
    is considered to flow into a component. This convention has to be used whenever
    this connector is used in a model class.
    
    Note that WaterMassPort_a and WaterMassPort_b are identical with the only
    exception of the different icon layout.
    """
    def __init__(self, VP=None, MV_flow=None):
        """
        Initialize WaterMassPort_b
        
        Parameters:
        -----------
        VP : float, optional
            Initial vapor pressure [Pa]
        MV_flow : float, optional
            Initial mass flow rate [kg/s]
        """
        super().__init__(VP=VP, MV_flow=MV_flow)