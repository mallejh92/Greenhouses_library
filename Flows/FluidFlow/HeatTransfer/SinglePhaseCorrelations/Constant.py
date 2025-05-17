from Flows.FluidFlow.HeatTransfer.BaseClasses.PartialSinglePhaseCorrelation import PartialSinglePhaseCorrelation
from Flows.FluidFlow.HeatTransfer.BaseClasses.PartialPipeCorrelation import PartialPipeCorrelation
from Flows.FluidFlow.HeatTransfer.BaseClasses.PartialPlateHeatExchangerCorrelation import PartialPlateHeatExchangerCorrelation
from Flows.FluidFlow.HeatTransfer.BaseClasses.PartialHeatTransferCorrelation import PartialHeatTransferCorrelation

class Constant(PartialSinglePhaseCorrelation, PartialPipeCorrelation, PartialPlateHeatExchangerCorrelation):
    """
    Constant heat transfer coefficient model
    
    This model extends PartialSinglePhaseCorrelation, PartialPipeCorrelation,
    and PartialPlateHeatExchangerCorrelation to define a constant heat
    transfer coefficient.
    
    Attributes:
        U_c (float): Heat transfer coefficient [W/(m²·K)]
    """
    
    def __init__(self, U_c: float = 1000.0):
        """
        Initialize constant heat transfer coefficient model
        
        Args:
            U_c (float): Heat transfer coefficient [W/(m²·K)]
            
        Raises:
            ValueError: If U_c is less than or equal to 0
        """
        # Validate input
        if U_c <= 0:
            raise ValueError("Heat transfer coefficient (U_c) must be greater than 0")
        
        # Initialize with d_h=0 for all parent classes
        d_h = 0.0
        
        # Initialize parent classes in correct order
        PartialHeatTransferCorrelation.__init__(self)  # Initialize base class first
        PartialPipeCorrelation.__init__(self, d_h=d_h)
        PartialSinglePhaseCorrelation.__init__(self, d_h=d_h)
        
        # Set constant heat transfer coefficient
        self.U_c = U_c  # Heat transfer coefficient
        
        # Override plate heat exchanger parameters
        self.a_hat = 0.0
        self.phi = 0.0
        self.Lambda = 1.0  # Avoid division by zero
        self.B_p = 0.0
        self.X = 0.0
        self.Phi = 1.0
        self.d_h = 0.0
        self.A_cro = 0.0
        self.alpha = 0.0
    
    def calculate(self) -> None:
        """
        Calculate heat transfer coefficient
        
        For constant model, the heat transfer coefficient is simply U_c
        """
        self.U = self.U_c
    
    def __str__(self) -> str:
        """String representation of the constant heat transfer model"""
        return (f"Constant Heat Transfer Model\n"
                f"U_c = {self.U_c:.2f} W/(m²·K)")

if __name__ == "__main__":
    # 테스트 코드
    model = Constant()
    print(model)
    model.calculate()
    print(f"Calculated U: {model.U} W/(m²·K)")
