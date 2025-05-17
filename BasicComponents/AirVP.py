import numpy as np

class AirVP:
    """
    Python version of the Modelica Greenhouses.BasicComponents.AirVP model.
    This class models the vapor pressure in air.
    """
    def __init__(self, V_air, steadystate=False):
        # Parameters
        self.V_air = V_air          # Air volume [m³]
        self.steadystate = steadystate
        
        # State
        self.VP = 0.0               # Vapor pressure [Pa]
        self.massPort_VP = 0.0      # Input vapor pressure [Pa]
        
    def update(self, massPort_VP):
        """
        Update the vapor pressure state
        """
        self.massPort_VP = massPort_VP
        if not self.steadystate:
            # Simple model: VP follows input with some time constant
            self.VP = massPort_VP
        return self.VP 