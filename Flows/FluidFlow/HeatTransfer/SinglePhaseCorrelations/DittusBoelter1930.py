from ..BaseClasses.PartialSinglePhaseCorrelation import PartialSinglePhaseCorrelation
from ..BaseClasses.PartialPlateHeatExchangerCorrelation import PartialPlateHeatExchangerCorrelation

class DittusBoelter1930(PartialSinglePhaseCorrelation, PartialPlateHeatExchangerCorrelation):
    """
    The Dittus-Boelter correlation for turbulent single phase flow
    
    This model extends PartialSinglePhaseCorrelation and PartialPlateHeatExchangerCorrelation
    to implement the Dittus-Boelter correlation for calculating heat transfer coefficients
    in turbulent single-phase flow.
    
    Attributes:
        a (float): Factor (0.023 for pipe, 0.035 for plate HX)
        b (float): Reynolds exponent (0.800)
        c (float): Prandtl exponent (0.400 for heating, 0.300 for cooling)
        cLen (float): Characteristic length [m]
        cVel (float): Characteristic velocity [m/s]
        Re (float): Reynolds number
        Pr (float): Prandtl number
        Nu (float): Nusselt number
        lambda_ (float): Thermal conductivity [W/(m·K)]
        eta (float): Dynamic viscosity [Pa·s]
        rho (float): Density [kg/m³]
        V_dot (float): Volume flow rate [m³/s]
    """
    
    def __init__(self, a: float = 0.023, b: float = 0.800, c: float = 0.400):
        """
        Initialize Dittus-Boelter correlation model
        
        Args:
            a (float): Factor (0.023 for pipe, 0.035 for plate HX)
            b (float): Reynolds exponent
            c (float): Prandtl exponent (0.400 for heating, 0.300 for cooling)
        """
        # Initialize with default d_h=0.01 for pipe correlation
        PartialSinglePhaseCorrelation.__init__(self, d_h=0.01)
        
        # Correlation parameters
        self.a = a  # Factor
        self.b = b  # Reynolds exponent
        self.c = c  # Prandtl exponent
        
        # Initialize variables
        self.cLen = 0.0  # Characteristic length
        self.cVel = 0.0  # Characteristic velocity
        self.Re = 0.0    # Reynolds number
        self.Pr = 0.0    # Prandtl number
        self.Nu = 0.0    # Nusselt number
        self.lambda_ = 0.0  # Thermal conductivity
        self.eta = 0.0   # Dynamic viscosity
        self.rho = 0.0   # Density
        self.V_dot = 0.0 # Volume flow rate
    
    def calculate(self) -> None:
        """
        Calculate heat transfer coefficient using Dittus-Boelter correlation
        
        The correlation is: Nu = a * Re^b * Pr^c
        where:
        - Nu is the Nusselt number
        - Re is the Reynolds number
        - Pr is the Prandtl number
        - a, b, c are correlation parameters
        
        The heat transfer coefficient is then calculated as:
        U = Nu * lambda_ / cLen
        """
        # Get fluid properties from state
        self.rho = self.state.get('density', 1000.0)
        self.lambda_ = self.state.get('thermal_conductivity', 0.6)
        self.eta = self.state.get('dynamic_viscosity', 0.001)
        self.Pr = self.state.get('prandtl_number', 7.0)
        
        # Limit transport properties as in Modelica code
        self.Pr = min(100, self.Pr)
        self.eta = min(10, self.eta)
        self.lambda_ = min(10, self.lambda_)
        
        # Validate transport properties
        if self.Pr <= 0:
            raise ValueError("Invalid Prandtl number, make sure transport properties are calculated.")
        if self.eta <= 0:
            raise ValueError("Invalid viscosity, make sure transport properties are calculated.")
        if self.lambda_ <= 0:
            raise ValueError("Invalid thermal conductivity, make sure transport properties are calculated.")
        
        # Calculate characteristic length and velocity
        self.cLen = self.d_h
        self.V_dot = self.m_dot / self.rho
        self.cVel = abs(self.V_dot) / self.A_cro
        
        # Calculate Reynolds number
        self.Re = (self.rho * abs(self.cVel) * self.cLen) / self.eta
        
        # Optional: Check for turbulent flow
        # if self.Re <= 1000:
        #     raise ValueError("Invalid Reynolds number, Dittus-Boelter is only for fully turbulent flow.")
        
        # Calculate Nusselt number using Dittus-Boelter correlation
        self.Nu = self.a * (self.Re ** self.b) * (self.Pr ** self.c)
        
        # Calculate heat transfer coefficient
        self.U = self.Nu * self.lambda_ / self.cLen
    
    def __str__(self) -> str:
        """String representation of the Dittus-Boelter correlation model"""
        return (f"Dittus-Boelter Correlation Model\n"
                f"a = {self.a:.3f}\n"
                f"b = {self.b:.3f}\n"
                f"c = {self.c:.3f}\n"
                f"Re = {self.Re:.2f}\n"
                f"Pr = {self.Pr:.2f}\n"
                f"Nu = {self.Nu:.2f}\n"
                f"U = {self.U:.2f} W/(m²·K)")