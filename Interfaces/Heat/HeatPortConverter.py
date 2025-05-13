from Interfaces.Heat.HeatPort_a import HeatPort_a
from Interfaces.Heat.ThermalPortL import ThermalPortL

class HeatPortConverter:
    """
    Convert thermal port into heat port
    
    This model converts between Modelica's HeatPort_a and ThermalPortL.
    It maintains the connection between temperature and heat flux values,
    with heat flux being calculated from heat flow rate divided by area.
    
    Attributes:
        N (int): Number of nodes (default: 10)
        A (float): Heat exchange area in m² (default: 1.0)
        heatPort (HeatPort_a): Heat port connector
        thermalPortL (ThermalPortL): Thermal port connector
    """
    
    def __init__(self, N: int = 10, A: float = 1.0):
        """
        Initialize HeatPortConverter
        
        Args:
            N (int): Number of nodes (default: 10)
            A (float): Heat exchange area in m² (default: 1.0)
        """
        self.N = N
        self.A = float(A)
        self.heatPort = HeatPort_a()
        self.thermalPortL = ThermalPortL()
    
    def update(self) -> None:
        """
        Update the connection between heat port and thermal port
        
        This method implements the Modelica equations:
        - thermalPortL.T = heatPort.T
        - thermalPortL.phi = -heatPort.Q_flow/A
        """
        # Update thermal port from heat port
        self.thermalPortL.set_temperature(self.heatPort.T)
        # Convert heat flow rate to heat flux (note the negative sign)
        heat_flux = -self.heatPort.Q_flow / self.A
        self.thermalPortL.set_heat_flux(heat_flux)
    
    def connect_heat_port(self, other: HeatPort_a) -> None:
        """
        Connect the heat port to another HeatPort_a
        
        Args:
            other (HeatPort_a): HeatPort_a to connect with
        """
        self.heatPort = other
        self.update()
    
    def connect_thermal_port(self, other: ThermalPortL) -> None:
        """
        Connect the thermal port to another ThermalPortL
        
        Args:
            other (ThermalPortL): ThermalPortL to connect with
        """
        self.thermalPortL = other
        self.update()
    
    def __str__(self) -> str:
        """String representation of the converter"""
        return (f"HeatPortConverter(N={self.N}, A={self.A} m²)\n"
                f"Heat Port:\n{self.heatPort}\n"
                f"Thermal Port:\n{self.thermalPortL}")
