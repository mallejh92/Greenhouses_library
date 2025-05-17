class CO2_Air:
    """
    CO2 mass balance of an air volume
    """
    
    def __init__(self, cap_CO2: float = 4.0, CO2_start: float = 1940.0, steadystate: bool = True):
        """
        Initialize CO2 air model
        
        Parameters:
            cap_CO2 (float): Capacity of the air to store CO2, equals the height of the air compartment [m]
            CO2_start (float): Initial CO2 concentration [mg/m3]
            steadystate (bool): If true, sets the derivative of CO2 to zero during initialization
        """
        # Parameters
        self.cap_CO2 = cap_CO2
        
        # Initialization parameters
        self.CO2_start = CO2_start
        self.steadystate = steadystate
        
        # State variables
        self.MC_flow = 0.0  # Mass flow rate [mg/(m2.s)]
        self.CO2 = CO2_start  # CO2 concentration [mg/m3]
        self.CO2_ppm = CO2_start / 1.94  # CO2 concentration in ppm
        
        # Port variables
        self.port_CO2 = CO2_start  # Port CO2 concentration
        
        # Initialize the system
        self.initialize()
        
    def initialize(self):
        """
        Initialize the system according to initial equations
        """
        # Set initial CO2 value
        self.CO2 = self.CO2_start
        
        # If in steady state, ensure MC_flow is zero
        if self.steadystate:
            self.MC_flow = 0.0
            
        # Update derived values
        self.CO2_ppm = self.CO2 / 1.94
        self.port_CO2 = self.CO2
        
    def step(self, dt: float):
        """
        Update CO2 concentration
        
        Parameters:
            dt (float): Time step [s]
        """
        # Update CO2 concentration
        if not self.steadystate:
            self.CO2 += (1.0 / self.cap_CO2) * self.MC_flow * dt
            
        # Update CO2 in ppm
        self.CO2_ppm = self.CO2 / 1.94
        
        # Update port CO2
        self.port_CO2 = self.CO2
        
        return self.CO2, self.CO2_ppm
