# WaterMassPort_a.py
from Interfaces.Vapour.WaterMassPort import WaterMassPort

class WaterMassPort_a(WaterMassPort):
    """
    Water mass port for 1-dim. water vapour mass transfer (filled rectangular icon).
    Functionally identical to WaterMassPort, only icon differs in Modelica.
    
    According to the Modelica sign convention, a positive mass flow rate MV_flow
    is considered to flow into a component. This convention has to be used whenever
    this connector is used in a model class.
    
    Note that WaterMassPort_a and WaterMassPort_b are identical with the only
    exception of the different icon layout.
    """
    def __init__(self, VP_start=0.04e5, P_start=101325):
        super().__init__(VP_start=VP_start, P_start=P_start)