from ..BaseClasses.PartialSinglePhaseCorrelation import PartialSinglePhaseCorrelation
from ..BaseClasses.PartialPipeCorrelation import PartialPipeCorrelation
import math

class Gnielinski2010(PartialSinglePhaseCorrelation, PartialPipeCorrelation):
    """
    Gnielinski pipe equations for heat transfer calculation
    
    This model extends PartialSinglePhaseCorrelation and PartialPipeCorrelation
    to implement the Gnielinski correlation for calculating heat transfer coefficients
    in pipe flow.
    
    Attributes:
        d_i (float): Hydraulic diameter [m]
        l (float): Pipe or plate length [m]
        Re (float): Reynolds number
        Re_tur (float): Turbulent Reynolds number
        Re_lam (float): Laminar Reynolds number
        Pr (float): Prandtl number
        lambda_ (float): Thermal conductivity [W/(m·K)]
        eta (float): Dynamic viscosity [Pa·s]
        cp (float): Specific heat capacity [J/(kg·K)]
        rho (float): Density [kg/m³]
        Nu_m_T_1 (float): Nusselt number for constant wall temperature (Eq. 4)
        Nu_m_T_2 (float): Nusselt number for constant wall temperature (Eq. 5)
        Nu_m_T_3 (float): Nusselt number for constant wall temperature (Eq. 11)
        Nu_m_T (float): Nusselt number for constant wall temperature (Eq. 12)
        gamma (float): Transition factor
        xtra (float): Reynolds correction factor
        zeta (float): Friction factor
        K (float): Correction term
        Nu_m (float): Nusselt number for fully developed turbulent flow
        Nu (float): Final Nusselt number
        cLen (float): Characteristic length [m]
        cVel (float): Characteristic velocity [m/s]
        V_dot (float): Volume flow rate [m³/s]
    """
    
    def __init__(self, d_i: float = 0.01, l: float = 0.250):
        """
        Initialize Gnielinski correlation model
        
        Args:
            d_i (float): Hydraulic diameter [m]
            l (float): Pipe or plate length [m]
        """
        # Initialize with d_h=d_i for pipe correlation
        PartialSinglePhaseCorrelation.__init__(self, d_h=d_i)
        
        # Geometry parameters
        self.d_i = d_i  # Hydraulic diameter
        self.l = l      # Pipe or plate length
        
        # Initialize variables
        self.Re = 0.0     # Reynolds number
        self.Re_tur = 0.0 # Turbulent Reynolds number
        self.Re_lam = 0.0 # Laminar Reynolds number
        self.Pr = 0.0     # Prandtl number
        
        # Fluid properties
        self.lambda_ = 0.0  # Thermal conductivity
        self.eta = 0.0      # Dynamic viscosity
        self.cp = 0.0       # Specific heat capacity
        self.rho = 0.0      # Density
        
        # Nusselt numbers for constant wall temperature
        self.Nu_m_T_1 = 0.0  # Eq. 4
        self.Nu_m_T_2 = 0.0  # Eq. 5
        self.Nu_m_T_3 = 0.0  # Eq. 11
        self.Nu_m_T = 0.0    # Eq. 12
        
        # Turbulent flow parameters
        self.gamma = 0.0  # Transition factor
        self.xtra = 0.0   # Reynolds correction factor
        self.zeta = 0.0   # Friction factor
        self.K = 1.0      # Correction term
        self.Nu_m = 0.0   # Nusselt number for turbulent flow
        self.Nu = 0.0     # Final Nusselt number
        
        # Other variables
        self.cLen = 0.0   # Characteristic length
        self.cVel = 0.0   # Characteristic velocity
        self.V_dot = 0.0  # Volume flow rate
    
    def transition_factor(self, start: float, stop: float, position: float) -> float:
        """
        Calculate transition factor between laminar and turbulent flow
        
        Args:
            start (float): Start position
            stop (float): Stop position
            position (float): Current position
            
        Returns:
            float: Transition factor
        """
        return max(0, min(1, (position - start) / (stop - start)))
    
    def calculate(self) -> None:
        """
        Calculate heat transfer coefficient using Gnielinski correlation
        
        The correlation combines laminar and turbulent flow correlations
        with a smooth transition between them.
        """
        # Get fluid properties from state
        self.eta = self.state.get('dynamic_viscosity', 0.001)
        self.lambda_ = self.state.get('thermal_conductivity', 0.6)
        self.cp = self.state.get('specific_heat_capacity', 4186.0)
        self.rho = self.state.get('density', 1000.0)
        
        # Validate transport properties
        if self.eta <= 0:
            raise ValueError("Invalid viscosity, make sure transport properties are calculated.")
        if self.lambda_ <= 0:
            raise ValueError("Invalid thermal conductivity, make sure transport properties are calculated.")
        if self.cp <= 0:
            raise ValueError("Invalid heat capacity, make sure that you are not in the two-phase region.")
        
        # Calculate basic variables
        self.V_dot = self.m_dot / self.rho
        self.cVel = abs(self.V_dot) / self.A_cro
        self.cLen = self.d_i
        self.Pr = self.cp * self.eta / self.lambda_
        
        # Calculate Reynolds number
        self.Re = (self.rho * abs(self.cVel) * self.cLen) / self.eta
        self.Re_lam = min(self.Re, 2300)
        self.Re_tur = max(self.Re, 10000)
        
        # Calculate Nusselt numbers for constant wall temperature
        self.Nu_m_T_1 = 3.66  # Eq. 4
        self.Nu_m_T_2 = 1.615 * (self.Re_lam * self.Pr * self.d_i/self.l) ** (1/3)  # Eq. 5
        self.Nu_m_T_3 = (2/(1+22*self.Pr)) ** (1/6) * (self.Re_lam * self.Pr * self.d_i/self.l) ** (1/2)  # Eq. 11
        self.Nu_m_T = (self.Nu_m_T_1**3 + 0.7**3 + (self.Nu_m_T_2-0.7)**3 + self.Nu_m_T_3**3) ** (1/3)  # Eq. 12
        
        # Calculate turbulent flow parameters
        self.zeta = (1.80 * math.log10(self.Re_tur) - 1.50) ** (-2)  # Eq. 27
        self.xtra = 0.0
        self.K = 1.0
        
        # Calculate Nusselt number for turbulent flow
        numerator = (self.zeta/8.0) * (self.Re_tur - self.xtra) * self.Pr
        denominator = 1 + 12.7 * math.sqrt(self.zeta/8.0) * (self.Pr ** (2.0/3.0) - 1.0)
        self.Nu_m = (numerator / denominator) * (1 + (self.d_i/self.l) ** (2.0/3.0)) * self.K
        
        # Calculate transition factor and final Nusselt number
        self.gamma = self.transition_factor(2300, 10000, self.Re)
        self.Nu = (1 - self.gamma) * self.Nu_m_T + self.gamma * self.Nu_m
        
        # Calculate heat transfer coefficient
        self.U = self.Nu * self.lambda_ / self.cLen
    
    def __str__(self) -> str:
        """String representation of the Gnielinski correlation model"""
        return (f"Gnielinski Correlation Model\n"
                f"d_i = {self.d_i:.4f} m\n"
                f"l = {self.l:.4f} m\n"
                f"Re = {self.Re:.2f}\n"
                f"Pr = {self.Pr:.2f}\n"
                f"Nu = {self.Nu:.2f}\n"
                f"U = {self.U:.2f} W/(m²·K)")
