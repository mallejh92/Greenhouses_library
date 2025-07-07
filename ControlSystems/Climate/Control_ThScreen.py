class Control_ThScreen:
    """
    Modelica Control_ThScreen StateGraph 논리를 1:1로 반영한 보온 스크린 제어기
    (상태/전이 이름, 타이머, 조건 모두 Modelica와 동일하게 구현)
    """
    def __init__(self, R_Glob_can=0.0, R_Glob_can_min=32):
        # 입력 파라미터 (Modelica와 동일)
        self.R_Glob_can = R_Glob_can
        self.R_Glob_can_min = R_Glob_can_min
        # 상태 변수 (Modelica 상태 이름과 동일)
        self.state = "closed"  # InitialStep
        self.timer = 0.0       # opening_ColdDay, opening_WarmDay, closing_ColdDay, open용 타이머
        self.timer_crack = 0.0 # crack → crack2 전이용 타이머
        self.timer_closing_CD = 0.0 # closing_ColdDay용 타이머
        # 출력 신호 값
        self.SC_OCD_value = 0.98  # Opening Cold Day
        self.SC_OWD_value = 0.96  # Opening Warm Day
        self.SC_CCD_value = 0.98  # Closing Cold Day
        self.SC_crack_value = 0.98
        self.SC_crack2_value = 0.96
        # 출력 변수
        self.opening_CD = 0.0
        self.opening_WD = 0.0
        self.closing_CD = 0.0
        self.op = 0.0
        self.cl = 1.0
        self.crack = 0.0
        self.crack2 = 0.0
        self.SC = 1.0
        # 입력값 (외부에서 매 step마다 갱신)
        self.T_air_sp = 293.15  
        self.Tout = 273.15      # 변수명 통일: T_out → Tout
        self.RH_air = 0.0
        self.SC_usable = 0.0
        
    def step(self, dt: float) -> float:
        """
        Modelica StateGraph 논리 1:1 반영 (상태/전이 이름 동일)
        """
        prev_state = self.state
        
        # 1. 타이머 업데이트 (상태별)
        if self.state in ("opening_ColdDay", "opening_WarmDay", "open"):
            self.timer += dt
        else:
            self.timer = 0.0
        if self.state == "closing_ColdDay":
            self.timer_closing_CD += dt
        else:
            self.timer_closing_CD = 0.0
        # crack → crack2용 타이머 (T9)
        if self.state == "crack" and self.RH_air > 0.85:
            self.timer_crack += dt
        else:
            self.timer_crack = 0.0
            
        # 2. 상태 전이 (Modelica Transition 이름 주석)
        # closed (InitialStep)
        if self.state == "closed":
            # T5: closed → crack (RH_air > 0.83)
            if self.RH_air > 0.83:
                self.state = "crack"
            # T2: closed → opening_ColdDay (R_Glob_can > min, T_out <= T_air_sp-7)
            elif self.R_Glob_can > self.R_Glob_can_min and self.Tout <= (self.T_air_sp - 7):
                self.state = "opening_ColdDay"
            # T3: closed → opening_WarmDay (R_Glob_can > min, T_out > T_air_sp-7)
            elif self.R_Glob_can > self.R_Glob_can_min and self.Tout > (self.T_air_sp - 7):
                self.state = "opening_WarmDay"
            # T4: closed → closing_ColdDay (SC_usable > 0, T_out < T_air_sp-7, enableTimer, waitTime=2h)
            elif self.SC_usable > 0 and self.Tout < (self.T_air_sp - 7):
                if self.timer >= 2 * 3600:
                    self.state = "closing_ColdDay"
                    
        # opening_ColdDay
        elif self.state == "opening_ColdDay":
            # T6: opening_ColdDay → open (timer >= 52min)
            if self.timer >= 52 * 60:
                self.state = "open"
            # T2b: opening_ColdDay → opening_ColdDay (R_Glob_can > min, T_out <= T_air_sp-7)
            # (유지)
            # T3b: opening_ColdDay → opening_WarmDay (R_Glob_can > min, T_out > T_air_sp-7)
            elif self.R_Glob_can > self.R_Glob_can_min and self.Tout > (self.T_air_sp - 7):
                self.state = "opening_WarmDay"
            # T8: opening_ColdDay → closed (RH_air < 0.7)
            elif self.RH_air < 0.7:
                self.state = "closed"
                
        # opening_WarmDay
        elif self.state == "opening_WarmDay":
            # T7: opening_WarmDay → open (timer >= 32min)
            if self.timer >= 32 * 60:
                self.state = "open"
            # T2c: opening_WarmDay → opening_ColdDay (R_Glob_can > min, T_out <= T_air_sp-7)
            elif self.R_Glob_can > self.R_Glob_can_min and self.Tout <= (self.T_air_sp - 7):
                self.state = "opening_ColdDay"
            # T8: opening_WarmDay → closed (RH_air < 0.7)
            elif self.RH_air < 0.7:
                self.state = "closed"
                
        # open
        elif self.state == "open":
            # T4: open → closing_ColdDay (SC_usable > 0, T_out < T_air_sp-7, enableTimer, waitTime=2h)
            if self.SC_usable > 0 and self.Tout < (self.T_air_sp - 7):
                if self.timer >= 2 * 3600:
                    self.state = "closing_ColdDay"
            # T2: open → opening_ColdDay (R_Glob_can > min, T_out <= T_air_sp-7)
            elif self.R_Glob_can > self.R_Glob_can_min and self.Tout <= (self.T_air_sp - 7):
                self.state = "opening_ColdDay"
            # T3: open → opening_WarmDay (R_Glob_can > min, T_out > T_air_sp-7)
            elif self.R_Glob_can > self.R_Glob_can_min and self.Tout > (self.T_air_sp - 7):
                self.state = "opening_WarmDay"
                
        # closing_ColdDay
        elif self.state == "closing_ColdDay":
            # T1: closing_ColdDay → closed (timer >= 52min)
            if self.timer_closing_CD >= 52 * 60:
                self.state = "closed"
                
        # crack
        elif self.state == "crack":
            # T8: crack → closed (RH_air < 0.7)
            if self.RH_air < 0.7:
                self.state = "closed"
            # T9: crack → crack2 (RH_air > 0.85, timer_crack >= 15min)
            elif self.RH_air > 0.85 and self.timer_crack >= 15 * 60:
                self.state = "crack2"
            # T2b: crack → opening_ColdDay (R_Glob_can > min, T_out <= T_air_sp-7)
            elif self.R_Glob_can > self.R_Glob_can_min and self.Tout <= (self.T_air_sp - 7):
                self.state = "opening_ColdDay"
            # T3b: crack → opening_WarmDay (R_Glob_can > min, T_out > T_air_sp-7)
            elif self.R_Glob_can > self.R_Glob_can_min and self.Tout > (self.T_air_sp - 7):
                self.state = "opening_WarmDay"
                
        # crack2
        elif self.state == "crack2":
            # T8b: crack2 → closed (RH_air < 0.7)
            if self.RH_air < 0.7:
                self.state = "closed"
            # T2c: crack2 → opening_ColdDay (R_Glob_can > min, T_out <= T_air_sp-7)
            elif self.R_Glob_can > self.R_Glob_can_min and self.Tout <= (self.T_air_sp - 7):
                self.state = "opening_ColdDay"
            # T3c: crack2 → opening_WarmDay (R_Glob_can > min, T_out > T_air_sp-7)
            elif self.R_Glob_can > self.R_Glob_can_min and self.Tout > (self.T_air_sp - 7):
                self.state = "opening_WarmDay"
                
        # 상태가 바뀌면 타이머 리셋
        if self.state != prev_state:
            self.timer = 0.0
            self.timer_crack = 0.0
            self.timer_closing_CD = 0.0
            
        # 3. 출력 신호 계산 (Modelica와 동일)
        self.opening_CD = self.SC_OCD_value if self.state == "opening_ColdDay" else 0.0
        self.opening_WD = self.SC_OWD_value if self.state == "opening_WarmDay" else 0.0
        self.closing_CD = self.SC_CCD_value if self.state == "closing_ColdDay" else 0.0
        self.op = 0.0 if self.state == "open" else 0.0
        self.cl = 1.0 if self.state == "closed" else 0.0
        self.crack = self.SC_crack_value if self.state == "crack" else 0.0
        self.crack2 = self.SC_crack2_value if self.state == "crack2" else 0.0
        self.SC = (self.opening_CD + self.opening_WD + self.closing_CD + self.op + self.cl + self.crack + self.crack2)
        
        if self.SC_usable == 0:
            self.state = "open"
            self.SC = 0.0
            return self.SC
            
        return self.SC
