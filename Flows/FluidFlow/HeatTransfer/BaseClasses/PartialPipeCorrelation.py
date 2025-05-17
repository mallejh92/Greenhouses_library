import math
from Flows.FluidFlow.HeatTransfer.BaseClasses.PartialHeatTransferCorrelation import PartialHeatTransferCorrelation

class PartialPipeCorrelation(PartialHeatTransferCorrelation):
    """
    Base class for heat transfer correlations for pipe flow
    
    This model is the base class for calculating heat transfer coefficients
    for pipes. It returns an enhanced HTC U and requires the characteristic
    length (hydraulic diameter) as input. For non-circular cross sections,
    the additional parameter A_cro can be used to decouple wetted perimeter
    and velocity calculations.
    
    Attributes:
        d_h (float): Hydraulic diameter [m]
        A_cro (float): Cross-sectional area [m²]
    """
    
    def __init__(self, d_h: float):
        """
        Initialize pipe correlation model
        
        Args:
            d_h (float): Hydraulic diameter [m]
        """
        super().__init__()
        
        # Geometry parameters
        self.d_h = d_h  # Hydraulic diameter
        self.A_cro = math.pi * d_h**2 / 4  # Cross-sectional area
    
    def __str__(self) -> str:
        """String representation of the pipe correlation model"""
        return (f"Pipe Correlation Model\n"
                f"d_h = {self.d_h:.4f} m\n"
                f"A_cro = {self.A_cro:.4f} m²")

if __name__ == "__main__":
    # 테스트 코드
    model = PartialPipeCorrelation(d_h=0.01)
    print(model)
