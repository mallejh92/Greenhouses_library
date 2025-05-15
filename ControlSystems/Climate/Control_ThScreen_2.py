from ControlSystems.PID import PID, PIDParameters

class Control_ThScreen_2:
    """
    Controller for the thermal screen closure and crack for humidity and temperature
    """
    
    def __init__(self):
        # Parameters
        self.R_Glob_can_min = 32  # Minimum global radiation
        
        # State variables
        self.state = "closed"  # Initial state
        self.timer = 0
        
        # Screen values
        self.SC_OCD_value = 0.98  # Opening Cold Day value
        self.SC_OWD_value = 0.96  # Opening Warm Day value
        self.SC_CCD_value = 0.98  # Closing Cold Day value
        
        # PID controllers
        pid_humidity_params = PIDParameters(
            Kp=0.5,
            Ti=600,
            Td=0,
            CSstart=0.5,
            steadyStateInit=False,
            CSmin=0.96,
            PVmin=0.4,
            PVmax=1,
            CSmax=1,
            PVstart=0.5
        )
        self.PID_crack = PID(pid_humidity_params)
        
        pid_temp_params = PIDParameters(
            Kp=0.5,
            Ti=600,
            Td=0,
            CSstart=0.5,
            steadyStateInit=False,
            CSmin=0.98,
            PVmin=12,
            PVmax=28,
            CSmax=1,
            PVstart=0.5
        )
        self.PID_crack_T = PID(pid_temp_params)
        
        # Setpoints
        self.RH_air_SP = 0.85
        self.T_out_sp = 12 + 273.15  # Initial value
        
        # Output signals
        self.opening_CD = 0
        self.opening_WD = 0
        self.closing_CD = 0
        self.op = 0
        self.cl = 1
        self.y = 0
        
    def update(self, T_out: float, T_air: float, T_air_sp: float, 
              R_Glob_can: float, RH_air: float, SC_usable: float, dt: float):
        """
        Update control system state and outputs
        
        Parameters:
            T_out (float): Outside temperature [K]
            T_air (float): Air temperature [K]
            T_air_sp (float): Air temperature setpoint [K]
            R_Glob_can (float): Global radiation at canopy level [W/m2]
            RH_air (float): Air relative humidity [0-1]
            SC_usable (float): Screen usability
            dt (float): Time step [s]
        """
        # Update timer
        if self.state in ["opening_ColdDay", "opening_WarmDay", "closing_ColdDay"]:
            self.timer += dt
            
        # Update PID controllers
        self.PID_crack.update(RH_air, self.RH_air_SP, dt)
        self.PID_crack_T.update(T_air, T_air_sp + 1.5, dt)
        
        # State machine logic
        if self.state == "closed":
            if R_Glob_can > self.R_Glob_can_min and T_out <= (T_air_sp - 7):
                self.state = "opening_ColdDay"
                self.timer = 0
            elif R_Glob_can > self.R_Glob_can_min and T_out > (T_air_sp - 7):
                self.state = "opening_WarmDay"
                self.timer = 0
            elif SC_usable > 0 and T_out < self.T_out_sp:
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
                
        elif self.state == "open":
            if R_Glob_can > self.R_Glob_can_min and T_out <= (T_air_sp - 7):
                self.state = "opening_ColdDay"
            elif R_Glob_can > self.R_Glob_can_min and T_out > (T_air_sp - 7):
                self.state = "opening_WarmDay"
        
        # Update screen values
        self.opening_CD = self.SC_OCD_value if self.state == "opening_ColdDay" else 0
        self.opening_WD = self.SC_OWD_value if self.state == "opening_WarmDay" else 0
        self.closing_CD = self.SC_CCD_value if self.state == "closing_ColdDay" else 0
        self.op = 0 if self.state == "open" else 0
        self.cl = 1 if self.state == "closed" else 0
        
        # Calculate final control signal
        self.y = (self.opening_CD + self.opening_WD + self.closing_CD + 
                 self.op + self.cl * min(self.PID_crack.CS, self.PID_crack_T.CS))
        
        return self.y
