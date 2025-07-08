from ControlSystems.PID import PID

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
        
        # 히스테리시스 파라미터 추가 (진동 방지)
        self.radiation_hysteresis = 10.0  # 일사량 히스테리시스 [W/m²] - 증가
        self.temperature_hysteresis = 2.0  # 온도 히스테리시스 [K] - 증가
        self.last_state_change_time = 0.0  # 마지막 상태 변경 시간
        self.min_state_duration = 900.0  # 최소 상태 유지 시간 [s] (15분으로 증가)
        
        # Screen values
        self.SC_OCD_value = 0.98  # Opening Cold Day value
        self.SC_OWD_value = 0.96  # Opening Warm Day value
        self.SC_CCD_value = 0.98  # Closing Cold Day value
        
        # PID controllers
        pid_humidity_params = PID(
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
        
        pid_temp_params = PID(
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
        
    def step(self, T_out: float, T_air: float, T_air_sp: float, 
             R_Glob_can: float, RH_air: float, SC_usable: float, dt: float) -> float:
        """
        Update control system state and outputs
        
        Parameters:
        -----------
        T_out : float
            Outside temperature [K]
        T_air : float
            Air temperature [K]
        T_air_sp : float
            Air temperature setpoint [K]
        R_Glob_can : float
            Global radiation at canopy level [W/m2]
        RH_air : float
            Air relative humidity [0-1]
        SC_usable : float
            Screen usability
        dt : float
            Time step [s]
            
        Returns:
        --------
        float
            Screen control signal (0-1)
        """
        # 현재 시간 업데이트
        current_time = getattr(self, 'current_time', 0.0) + dt
        self.current_time = current_time
        
        # Update timer
        if self.state in ["opening_ColdDay", "opening_WarmDay", "closing_ColdDay"]:
            self.timer += dt
        
        # 최소 상태 유지 시간 체크
        time_since_last_change = current_time - self.last_state_change_time
        can_change_state = time_since_last_change >= self.min_state_duration
            
        # Update PID controllers
        self.PID_crack.step(dt)
        self.PID_crack_T.step(dt)
        
        # 히스테리시스가 적용된 조건 계산
        if self.state == "closed":
            # 닫힌 상태에서 열리려면 더 높은 임계값 필요
            radiation_threshold = self.R_Glob_can_min + self.radiation_hysteresis
            temp_threshold = T_air_sp - 7 + self.temperature_hysteresis
        else:
            # 열린 상태에서 닫히려면 더 낮은 임계값 필요
            radiation_threshold = self.R_Glob_can_min - self.radiation_hysteresis
            temp_threshold = T_air_sp - 7 - self.temperature_hysteresis
        
        # State machine logic with hysteresis and minimum duration
        old_state = self.state
        
        if self.state == "closed" and can_change_state:
            if R_Glob_can > radiation_threshold and T_out <= temp_threshold:
                self.state = "opening_ColdDay"
                self.timer = 0
            elif R_Glob_can > radiation_threshold and T_out > temp_threshold:
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
                
        elif self.state == "open" and can_change_state:
            # 열린 상태에서는 더 낮은 임계값으로 상태 변경
            if R_Glob_can < radiation_threshold:  # 일사량이 충분히 낮아져야 함
                pass  # 상태 유지
            elif T_out <= temp_threshold:
                self.state = "opening_ColdDay"
            elif T_out > temp_threshold:
                self.state = "opening_WarmDay"
        
        # 상태가 변경되었으면 시간 기록
        if old_state != self.state:
            self.last_state_change_time = current_time
        
        # Update screen values
        self.opening_CD = self.SC_OCD_value if self.state == "opening_ColdDay" else 0
        self.opening_WD = self.SC_OWD_value if self.state == "opening_WarmDay" else 0
        self.closing_CD = self.SC_CCD_value if self.state == "closing_ColdDay" else 0
        self.op = 0 if self.state == "open" else 0
        self.cl = 1 if self.state == "closed" else 0
        
        # Calculate final control signal with smoother transitions
        # PID 제어 신호에 저역 통과 필터 적용 (급격한 변화 방지)
        pid_output = min(self.PID_crack.CS, self.PID_crack_T.CS)
        
        self.y = (self.opening_CD + self.opening_WD + self.closing_CD + 
                 self.op + self.cl * pid_output)
        
        return self.y
