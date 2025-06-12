from ControlSystems.PID import PID
import numpy as np

class Uvents_T_Mdot:
    """
    환기 제어 시스템 (온도, 질량유량 기반)
    온도와 질량유량을 기반으로 창문 개폐를 제어하는 시스템
    """
    
    def __init__(self):
        # Varying inputs
        self.T_air = 293.15  # 공기 온도 [K]
        self.T_air_sp = 293.15  # 공기 온도 설정값 [K]
        self.Mdot = 0.528  # 질량 유량 [kg/s]
        
        # Parameters
        self.Tmax_tomato = 299.15  # 토마토 최대 허용 온도 [K]
        self.U_max = 1.0  # 최대 제어 신호
        
        # PID controllers
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
        
        # Output signal
        self._y = 0.0
        
    @property
    def y(self):
        """환기 제어 신호 (0-1)"""
        return self._y
        
    def step(self, dt: float) -> float:
        """
        환기 제어 시스템 업데이트
        
        Parameters:
        -----------
        dt : float
            Time step [s]
            
        Returns:
        --------
        float
            Ventilation control signal (0-1)
        """
        # 온도 PID 제어 (최대 온도 기준)
        self.PIDT.PV = self.T_air
        self.PIDT.SP = self.Tmax_tomato
        self.PIDT.step(dt)
        
        # 온도 PID 제어 (설정 온도 + 2K 기준)
        self.PIDT_noH.PV = self.T_air
        self.PIDT_noH.SP = self.T_air_sp + 2.0
        self.PIDT_noH.step(dt)
        
        # 시그모이드 함수 계산 (질량유량에 따른 가중치)
        x = 200.0 * (self.Mdot - 0.05)
        x = np.clip(x, -500.0, 500.0)  # 수치 안정성을 위한 클리핑
        sigmoid1 = 1.0 / (1.0 + np.exp(-x))
        sigmoid2 = 1.0 / (1.0 + np.exp(x))
        
        # PID 출력 결합
        self._y = (
            sigmoid1 * self.PIDT.CS +
            sigmoid2 * self.PIDT_noH.CS
        )
        
        return self._y
