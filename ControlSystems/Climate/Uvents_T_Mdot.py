from ControlSystems.PID import PID
import numpy as np

class Uvents_T_Mdot:
    """
    Modelica의 Uvents_T_Mdot 모델을 Python으로 1:1로 구현한 클래스
    (온실 환기 제어, 온도 및 질량유량 기반)
    """
    
    def __init__(self):
        # 입력 변수 초기화 (Modelica와 동일)
        self.T_air = 293.15  # 공기 온도 [K]
        self.T_air_sp = 293.15  # 공기 온도 설정값 [K]
        self.Mdot = 0.528  # 질량 유량 [kg/s]
        self.Tmax_tomato = 299.15  # 토마토 최대 허용 온도 [K]
        self.U_max = 1.0  # 최대 제어 신호
        
        # PID 컨트롤러 2개 (파라미터, 초기값 모두 Modelica와 동일)
        self.PIDT = PID(
            Kp=-0.5,
            Ti=500,
            Td=0,
            CSstart=0.5,
            steadyStateInit=False,
            CSmin=0,
            PVmin=12 + 273.15,
            PVmax=30 + 273.15,
            CSmax=self.U_max,
            PVstart=0.5
        )
        
        self.PIDT_noH = PID(
            Kp=-0.5,
            Ti=500,
            Td=0,
            CSstart=0.5,
            steadyStateInit=False,
            CSmin=0,
            PVmin=12 + 273.15,
            PVmax=30 + 273.15,
            CSmax=self.U_max,
            PVstart=0.5
        )
        
        # 출력 신호
        self.y = 0.0
        
    def step(self, dt: float) -> float:
        """
        한 타임스텝(dt)마다 제어 신호 계산 (Modelica와 동일한 논리)
        """
        # PIDT: 입력값 연결 (PV, SP)
        self.PIDT.PV = self.T_air
        self.PIDT.SP = self.Tmax_tomato
        self.PIDT.step(dt)
        
        # PIDT_noH: 입력값 연결 (PV, SP)
        self.PIDT_noH.PV = self.T_air
        self.PIDT_noH.SP = self.T_air_sp + 2.0
        self.PIDT_noH.step(dt)
        
        # 시그모이드 함수 계산 (질량유량에 따른 가중치, 수치 안정성 위해 clip)
        x = 200.0 * (self.Mdot - 0.05)
        x = np.clip(x, -500.0, 500.0)  # exp 오버플로 방지
        sigmoid1 = 1.0 / (1.0 + np.exp(-x))
        sigmoid2 = 1.0 / (1.0 + np.exp(x))
        
        # PID 출력 결합 (Modelica와 동일)
        self.y = sigmoid1 * self.PIDT.CS + sigmoid2 * self.PIDT_noH.CS
        
        return self.y
