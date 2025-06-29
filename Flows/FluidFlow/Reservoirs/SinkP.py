from Modelica.Fluid.Interfaces.FluidPort_b import FluidPort_b

class SinkP:
    """
    Python version of Greenhouses.Flows.FluidFlow.Reservoirs.SinkP
    Pressure sink for fluid flows (e.g., heating water return)
    """
    def __init__(self, p0=1.01325e5, h=1e5):
        """
        Initialize pressure sink
        
        Parameters:
            p0 (float): Nominal pressure [Pa]
            h (float): Nominal specific enthalpy [J/kg]
        """
        # Parameters
        self.p0 = p0        # Nominal pressure [Pa]
        self.h = h          # Nominal specific enthalpy [J/kg]
        
        # Input signals (if None, use parameter)
        self.in_p0 = None
        self.in_h = None
        
        # Output port
        self.flangeB = FluidPort_b(p_start=p0, h_start=h)
        self.p = p0  # Current pressure

    def step(self, dt: float):
        """
        Update the output port based on current input signals or parameters.
        
        Args:
            dt (float): Time step [s]
        """
        # Use input signals if provided, otherwise use default parameters
        p = self.in_p0 if self.in_p0 is not None else self.p0
        h = self.in_h if self.in_h is not None else self.h

        # Set pressure and enthalpy at the output port
        self.flangeB.p = p
        self.flangeB.h_outflow = h
        self.p = p

# 0604
