import numpy as np
from ControlSystems.PID import PID

class Uvents_RH_T_Mdot:
    """
    Modelica의 Uvents_RH_T_Mdot 모델을 Python으로 1:1로 구현한 클래스
    (습도, 온도, 질량유량 기반 환기 제어)
    """
    
    def __init__(self, T_air: float = 293.15, T_air_sp: float = 293.15, 
                 Mdot: float = 0.528, RH_air_input: float = 0.75):
        # 입력 변수 초기화 (Modelica와 동일)
        self.RH_air_input = RH_air_input  # 기본 상대습도 입력값 (connector 미사용시)
        self.RH_air = None  # 외부에서 설정된 상대습도 (cardinality 체크용)
        self.T_air = T_air  # 공기 온도 [K]
        self.T_air_sp = T_air_sp  # 공기 온도 설정값 [K]
        self.Mdot = Mdot  # 질량 유량 [kg/s]
        
        # 파라미터 (Modelica와 동일)
        self.Tmax_tomato = 299.15  # 토마토 최대 허용 온도 [K]
        self.U_max = 1.0  # 최대 제어 신호
        self.RH_max = 0.85  # 최대 허용 상대습도
        
        # PID 컨트롤러 3개 (파라미터, 초기값 모두 Modelica와 동일)
        self.PID = PID(
            Kp=-0.5,
            Ti=650,
            Td=0,
            CSstart=0.5,
            steadyStateInit=False,
            CSmin=0,
            PVmin=0.1,
            PVmax=1.0,
            CSmax=self.U_max,
            PVstart=0.5
        )
        
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
        # cardinality 체크: RH_air가 연결되지 않은 경우 RH_air_input 사용
        if self.RH_air is None:
            rh_air = self.RH_air_input
        else:
            rh_air = self.RH_air
        
        # PID 컨트롤러들: 입력값 연결 (PV, SP)
        self.PID.PV = rh_air
        self.PID.SP = self.RH_max
        self.PID.step(dt)
        
        self.PIDT.PV = self.T_air
        self.PIDT.SP = self.Tmax_tomato
        self.PIDT.step(dt)
        
        self.PIDT_noH.PV = self.T_air
        self.PIDT_noH.SP = self.T_air_sp + 2.0
        self.PIDT_noH.step(dt)
        
        # 시그모이드 함수 계산 (질량유량에 따른 가중치, 수치 안정성 위해 clip)
        x = 200.0 * (self.Mdot - 0.05)
        x = np.clip(x, -500.0, 500.0)  # exp 오버플로 방지
        sigmoid1 = 1.0 / (1.0 + np.exp(-x))
        sigmoid2 = 1.0 / (1.0 + np.exp(x))
        
        # PID 출력 결합 (Modelica 원본과 정확히 동일)
        # y = 1/(1+exp(-200*(Mdot-0.05)))*max(PID.CS,PIDT.CS) + 1/(1+exp(200*(Mdot-0.05)))*max(PID.CS,PIDT_noH.CS)
        term1 = max(self.PID.CS, self.PIDT.CS)
        term2 = max(self.PID.CS, self.PIDT_noH.CS)
        self.y = sigmoid1 * term1 + sigmoid2 * term2

        # # 디버깅 출력 (10분마다)
        # if hasattr(self, '_debug_counter'):
        #     self._debug_counter += 1
        # else:
        #     self._debug_counter = 1
        
        # # 10분(600초)마다 출력 (dt=1초 기준)
        # if self._debug_counter % 600 == 0:
        #     print(f"\n=== 환기 제어 디버깅 ({self._debug_counter*dt/3600:.2f}시간) ===")
        #     print(f"T_air={self.T_air:.2f}K({self.T_air-273.15:.2f}°C)")
        #     print(f"T_air_sp={self.T_air_sp:.2f}K({self.T_air_sp-273.15:.2f}°C)")
        #     print(f"Tmax_tomato={self.Tmax_tomato:.2f}K({self.Tmax_tomato-273.15:.2f}°C)")
        #     print(f"PIDT_noH.SP={self.PIDT_noH.SP:.2f}K({self.PIDT_noH.SP-273.15:.2f}°C)")
        #     print(f"RH_air={rh_air:.3f}, RH_max={self.RH_max:.3f}")
        #     print(f"Mdot={self.Mdot:.3f} kg/s")
        #     print(f"sigmoid1={sigmoid1:.3f}, sigmoid2={sigmoid2:.3f}")
        #     print(f"PID.CS={self.PID.CS:.3f} (습도제어)")
        #     print(f"PIDT.CS={self.PIDT.CS:.3f} (온도제어-난방시)")
        #     print(f"PIDT_noH.CS={self.PIDT_noH.CS:.3f} (온도제어-비난방시)")
        #     print(f"term1={term1:.3f}, term2={term2:.3f}")
        #     print(f"최종 y={self.y:.3f}")
        #     print("=" * 50)
        
        return self.y