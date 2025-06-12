class Control_ThScreen:
    """
    Controller for the thermal screen closure including a crack for dehumidification
    """
    
    def __init__(self, R_Glob_can=0.0, R_Glob_can_min=32):
        """
        Initialize thermal screen controller
        
        Parameters:
        -----------
        R_Glob_can : float, optional
            Global radiation at canopy level [W/m2], default is 0.0
        R_Glob_can_min : float, optional
            Minimum global radiation [W/m2], default is 32
        """
        # Parameters
        self.R_Glob_can = R_Glob_can
        self.R_Glob_can_min = R_Glob_can_min
        
        # State variables
        self.state = "closed"  # Initial state
        self.timer = 0
        
        # Screen values
        self.SC_OCD_value = 0.98  # Opening Cold Day value
        self.SC_OWD_value = 0.96  # Opening Warm Day value
        self.SC_CCD_value = 0.98  # Closing Cold Day value
        self.SC_crack_value = 0.98  # Crack value
        self.SC_crack2_value = 0.96  # Second crack value
        
        # Output signals
        self.opening_CD = 0
        self.opening_WD = 0
        self.closing_CD = 0
        self.op = 0
        self.cl = 1
        self.crack = 0
        self.crack2 = 0
        self.SC = 0  # Final control signal
        
        # Additional inputs
        self.T_air_sp = 293.15  # Default air temperature setpoint [K]
        self.T_out = 273.15    # Default outside temperature [K]
        self.RH_air = 0.0      # Default relative humidity [0-1]
        self.SC_usable = 0.0   # Default screen usability
        
    def step(self, dt: float) -> float:
        """
        Update control signal based on current state and inputs
        
        Parameters:
        -----------
        dt : float
            Time step [s]
            
        Returns:
        --------
        float
            Screen control signal (0-1)
        """
        # Increment timer for states with timed transitions
        if self.state in ("opening_ColdDay", "opening_WarmDay", "closing_ColdDay"):
            self.timer += dt
        else:
            self.timer = 0

        # Separate timer for crack -> crack2 transition
        if not hasattr(self, "crack_timer"):
            self.crack_timer = 0.0

        # State machine logic
        if self.state == "closed":
            if self.RH_air > 0.83:
                self.state = "crack"
                self.crack_timer = 0
            elif self.R_Glob_can > self.R_Glob_can_min and self.T_out <= (self.T_air_sp - 7):
                self.state = "opening_ColdDay"
                self.timer = 0
            elif self.R_Glob_can > self.R_Glob_can_min and self.T_out > (self.T_air_sp - 7):
                self.state = "opening_WarmDay"
                self.timer = 0
            elif self.SC_usable > 0 and self.T_out < (self.T_air_sp - 7):
                self.state = "closing_ColdDay"
                self.timer = 0
                
        elif self.state == "opening_ColdDay":
            if self.timer >= 52 * 60:  # 52 minutes
                self.state = "open"
                
        elif self.state == "opening_WarmDay":
            if self.timer >= 32 * 60:  # 32 minutes
                self.state = "open"
                
        elif self.state == "closing_ColdDay":
            if self.timer >= 52 * 60:  # 52 minutes
                self.state = "closed"
                
        elif self.state == "crack":
            if self.RH_air < 0.7:
                self.state = "closed"
                self.crack_timer = 0
            elif self.RH_air > 0.85:
                self.state = "crack2"
                self.crack_timer += dt
                if self.crack_timer >= 15 * 60:
                    self.state = "crack2"
                    self.crack_timer = 0
            else:
                self.crack_timer = 0
                
        elif self.state == "crack2":
            if self.RH_air < 0.7:
                self.state = "closed"
            elif self.R_Glob_can > self.R_Glob_can_min and self.T_out <= (self.T_air_sp - 7):
                self.state = "opening_ColdDay"
                self.timer = 0
            elif self.R_Glob_can > self.R_Glob_can_min and self.T_out > (self.T_air_sp - 7):
                self.state = "opening_WarmDay"
                self.timer = 0
                
        elif self.state == "open":
            if self.R_Glob_can > self.R_Glob_can_min and self.T_out <= (self.T_air_sp - 7):
                self.state = "opening_ColdDay"
                self.timer = 0
            elif self.R_Glob_can > self.R_Glob_can_min and self.T_out > (self.T_air_sp - 7):
                self.state = "opening_WarmDay"
                self.timer = 0
            elif self.SC_usable > 0 and self.T_out < (self.T_air_sp - 7):
                self.timer += dt
                if self.timer >= 2 * 3600:  # 2 hours
                    self.state = "closing_ColdDay"
                    self.timer = 0
            else:
                self.timer = 0
        
        # Update screen values
        self.opening_CD = self.SC_OCD_value if self.state == "opening_ColdDay" else 0
        self.opening_WD = self.SC_OWD_value if self.state == "opening_WarmDay" else 0
        self.closing_CD = self.SC_CCD_value if self.state == "closing_ColdDay" else 0
        self.op = 0 if self.state == "open" else 0
        self.cl = 1 if self.state == "closed" else 0
        self.crack = self.SC_crack_value if self.state == "crack" else 0
        self.crack2 = self.SC_crack2_value if self.state == "crack2" else 0
        
        # Calculate final control signal
        self.SC = (self.opening_CD + self.opening_WD + self.closing_CD + 
                  self.op + self.cl + self.crack + self.crack2)
        
        return self.SC
