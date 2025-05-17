class PartialHeatTransferCorrelation:
    """
    Base class for all heat transfer correlations
    
    This is the base class for calculating heat transfer coefficients.
    It returns a heat transfer coefficient (U) and requires a thermodynamic state,
    the inlet mass flow rate and the heat flux as inputs.
    
    Attributes:
        m_dot (float): Inlet mass flow rate [kg/s]
        q_dot (float): Heat flow rate per area [W/m²]
        U (float): Heat transfer coefficient [W/(m²·K)]
    """
    
    def __init__(self):
        """Initialize heat transfer correlation model"""
        self.m_dot = 0.0  # Inlet mass flow rate
        self.q_dot = 0.0  # Heat flow rate per area
        self.U = 0.0      # Heat transfer coefficient
    
    def update_parameters(self, m_dot: float, q_dot: float) -> None:
        """
        Update input parameters
        
        Args:
            m_dot (float): Inlet mass flow rate [kg/s]
            q_dot (float): Heat flow rate per area [W/m²]
        """
        self.m_dot = m_dot
        self.q_dot = q_dot
    
    def calculate(self) -> None:
        """
        Calculate heat transfer coefficient
        
        This method should be overridden by subclasses to implement
        specific heat transfer correlation calculations.
        """
        raise NotImplementedError("Subclasses must implement calculate() method")
    
    def get_heat_transfer_coefficient(self) -> float:
        """
        Get the calculated heat transfer coefficient
        
        Returns:
            float: Heat transfer coefficient [W/(m²·K)]
        """
        return self.U
    
    def __str__(self) -> str:
        """String representation of the heat transfer correlation"""
        return (f"Heat Transfer Correlation\n"
                f"m_dot = {self.m_dot:.2f} kg/s\n"
                f"q_dot = {self.q_dot:.2f} W/m²\n"
                f"U = {self.U:.2f} W/(m²·K)")
