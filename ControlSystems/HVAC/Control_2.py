class Control_2:
    """
    Controller for the CHP and heat pump and TES with modified conditions
    """
    
    def __init__(self):
        # Parameters
        self.T_max = 273.15 + 60  # Fill level of tank 1
        self.T_min = 273.15 + 50  # Lowest level of tank 1 and 2
        self.waitTime = 2  # Wait time, between operations
        self.Mdot_max = 38  # Maximum mass flow rate in the greenhouse heating circuit
        
        # Varying inputs
        self.Mdot_1ry = 30  # Primary mass flow rate
        
        # State variables
        self.state = "All_off"  # Initial state
        self.time = 0
        self.transition_timer = 0  # Timer for T2 transition
        
        # Output signals
        self.CHP = False
        self.ElectricalHeater = False
        self.HP = False
        
        # Hysteresis parameters
        self.hysteresis_low = self.T_min - 5
        self.hysteresis_high = self.T_max - 5
        self.hysteresis_state = False
        
    def step(self, T_tank: float, T_low_TES: float, T_su_hx: float, dt: float):
        """
        Step control system state and outputs
        
        Parameters:
            T_tank (float): Tank temperature [K]
            T_low_TES (float): Low temperature thermal energy storage [K]
            T_su_hx (float): Supply heat exchanger temperature [K]
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
            if (T_tank < self.T_min and T_su_hx < 363.15 and 
                self.Mdot_1ry > 0.1 * self.Mdot_max):
                self.state = "runCHP"
                self.transition_timer = 0
                
        elif self.state == "runCHP":
            # Update transition timer
            self.transition_timer += dt
            
            # Transition T2 condition with timer
            if (self.transition_timer >= 60 and  # 60 seconds wait time
                (T_tank > self.T_max or 
                 T_su_hx > (90 + 273.15) or 
                 self.Mdot_1ry < 0.1 * self.Mdot_max)):
                self.state = "All_off"
        
        # Update outputs
        self.CHP = self.state == "runCHP"
        self.ElectricalHeater = not self.hysteresis_state and self.time > 1e3
        self.HP = self.state == "runCHP" and T_low_TES < 333.15
        
        return self.CHP, self.ElectricalHeater, self.HP
