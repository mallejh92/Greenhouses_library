class Control_Illu:
    """
    Controller for the artificial illumination
    """
    
    def __init__(self, R_illu=100):
        """
        Initialize illumination controller
        
        Parameters:
        -----------
        R_illu : float, optional
            Illumination power [W/m2], default is 100
        """
        # Parameters
        self.R_illu = R_illu
        
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
        
        # Inputs
        self.h = 0.0  # Hour of the day
        self.R_t_PAR = 0.0  # Current PAR light
        
        # Output
        self.illu_signal = 0  # Control signal
        
    def compute(self):
        """
        Compute control signal based on current state and inputs
        
        Returns:
        --------
        float
            Illumination control signal (0 or 1)
        """
        # Update timers
        if self.newDay_active:
            self.timer += 1
        if self.state == "off_ProvingTime":
            self.proving_timer += 1
        if self.state == "on":
            self.min_on_timer += 1
            
        # State machine logic
        if self.state == "off":
            if (6 <= self.h <= 22 and self.E_acc < self.E_acc_limit and self.R_t_PAR < 40):
                self.state = "off_ProvingTime"
                self.proving_timer = 0
                
        elif self.state == "off_ProvingTime":
            if self.proving_timer >= 30 * 60:  # 30 minutes
                if self.R_t_PAR < 40:
                    self.state = "on"
                    self.min_on_timer = 0
                else:
                    self.state = "off"
                    
        elif self.state == "on":
            if self.min_on_timer >= 120 * 60:  # 2 hours
                if self.R_t_PAR > 120 or self.h > 22 or self.h < 6:
                    self.state = "off"
                    
        # New day logic
        if self.h <= 0 and self.sameDay_active:
            self.newDay_active = True
            self.sameDay_active = False
            
        if self.newDay_active and self.timer >= 3600:  # 1 hour
            self.newDay_active = False
            self.sameDay_active = True
            self.timer = 0
            
        # Update PAR calculations
        self.R_PAR_tot = self.R_t_PAR + (0.25 * self.R_illu if self.state == "on" else 0)
        self.R_PAR_day = self.R_PAR_tot if self.newDay_active else 0
        
        # Update accumulated energy
        self.E_acc += (self.R_PAR_tot - self.R_PAR_day) / 86400
        
        # Update output
        self.illu_signal = 1 if self.state == "on" else 0
        
        return self.illu_signal
