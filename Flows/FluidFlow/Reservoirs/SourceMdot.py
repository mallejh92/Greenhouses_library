from Modelica.Fluid.Interfaces.FluidPort_b import FluidPort_b

class SourceMdot:
    """
    Python version of Greenhouses.Flows.FluidFlow.Reservoirs.SourceMdot
    Mass flow source for fluid flows (e.g., heating water supply)
    """
    def __init__(self, Mdot_0=0.0, p=101325, UseT=True, T_0=298.15, h_0=0.0, Medium=None):
        # Parameters
        self.Mdot_0 = Mdot_0  # Default mass flow rate [kg/s]
        self.p = p            # Pressure [Pa]
        self.UseT = UseT      # Use temperature as input (True) or enthalpy (False)
        self.T_0 = T_0        # Default temperature [K]
        self.h_0 = h_0        # Default enthalpy [J/kg]
        self.Medium = Medium  # Medium model (optional)
        # Input signals (if None, use parameter)
        self.in_Mdot = None
        self.in_T = None
        self.in_h = None
        # Output port
        self.flangeB = FluidPort_b(Medium=self.Medium, p_start=p, h_start=h_0)
        self.h = 0.0  # Calculated specific enthalpy

    def step(self, dt: float) -> float:
        """
        Update the output port based on current input signals or parameters.
        
        Args:
            dt (float): Time step [s]
        """
        # Use input signals if provided, otherwise use default parameters
        m_flow = self.in_Mdot if self.in_Mdot is not None else self.Mdot_0
        T = self.in_T if self.in_T is not None else self.T_0
        h = self.in_h if self.in_h is not None else self.h_0

        # Set mass flow at the output port (negative sign as in Modelica)
        self.flangeB.m_flow = -m_flow
        self.flangeB.p = self.p

        # Set enthalpy at the output port
        if self.UseT:
            # If Medium model provides enthalpy calculation, use it
            if self.Medium and hasattr(self.Medium, 'specificEnthalpy_pTX'):
                self.h = self.Medium.specificEnthalpy_pTX(self.p, T, [])
            else:
                # For water: h = c_p * T (approximate)
                c_p = 4186.0  # [J/kg·K] for water
                self.h = c_p * T
            self.flangeB.h_outflow = self.h
        else:
            self.flangeB.h_outflow = h
            self.h = h
