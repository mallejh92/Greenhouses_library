import math
from Flows.FluidFlow.HeatTransfer.BaseClasses.PartialHeatTransferCorrelation import PartialHeatTransferCorrelation

class PartialPlateHeatExchangerCorrelation(PartialHeatTransferCorrelation):
    """
    Base class for heat transfer correlations for plate heat exchangers
    
    This model is the basic model for calculating heat transfer coefficients
    for plate heat exchangers. It provides basic geometric definitions and
    returns an enhanced HTC U based on geometry and alpha.
    
    Attributes:
        a_hat (float): Corrugation amplitude [m]
        phi (float): Corrugation angle [rad]
        Lambda (float): Corrugation wavelength [m]
        B_p (float): Plate flow width [m]
        X (float): Wave number
        Phi (float): Enhancement factor
        d_h (float): Characteristic length [m]
        A_cro (float): Cross-sectional area [m²]
        alpha (float): The calculated HTC [W/(m²·K)]
    """
    
    def __init__(self, a_hat: float = 0.002, phi: float = math.radians(45),
                 Lambda: float = 0.0126, B_p: float = 0.1):
        """
        Initialize plate heat exchanger correlation model
        
        Args:
            a_hat (float): Corrugation amplitude [m]
            phi (float): Corrugation angle [rad]
            Lambda (float): Corrugation wavelength [m]
            B_p (float): Plate flow width [m]
        """
        super().__init__()
        
        # Geometry parameters
        self.a_hat = a_hat  # Corrugation amplitude
        self.phi = phi      # Corrugation angle
        self.Lambda = Lambda  # Corrugation wavelength
        self.B_p = B_p      # Plate flow width
        
        # Calculate derived parameters
        self.X = 2 * math.pi * self.a_hat / self.Lambda  # Wave number
        self.Phi = (1/6) * (1 + math.sqrt(1 + self.X**2) + 
                           4 * math.sqrt(1 + self.X**2/2))  # Enhancement factor
        self.d_h = 4 * self.a_hat / self.Phi  # Characteristic length
        self.A_cro = 2 * self.a_hat * self.B_p  # Cross-sectional area
        
        # Heat transfer coefficient
        self.alpha = 0.0  # The calculated HTC
    
    def calculate(self) -> None:
        """
        Calculate enhanced heat transfer coefficient
        
        The enhanced HTC (U) is calculated as:
        U = Phi * alpha
        where Phi is the enhancement factor and alpha is the calculated HTC
        """
        self.U = self.Phi * self.alpha
    
    def __str__(self) -> str:
        """String representation of the plate heat exchanger correlation model"""
        return (f"Plate Heat Exchanger Correlation Model\n"
                f"a_hat = {self.a_hat:.4f} m\n"
                f"phi = {math.degrees(self.phi):.1f}°\n"
                f"Lambda = {self.Lambda:.4f} m\n"
                f"B_p = {self.B_p:.4f} m\n"
                f"X = {self.X:.2f}\n"
                f"Phi = {self.Phi:.2f}\n"
                f"d_h = {self.d_h:.4f} m\n"
                f"A_cro = {self.A_cro:.4f} m²\n"
                f"alpha = {self.alpha:.2f} W/(m²·K)\n"
                f"U = {self.U:.2f} W/(m²·K)")

if __name__ == "__main__":
    # 테스트 코드
    model = PartialPlateHeatExchangerCorrelation()
    print(model)
    model.alpha = 1000.0
    model.calculate()
    print(f"Calculated U: {model.U} W/(m²·K)")
