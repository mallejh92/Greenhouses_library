from ..BaseClasses.PartialSinglePhaseCorrelation import PartialSinglePhaseCorrelation
from ..BaseClasses.PartialPlateHeatExchangerCorrelation import PartialPlateHeatExchangerCorrelation
import math

class Martin2010(PartialSinglePhaseCorrelation, PartialPlateHeatExchangerCorrelation):
    """
    The Martin approach for plate heat exchangers from VDI Heat Atlas
    
    This model extends PartialSinglePhaseCorrelation and PartialPlateHeatExchangerCorrelation
    to implement the Martin correlation for calculating heat transfer coefficients
    in plate heat exchangers.
    
    Attributes:
        s_w (float): Wall thickness [m]
        lambda_w (float): Conductivity of the wall [W/(m·K)]
        L_p (float): Plate length [m]
        Re_turb (float): Flow transition Re
        Re_tran (float): Flow transition range
        c_q (float): Empirical constant
        q (float): Empirical constant
        B_0 (float): Shape factor
        B_1 (float): Empirical pressure drop factor B_1
        C_1 (float): Empirical pressure drop factor C_1
        K_1 (float): Empirical pressure drop factor K_1
        n (float): Empirical pressure drop factor n
        a (float): Empirical pressure drop factor a
        b (float): Empirical pressure drop factor b
        c (float): Empirical pressure drop factor c
    """
    
    def __init__(self, s_w: float = 0.00075, lambda_w: float = 15.0, L_p: float = 0.2,
                 Re_turb: float = 2000.0, Re_tran: float = 100.0, c_q: float = 0.122,
                 q: float = 0.374, B_0: float = 64.0, B_1: float = 597.0,
                 C_1: float = 3.85, K_1: float = 39.0, n: float = 0.289,
                 a: float = 3.8, b: float = 0.18, c: float = 0.36):
        """
        Initialize Martin correlation model
        
        Args:
            s_w (float): Wall thickness [m]
            lambda_w (float): Conductivity of the wall [W/(m·K)]
            L_p (float): Plate length [m]
            Re_turb (float): Flow transition Re
            Re_tran (float): Flow transition range
            c_q (float): Empirical constant
            q (float): Empirical constant
            B_0 (float): Shape factor
            B_1 (float): Empirical pressure drop factor B_1
            C_1 (float): Empirical pressure drop factor C_1
            K_1 (float): Empirical pressure drop factor K_1
            n (float): Empirical pressure drop factor n
            a (float): Empirical pressure drop factor a
            b (float): Empirical pressure drop factor b
            c (float): Empirical pressure drop factor c
        """
        # Initialize with default d_h=0.01 for pipe correlation
        PartialSinglePhaseCorrelation.__init__(self, d_h=0.01)
        
        # Geometry parameters
        self.s_w = s_w  # Wall thickness
        self.lambda_w = lambda_w  # Wall conductivity
        self.L_p = L_p  # Plate length
        
        # Flow transition parameters
        self.Re_turb = Re_turb  # Flow transition Re
        self.Re_tran = Re_tran  # Flow transition range
        
        # Empirical constants
        self.c_q = c_q  # Empirical constant
        self.q = q      # Empirical constant
        self.B_0 = B_0  # Shape factor
        
        # Focke paper parameters
        self.B_1 = B_1  # Empirical pressure drop factor B_1
        self.C_1 = C_1  # Empirical pressure drop factor C_1
        self.K_1 = K_1  # Empirical pressure drop factor K_1
        self.n = n      # Empirical pressure drop factor n
        
        # Martin parameters
        self.a = a      # Empirical pressure drop factor a
        self.b = b      # Empirical pressure drop factor b
        self.c = c      # Empirical pressure drop factor c
        
        # Initialize variables
        self.Re = 0.0     # Reynolds number
        self.Pr = 0.0     # Prandtl number
        self.Nu = 0.0     # Nusselt number
        self.Hg = 0.0     # Hagen number
        self.xi = 0.0     # Friction factor
        self.xi_0 = 0.0   # Friction factor
        self.xi_0_lam = 0.0  # Laminar friction factor
        self.xi_0_tur = 0.0  # Turbulent friction factor
        self.xi_1 = 0.0   # Friction factor
        self.xi_1_lam = 0.0  # Laminar friction factor
        self.xi_1_tur = 0.0  # Turbulent friction factor
        self.lamTurb = 0.0  # Laminar or turbulent flow
        self.w = 0.0     # Fluid velocity
        
        # Fluid properties
        self.rho = 0.0   # Density
        self.T = 293.15  # Temperature [K]
        self.T_f_w = 293.15  # Wall temperature [K]
        self.T_f_w_in = 293.15  # Initial wall temperature [K]
        self.eta = 0.0   # Dynamic viscosity
        self.eta_f_w = 0.0  # Viscosity at wall temperature
        self.lambda_ = 0.0  # Thermal conductivity
        self.delta_p = 0.0  # Pressure drop
        self.V_dot = 0.0  # Volume flow rate
        
        # Intermediate calculations
        self.part1 = 0.0
        self.part2 = 0.0
    
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
        Calculate heat transfer coefficient using Martin correlation
        
        The correlation combines laminar and turbulent flow correlations
        with a smooth transition between them for plate heat exchangers.
        """
        # Get fluid properties from state
        self.rho = self.state.get('density', 1000.0)
        self.lambda_ = self.state.get('thermal_conductivity', 0.6)
        self.eta = self.state.get('dynamic_viscosity', 0.001)
        self.Pr = self.state.get('prandtl_number', 7.0)
        
        # Limit transport properties
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
        
        # Calculate basic variables
        self.V_dot = self.m_dot / self.rho
        self.w = abs(self.V_dot) / self.A_cro
        self.Re = (self.rho * abs(self.w) * self.d_h) / self.eta
        
        # Calculate wall temperature (simplified for initial calculation)
        self.T_f_w = self.T  # Assume wall temperature equals fluid temperature initially
        self.eta_f_w = self.eta  # Use fluid viscosity initially
        
        # Calculate transition factor
        self.lamTurb = self.transition_factor(
            self.Re_turb - self.Re_tran,
            self.Re_turb + self.Re_tran,
            self.Re
        )
        
        # Calculate friction factors
        self.xi_0_lam = self.B_0 / self.Re
        self.xi_0_tur = (1.8 * math.log10(self.Re) - 1.5) ** (-2)
        self.xi_0 = (1 - self.lamTurb) * self.xi_0_lam + self.lamTurb * self.xi_0_tur
        
        self.xi_1_lam = self.B_1 / self.Re + self.C_1
        self.xi_1_tur = self.K_1 / (self.Re ** self.n)
        self.xi_1 = self.a * ((1 - self.lamTurb) * self.xi_1_lam + self.lamTurb * self.xi_1_tur)
        
        # Calculate overall friction factor
        self.part1 = math.cos(self.phi) / math.sqrt(self.b * math.tan(self.phi) + 
                                                  self.c * math.sin(self.phi) + 
                                                  self.xi_0 / math.cos(self.phi))
        self.part2 = (1 - math.cos(self.phi)) / math.sqrt(self.xi_1)
        self.xi = 1 / (self.part1 + self.part2) ** 2
        
        # Calculate Hagen number and Nusselt number
        self.Hg = self.xi / 2 * self.Re ** 2
        self.Nu = (self.c_q * (self.Pr ** (1/3)) * 
                  (self.eta / self.eta_f_w) ** (1/6) * 
                  (2 * self.Hg * math.sin(2 * self.phi)) ** self.q)
        
        # Calculate heat transfer coefficient
        self.U = self.Nu * self.lambda_ / self.d_h
        
        # Update wall temperature after U is calculated
        if self.U > 0:
            self.T_f_w_in = self.q_dot / self.U + self.T
            self.T_f_w = self.T_f_w_in  # Update wall temperature
    
    def __str__(self) -> str:
        """String representation of the Martin correlation model"""
        return (f"Martin Correlation Model\n"
                f"Re = {self.Re:.2f}\n"
                f"Pr = {self.Pr:.2f}\n"
                f"Nu = {self.Nu:.2f}\n"
                f"U = {self.U:.2f} W/(m²·K)")
