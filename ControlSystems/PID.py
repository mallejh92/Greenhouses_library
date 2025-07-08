import numpy as np

class PID:
    """
    ISA PID controller with anti-windup
    """
    
    def __init__(self, Kp, Ti, Td=0, Nd=1, Ni=1, b=1, c=0,
                 PVmin=0, PVmax=1, CSmin=0, CSmax=1,
                 PVstart=0.5, CSstart=0.5, steadyStateInit=False):
        """
        Initialize PID controller
        
        Parameters:
        -----------
        Kp : float
            Proportional gain (normalised units)
        Ti : float
            Integral time
        Td : float, optional
            Derivative time, default is 0
        Nd : float, optional
            Derivative action up to Nd / Td rad/s, default is 1
        Ni : float, optional
            Ni*Ti is the time constant of anti-windup compensation, default is 1
        b : float, optional
            Setpoint weight on proportional action, default is 1
        c : float, optional
            Setpoint weight on derivative action, default is 0
        PVmin : float, optional
            Minimum value of process variable for scaling, default is 0
        PVmax : float, optional
            Maximum value of process variable for scaling, default is 1
        CSmin : float, optional
            Minimum value of control signal for scaling, default is 0
        CSmax : float, optional
            Maximum value of control signal for scaling, default is 1
        PVstart : float, optional
            Start value of PV (scaled), default is 0.5
        CSstart : float, optional
            Start value of CS (scaled), default is 0.5
        steadyStateInit : bool, optional
            Whether to initialize in steady state, default is False
        """
        # Store parameters
        self.Kp = Kp
        self.Ti = Ti
        self.Td = Td
        self.Nd = Nd
        self.Ni = Ni
        self.b = b
        self.c = c
        self.PVmin = PVmin
        self.PVmax = PVmax
        self.CSmin = CSmin
        self.CSmax = CSmax
        self.PVstart = PVstart
        self.CSstart = CSstart
        self.steadyStateInit = steadyStateInit
        
        # 출력 변화율 제한 파라미터 추가 (진동 방지)
        self.max_output_rate = 0.05  # 최대 출력 변화율 [1/s] (5%/초로 감소)
        self.last_CS = CSstart  # 이전 제어 신호
        
        # Initialize state variables
        self.I = CSstart / Kp  # Integral action / Kp
        self.Dx = c * PVstart - PVstart  # State of approximated derivator
        self.CSs = CSstart  # Control signal scaled in per unit
        self.CSbs = CSstart  # Control signal scaled in per unit before saturation
        
        # Time step for numerical integration
        self.dt = 1  # Default time step
        
        # Process variable and setpoint
        self.PV = PVstart
        self.SP = PVstart
        
        self.CS = self.CSstart  # 실제 제어 신호 (초기값)
        
    def step(self, dt: float) -> float:
        """
        PID 제어 신호를 계산합니다.
        
        Parameters:
        -----------
        dt : float
            시간 간격 [s]
            
        Returns:
        --------
        float
            제어 신호
        """
        # Scaling
        SPs = (self.SP - self.PVmin) / (self.PVmax - self.PVmin)
        PVs = (self.PV - self.PVmin) / (self.PVmax - self.PVmin)
        
        # Controller actions
        P = self.b * SPs - PVs  # Proportional action / Kp
        
        # Integral action
        if self.Ti > 0:
            track = (self.CSs - self.CSbs) / (self.Kp * self.Ni)
            dI = (SPs - PVs + track) / self.Ti
            self.I += dI * dt
            
            # Overflow 방지: 적분값 즉시 제한
            max_I = 1e6
            min_I = -1e6
            self.I = np.clip(self.I, min_I, max_I)
        else:
            self.I = 0
            
        # Derivative action
        if self.Td > 0:
            # State equation of approximated derivator
            dDx = (self.Nd / self.Td) * ((self.c * SPs - PVs) - self.Dx)
            self.Dx += dDx * dt
            # Output equation of approximated derivator
            D = self.Nd * ((self.c * SPs - PVs) - self.Dx)
        else:
            self.Dx = 0
            D = 0
            
        # Calculate control signal
        self.CSbs = self.Kp * (P + self.I + D)  # Control signal before saturation
        self.CSs = np.clip(self.CSbs, 0, 1)  # Saturated control signal
        
        # Convert to actual control signal
        raw_CS = self.CSmin + self.CSs * (self.CSmax - self.CSmin)
        
        # 출력 변화율 제한 적용 (급격한 변화 방지)
        max_change = self.max_output_rate * dt * (self.CSmax - self.CSmin)
        CS_change = raw_CS - self.last_CS
        
        if abs(CS_change) > max_change:
            # 변화량이 제한을 초과하면 제한된 변화량 적용
            if CS_change > 0:
                self.CS = self.last_CS + max_change
            else:
                self.CS = self.last_CS - max_change
        else:
            # 변화량이 제한 내에 있으면 그대로 적용
            self.CS = raw_CS
        
        # 이전 제어 신호 업데이트
        self.last_CS = self.CS
        
        max_I = 1e6
        min_I = -1e6
        self.I = np.clip(self.I, min_I, max_I)
        
        return self.CS
