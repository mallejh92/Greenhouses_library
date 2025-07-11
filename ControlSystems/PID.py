# import numpy as np

# class PID:
#     """
#     ISA PID controller with anti-windup
#     """
    
#     def __init__(self, Kp, Ti, Td=0, Nd=1, Ni=1, b=1, c=0,
#                  PVmin=0, PVmax=1, CSmin=0, CSmax=1,
#                  PVstart=0.5, CSstart=0.5, steadyStateInit=False):
#         """
#         Initialize PID controller
        
#         Parameters:
#         -----------
#         Kp : float
#             Proportional gain (normalised units)
#         Ti : float
#             Integral time
#         Td : float, optional
#             Derivative time, default is 0
#         Nd : float, optional
#             Derivative action up to Nd / Td rad/s, default is 1
#         Ni : float, optional
#             Ni*Ti is the time constant of anti-windup compensation, default is 1
#         b : float, optional
#             Setpoint weight on proportional action, default is 1
#         c : float, optional
#             Setpoint weight on derivative action, default is 0
#         PVmin : float, optional
#             Minimum value of process variable for scaling, default is 0
#         PVmax : float, optional
#             Maximum value of process variable for scaling, default is 1
#         CSmin : float, optional
#             Minimum value of control signal for scaling, default is 0
#         CSmax : float, optional
#             Maximum value of control signal for scaling, default is 1
#         PVstart : float, optional
#             Start value of PV (scaled), default is 0.5
#         CSstart : float, optional
#             Start value of CS (scaled), default is 0.5
#         steadyStateInit : bool, optional
#             Whether to initialize in steady state, default is False
#         """
#         # Store parameters
#         self.Kp = Kp
#         self.Ti = Ti
#         self.Td = Td
#         self.Nd = Nd
#         self.Ni = Ni
#         self.b = b
#         self.c = c
#         self.PVmin = PVmin
#         self.PVmax = PVmax
#         self.CSmin = CSmin
#         self.CSmax = CSmax
#         self.PVstart = PVstart
#         self.CSstart = CSstart
#         self.steadyStateInit = steadyStateInit
        
#         # 출력 변화율 제한 파라미터 추가 (진동 방지)
#         self.max_output_rate = 0.05  # 최대 출력 변화율 [1/s] (5%/초로 감소)
#         self.last_CS = CSstart  # 이전 제어 신호
        
#         # Initialize state variables
#         self.I = CSstart / Kp  # Integral action / Kp
#         self.Dx = c * PVstart - PVstart  # State of approximated derivator
#         self.CSs = CSstart  # Control signal scaled in per unit
#         self.CSbs = CSstart  # Control signal scaled in per unit before saturation
        
#         # Time step for numerical integration
#         self.dt = 1  # Default time step
        
#         # Process variable and setpoint
#         self.PV = PVstart
#         self.SP = PVstart
        
#         self.CS = self.CSstart  # 실제 제어 신호 (초기값)
        
#     def step(self, dt: float) -> float:
#         """
#         PID 제어 신호를 계산합니다.
        
#         Parameters:
#         -----------
#         dt : float
#             시간 간격 [s]
            
#         Returns:
#         --------
#         float
#             제어 신호
#         """
#         # Scaling
#         SPs = (self.SP - self.PVmin) / (self.PVmax - self.PVmin)
#         PVs = (self.PV - self.PVmin) / (self.PVmax - self.PVmin)
        
#         # Controller actions
#         P = self.b * SPs - PVs  # Proportional action / Kp
        
#         # Integral action
#         if self.Ti > 0:
#             track = (self.CSs - self.CSbs) / (self.Kp * self.Ni)
#             dI = (SPs - PVs + track) / self.Ti
#             self.I += dI * dt
            
#             # Overflow 방지: 적분값 즉시 제한
#             max_I = 1e6
#             min_I = -1e6
#             self.I = np.clip(self.I, min_I, max_I)
#         else:
#             self.I = 0
            
#         # Derivative action
#         if self.Td > 0:
#             # State equation of approximated derivator
#             dDx = (self.Nd / self.Td) * ((self.c * SPs - PVs) - self.Dx)
#             self.Dx += dDx * dt
#             # Output equation of approximated derivator
#             D = self.Nd * ((self.c * SPs - PVs) - self.Dx)
#         else:
#             self.Dx = 0
#             D = 0
            
#         # Calculate control signal
#         self.CSbs = self.Kp * (P + self.I + D)  # Control signal before saturation
#         self.CSs = np.clip(self.CSbs, 0, 1)  # Saturated control signal
        
#         # Convert to actual control signal
#         raw_CS = self.CSmin + self.CSs * (self.CSmax - self.CSmin)
        
#         # 출력 변화율 제한 적용 (급격한 변화 방지)
#         max_change = self.max_output_rate * dt * (self.CSmax - self.CSmin)
#         CS_change = raw_CS - self.last_CS
        
#         if abs(CS_change) > max_change:
#             # 변화량이 제한을 초과하면 제한된 변화량 적용
#             if CS_change > 0:
#                 self.CS = self.last_CS + max_change
#             else:
#                 self.CS = self.last_CS - max_change
#         else:
#             # 변화량이 제한 내에 있으면 그대로 적용
#             self.CS = raw_CS
        
#         # 이전 제어 신호 업데이트
#         self.last_CS = self.CS
        
#         max_I = 1e6
#         min_I = -1e6
#         self.I = np.clip(self.I, min_I, max_I)
        
#         return self.CS
import numpy as np
from scipy.integrate import solve_ivp

class PID:
    """
    Modelica의 ISA PID 컨트롤러를 Python으로 구현한 클래스.
    - scipy.integrate.solve_ivp를 사용하여 ODE 시스템 해석
    """
    def __init__(self, Kp, Ti, Td=0, Nd=1, Ni=1, b=1, c=0,
                 PVmin=0, PVmax=1, CSmin=0, CSmax=1,
                 PVstart=0.5, CSstart=0.5, steadyStateInit=False):
        # 파라미터 저장 (이전과 동일)
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
        self.steadyStateInit = steadyStateInit

        # 상태 변수 벡터 [I, Dx]
        initial_I = CSstart / Kp if Kp != 0 else 0
        initial_Dx = c * PVstart - PVstart
        self.y = np.array([initial_I, initial_Dx])

        # 현재값(PV), 목표값(SP), 제어신호(CS)
        self.PV = PVstart * (PVmax - PVmin) + PVmin
        self.SP = PVstart * (PVmax - PVmin) + PVmin
        self.CS = CSmin + CSstart * (CSmax - CSmin)
        
        # 안티 와인드업을 위한 내부 변수
        self.track = 0.0

    def _system_dynamics(self, t, y, SPs, PVs):
        """
        solve_ivp가 호출할 ODE 시스템 정의 함수
        y[0] = I (적분 항)
        y[1] = Dx (미분 상태 변수)
        """
        I_current, Dx_current = y

        # der(I) 계산
        if self.Ti > 0:
            dI_dt = (SPs - PVs + self.track) / self.Ti
        else:
            dI_dt = 0

        # der(Dx) 계산
        if self.Td > 0:
            dDx_dt = (self.Nd / self.Td) * ((self.c * SPs - PVs) - Dx_current)
        else:
            dDx_dt = 0
            
        return [dI_dt, dDx_dt]

    def step(self, dt: float) -> float:
        """한 타임스텝(dt)마다 제어 신호를 계산합니다."""
        
        # --- 1. 스케일링 ---
        SPs = (self.SP - self.PVmin) / (self.PVmax - self.PVmin)
        PVs = (self.PV - self.PVmin) / (self.PVmax - self.PVmin)

        # --- 2. ODE 풀이 (solve_ivp 사용) ---
        # t_span: 현재 시간(0)부터 다음 스텝(dt)까지
        # y0: 현재 상태 변수 값
        sol = solve_ivp(
            fun=self._system_dynamics,
            t_span=[0, dt],
            y0=self.y,
            method='RK45',  # 기본 룬게-쿤타 계열 솔버
            args=(SPs, PVs)
        )
        
        # 다음 스텝의 상태 변수 값 업데이트
        self.y = sol.y[:, -1]
        I, Dx = self.y[0], self.y[1]

        # --- 3. P, D 항 계산 ---
        P = self.b * SPs - PVs
        if self.Td > 0:
            D = self.Nd * ((self.c * SPs - PVs) - Dx)
        else:
            D = 0
        
        # --- 4. 제어 신호 계산 및 포화 처리 ---
        CSbs = self.Kp * (P + I + D)
        CSs = np.clip(CSbs, 0, 1)

        # --- 5. 안티 와인드업 track 신호 업데이트 ---
        # 다음 스텝의 _system_dynamics 계산에 사용될 값
        self.track = (CSs - CSbs) / (self.Kp * self.Ni) if self.Kp != 0 else 0

        # --- 6. 최종 제어 신호 변환 ---
        self.CS = self.CSmin + CSs * (self.CSmax - self.CSmin)

        return self.CS