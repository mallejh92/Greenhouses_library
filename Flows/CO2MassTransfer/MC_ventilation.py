from HeatAndVapourTransfer.VentilationRates.NaturalVentilationRate_2 import NaturalVentilationRate_2

class MC_ventilation:
    """
    CO2 mass flow exchange accompanying an air ventilation process.
    Distinguishes from the two different air zones on the presence of a thermal screen.
    """
    
    def __init__(self, thermalScreen: bool = False, topAir: bool = False):
        """
        Initialize ventilation CO2 mass flow model
        
        Parameters:
            thermalScreen (bool): Presence of a thermal screen in the greenhouse
            topAir (bool): False for Main air zone, True for Top air zone
        """
        # Parameters
        self.thermalScreen = thermalScreen
        self.topAir = topAir
        
        # Input variables
        self.SC = 0.0  # Screen closure 1:closed, 0:open
        self.U_vents = 0.0  # From 0 to 1, control of the aperture of the roof vents
        self.T_a = 300.0  # Temperature at port a [K]
        self.T_b = 300.0  # Temperature at port b [K]
        self.u = 0.0  # Wind speed [m/s]
        
        # State variables
        self.f_vent = 0.0  # Ventilation factor
        self.MC_flow = 0.0  # CO2 mass flow rate [mg/(m2.s)]
        self.dC = 0.0  # CO2 concentration difference [mg/m3]
        
        # Create ventilation rate calculator
        self.airExchangeRate = NaturalVentilationRate_2(
            thermalScreen=thermalScreen,
            u=self.u,
            dT=self.T_a - self.T_b,
            U_roof=self.U_vents,
            SC=self.SC,
            T_a=self.T_a,
            T_b=self.T_b
        )
        
    def update(self, SC: float = None, U_vents: float = None, 
              T_a: float = None, T_b: float = None, u: float = None,
              dC: float = None) -> float:
        """
        Update ventilation CO2 mass flow
        
        Parameters:
            SC (float, optional): Screen closure (1:closed, 0:open)
            U_vents (float, optional): Roof vent aperture (0 to 1)
            T_a (float, optional): Temperature at port a [K]
            T_b (float, optional): Temperature at port b [K]
            u (float, optional): Wind speed [m/s]
            dC (float, optional): CO2 concentration difference [mg/m3]
            
        Returns:
            float: Updated CO2 mass flow rate [mg/(m2.s)]
        """
        # Update input variables if provided
        if SC is not None:
            self.SC = SC
        if U_vents is not None:
            self.U_vents = U_vents
        if T_a is not None:
            self.T_a = T_a
        if T_b is not None:
            self.T_b = T_b
        if u is not None:
            self.u = u
        if dC is not None:
            self.dC = dC
            
        # Update ventilation rate calculator
        self.airExchangeRate.update(
            u=self.u,
            dT=self.T_a - self.T_b,
            U_roof=self.U_vents,
            SC=self.SC,
            T_a=self.T_a,
            T_b=self.T_b
        )
        
        # Calculate ventilation factor based on thermal screen and air zone
        if self.thermalScreen:
            if not self.topAir:
                self.f_vent = self.airExchangeRate.f_vent_air
            else:
                self.f_vent = self.airExchangeRate.f_vent_top
        else:
            self.f_vent = self.airExchangeRate.f_vent_air
            
        # Calculate CO2 mass flow
        self.MC_flow = self.f_vent * self.dC
        
        return self.MC_flow
