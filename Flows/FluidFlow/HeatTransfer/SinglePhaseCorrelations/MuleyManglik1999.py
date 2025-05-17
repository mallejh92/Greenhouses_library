from ..BaseClasses.PartialSinglePhaseCorrelation import PartialSinglePhaseCorrelation
from ..BaseClasses.PartialPlateHeatExchangerCorrelation import PartialPlateHeatExchangerCorrelation
import math

class MuleyManglik1999(PartialSinglePhaseCorrelation, PartialPlateHeatExchangerCorrelation):
    """
    Heat transfer in plate heat exchangers, Muley and Manglik 1999
    
    This model extends PartialSinglePhaseCorrelation and PartialPlateHeatExchangerCorrelation
    to implement the Muley-Manglik correlation for calculating heat transfer coefficients
    in plate heat exchangers.
    
    Attributes:
        Re_lam (float): Fully laminar Reynolds number
        Re_tur (float): Fully turbulent Reynolds number
    """
    
    def __init__(self, Re_lam: float = 400.0, Re_tur: float = 1000.0):
        """
        Initialize Muley-Manglik correlation model
        
        Args:
            Re_lam (float): Fully laminar Reynolds number
            Re_tur (float): Fully turbulent Reynolds number
        """
        # Initialize with default d_h=0.01 for pipe correlation
        PartialSinglePhaseCorrelation.__init__(self, d_h=0.01)
        
        # Flow transition parameters
        self.Re_lam = Re_lam  # Fully laminar Reynolds number
        self.Re_tur = Re_tur  # Fully turbulent Reynolds number
        
        # Initialize variables
        self.Re = 0.0     # Reynolds number
        self.lamTur = 0.0  # Laminar-turbulent transition factor
        self.Pr = 0.0     # Prandtl number
        self.Nu = 0.0     # Nusselt number
        self.Nu_lam = 0.0  # Laminar Nusselt number
        self.Nu_tur = 0.0  # Turbulent Nusselt number
        
        # Fluid properties
        self.rho = 0.0   # Density
        self.T = 293.15  # Temperature [K]
        self.T_f_w = 293.15  # Wall temperature [K]
        self.T_f_w_in = 293.15  # Initial wall temperature [K]
        self.eta = 0.0   # Dynamic viscosity
        self.eta_f_w = 0.0  # Viscosity at wall temperature
        self.lambda_ = 0.0  # Thermal conductivity
        self.V_dot = 0.0  # Volume flow rate
        self.w = 0.0     # Fluid velocity
        
        # Intermediate calculations
        self.commonTerm = 0.0
    
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
        Calculate heat transfer coefficient using Muley-Manglik correlation
        
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
        self.lamTur = self.transition_factor(self.Re_lam, self.Re_tur, self.Re)
        
        # Calculate common term
        self.commonTerm = (self.Pr ** (1/3)) * (self.eta / self.eta_f_w) ** 0.14
        
        # Calculate turbulent Nusselt number
        phi_deg = math.degrees(self.phi)
        self.Nu_tur = ((2.668e-1 - 6.967e-3 * phi_deg + 7.244e-5 * phi_deg**2) *
                       (2.078e+1 - 5.094e+1 * self.Phi + 4.116e+1 * self.Phi**2 - 1.015e+1 * self.Phi**3) *
                       (self.Re ** (0.728 + 0.0543 * math.sin(math.pi * phi_deg / 45 + 3.7))) *
                       self.commonTerm)
        
        # Calculate laminar Nusselt number
        self.Nu_lam = (0.44 * (phi_deg / 30) ** 0.38 *
                      self.Re ** 0.5 *
                      self.commonTerm)
        
        # Calculate overall Nusselt number
        self.Nu = (1 - self.lamTur) * self.Nu_lam + self.lamTur * self.Nu_tur
        
        # Calculate heat transfer coefficient
        self.U = self.Nu * self.lambda_ / self.d_h
        
        # Update wall temperature after U is calculated
        if self.U > 0:
            self.T_f_w_in = self.q_dot / self.U + self.T
            self.T_f_w = self.T_f_w_in  # Update wall temperature
    
    def __str__(self) -> str:
        """String representation of the Muley-Manglik correlation model"""
        return (f"Muley-Manglik Correlation Model\n"
                f"Re = {self.Re:.2f}\n"
                f"Pr = {self.Pr:.2f}\n"
                f"Nu_lam = {self.Nu_lam:.2f}\n"
                f"Nu_tur = {self.Nu_tur:.2f}\n"
                f"Nu = {self.Nu:.2f}\n"
                f"U = {self.U:.2f} W/(m²·K)")
