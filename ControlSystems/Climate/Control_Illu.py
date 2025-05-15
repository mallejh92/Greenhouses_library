class Control_Illu:
    """
    Controller for the artificial illumination
    """
    
    def __init__(self):
        # Parameters
        self.R_illu = 100  # W/m2
        
        # State variables
        self.E_acc = 0  # Accumulated PAR light (W.s/m2)
        self.E_acc_limit = 1.2 * 1000 * 3600  # 1.2 kWh/m2
        self.R_PAR_tot = 0  # Total PAR light
        self.R_PAR_day = 0  # Daily PAR light
        
        # State machine states
        self.state = "off"  # Initial state
        self.newDay_active = False
        self.sameDay_active = True
        
        # Timers
        self.timer = 0
        self.proving_timer = 0
        self.min_on_timer = 0
        
        # Output
        self.y = 0  # Control signal
        
    def update(self, h: float, R_t_PAR: float, dt: float):
        """
        Update control system state and outputs
        
        Parameters:
            h (float): Hour of the day
            R_t_PAR (float): Current PAR light
            dt (float): Time step [s]
        """
        # Update timers
        if self.newDay_active:
            self.timer += dt
        if self.state == "off_ProvingTime":
            self.proving_timer += dt
        if self.state == "on":
            self.min_on_timer += dt
            
        # State machine logic
        if self.state == "off":
            if (6 <= h <= 22 and self.E_acc < self.E_acc_limit and R_t_PAR < 40):
                self.state = "off_ProvingTime"
                self.proving_timer = 0
                
        elif self.state == "off_ProvingTime":
            if self.proving_timer >= 30 * 60:  # 30 minutes
                if R_t_PAR < 40:
                    self.state = "on"
                    self.min_on_timer = 0
                else:
                    self.state = "off"
                    
        elif self.state == "on":
            if self.min_on_timer >= 120 * 60:  # 2 hours
                if R_t_PAR > 120 or h > 22 or h < 6:
                    self.state = "off"
                    
        # New day logic
        if h <= 0 and self.sameDay_active:
            self.newDay_active = True
            self.sameDay_active = False
            
        if self.newDay_active and self.timer >= 3600:  # 1 hour
            self.newDay_active = False
            self.sameDay_active = True
            self.timer = 0
            
        # Update PAR calculations
        self.R_PAR_tot = R_t_PAR + (0.25 * self.R_illu if self.state == "on" else 0)
        self.R_PAR_day = self.R_PAR_tot if self.newDay_active else 0
        
        # Update accumulated energy
        self.E_acc += (self.R_PAR_tot - self.R_PAR_day) * dt / 86400
        
        # Update output
        self.y = 1 if self.state == "on" else 0
        
        return self.y
