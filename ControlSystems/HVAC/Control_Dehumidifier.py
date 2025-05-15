from ControlSystems.PID import PID, PIDParameters

class Control_Dehumidifier:
    """
    Controller for the dehumidifier with state machine and PID control
    """
    
    def __init__(self):
        # Parameters
        self.T_max = 273.15 + 60  # Fill level of tank 1
        self.T_min = 273.15 + 50  # Lowest level of tank 1 and 2
        self.waitTime = 2  # Wait time, between operations
        
        # State variables
        self.state = "All_off"  # Initial state
        self.time = 0
        
        # Output signals
        self.Dehum = False
        self.CS = 0.5  # Control signal
        
        # PID controller for humidity control
        pid_params = PIDParameters(
            Kp=-0.9,
            Ti=100,
            Td=0,
            CSstart=0.5,
            steadyStateInit=False,
            CSmin=0,
            PVmin=0,
            PVmax=1,
            CSmax=1,
            PVstart=0.85
        )
        self.PID_HR = PID(pid_params)
        
        # Humidity setpoint
        self.RH_setpoint = 0.85
        
    def update(self, T_air: float, air_RH: float, T_air_sp: float, dt: float):
        """
        Update control system state and outputs
        
        Parameters:
            T_air (float): Air temperature [K]
            air_RH (float): Air relative humidity [0-1]
            T_air_sp (float): Air temperature setpoint [K]
            dt (float): Time step [s]
        """
        self.time += dt
        
        # State machine logic
        if self.state == "All_off":
            # Transition T1 condition
            if T_air < 293.15:  # 20°C
                self.state = "runDehum"
                
        elif self.state == "runDehum":
            # Transition T2 condition
            if T_air > 295.15:  # 22°C
                self.state = "All_off"
        
        # Update outputs
        self.Dehum = self.state == "runDehum"
        
        # Update PID controller for humidity control
        if self.Dehum:
            self.CS = self.PID_HR.update(air_RH, self.RH_setpoint, dt)
        else:
            self.CS = 0.5  # Default control signal when dehumidifier is off
        
        return self.Dehum, self.CS
