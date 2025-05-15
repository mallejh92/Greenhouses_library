class Control_1:
    """
    Controller for the CHP and heat pump and TES
    """
    
    def __init__(self):
        # Parameters
        self.T_max = 273.15 + 60  # Fill level of tank 1
        self.T_min = 273.15 + 50  # Lowest level of tank 1 and 2
        self.waitTime = 2  # Wait time, between operations
        self.Mdot_max = 38  # Maximum mass flow rate in the greenhouse heating circuit
        
        # Varying inputs
        self.T_high_tank = 90 + 273.15
        
        # State variables
        self.state = "All_off"  # Initial state
        self.time = 0
        
        # Output signals
        self.CHP = False
        self.ElectricalHeater = False
        self.HP = False
        
        # Hysteresis parameters
        self.hysteresis_low = self.T_min - 5
        self.hysteresis_high = self.T_max - 5
        self.hysteresis_state = False
        
    def update(self, T_tank: float, Mdot_1ry: float, T_low_TES: float, dt: float):
        """
        Update control system state and outputs
        
        Parameters:
            T_tank (float): Tank temperature [K]
            Mdot_1ry (float): Primary mass flow rate [kg/s]
            T_low_TES (float): Low temperature thermal energy storage [K]
            dt (float): Time step [s]
        """
        self.time += dt
        
        # Update hysteresis
        if T_tank > self.hysteresis_high:
            self.hysteresis_state = True
        elif T_tank < self.hysteresis_low:
            self.hysteresis_state = False
            
        # State machine logic
        if self.state == "All_off":
            # Transition T1 condition
            if ((T_tank < self.T_min and self.T_high_tank < self.T_max and Mdot_1ry > 0.1 * self.Mdot_max) or
                (T_tank < self.T_max - 10 and Mdot_1ry > self.Mdot_max)):
                self.state = "runCHP"
                
        elif self.state == "runCHP":
            # Transition T2 condition
            if (T_tank > self.T_max or Mdot_1ry <= 0.1 * self.Mdot_max or 
                self.T_high_tank > self.T_max):
                self.state = "All_off"
        
        # Update outputs
        self.CHP = self.state == "runCHP"
        self.ElectricalHeater = not self.hysteresis_state and self.time > 1e3
        self.HP = self.state == "runCHP" and T_low_TES < 333.15
        
        return self.CHP, self.ElectricalHeater, self.HP
