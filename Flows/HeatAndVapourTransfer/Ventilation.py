import numpy as np
from .VentilationRates.NaturalVentilationRate_2 import NaturalVentilationRate_2
from .VentilationRates.ForcedVentilationRate import ForcedVentilationRate
from Interfaces.HeatAndVapour.Element1D import Element1D

class Ventilation(Element1D):
    """
    온실 공기와 외부 공기 간의 환기를 통한 열 및 수증기 질량 흐름을 계산하는 클래스
    
    환기는 주로 창문을 통한 자연 환기로 이루어지며, 온실 기후 제어기에 의해 제어됩니다.
    또한 온실이 완전히 밀폐되지 않아 누설에 의한 작은 환기 흐름도 존재합니다.
    
    자연 환기에 의한 열 전달은 환기율의 함수로 계산되며, 주로 두 가지 요소에 의존합니다:
    1. 창문 개방도 (기후 제어기에 의해 설정)
    2. 창문 특성 (예: 풍압 계수, 창문 마찰에 의한 에너지 방출 계수)
    
    기계 환기 시스템이 설치된 경우, 이 시스템에 의한 열 흐름도 고려됩니다.
    강제 환기의 열 흐름도 환기율의 함수로 계산되며, 이는 기계 환기 시스템의 용량과
    제어 밸브의 위치에 따라 달라집니다.
    
    열 스크린의 상태에 따라 열 흐름은 상부 또는 주 공기 구역에서 발생할 수 있습니다.
    따라서 사용자는 Boolean 파라미터를 통해 어떤 구역이 모델링되는지 지정해야 합니다.
    스크린 폐쇄도 기후 제어기의 제어 변수로 필요한 입력입니다.
    
    이 모델은 온실 구조를 통한 누설율도 고려하며, 이는 풍속(모델 입력)과
    온실의 누설 계수(모델 파라미터, 구조 특성)에 따라 달라집니다.
    """
    
    def __init__(self, A: float, thermalScreen: bool = False, topAir: bool = False,
                 forcedVentilation: bool = False, phi_VentForced: float = 0.0):
        """
        Ventilation 클래스 초기화
        
        Args:
            A: 온실 바닥 면적 [m²]
            thermalScreen: 온실 내 열 스크린 존재 여부
            topAir: False: 주 공기 구역, True: 상부 공기 구역 (thermalScreen이 True일 때만 사용)
            forcedVentilation: 온실 내 기계 환기 시스템 존재 여부
            phi_VentForced: 기계 환기 시스템의 공기 흐름 용량 [m³/s] (forcedVentilation이 True일 때만 사용)
        """
        super().__init__()
        
        # 파라미터
        self.A = A
        self.thermalScreen = thermalScreen
        self.topAir = topAir
        self.forcedVentilation = forcedVentilation
        self.phi_VentForced = phi_VentForced
        
        # 변하는 입력값
        self.SC = 0.0  # 스크린 폐쇄도 (1: 닫힘, 0: 열림)
        self.u = 0.0   # 풍속 [m/s]
        self.U_vents = 0.0  # 지붕 창문 개방도 (0~1)
        self.U_VentForced = 0.0  # 강제 환기 제어 (0~1, forcedVentilation이 True일 때만 사용)
        
        # 변수
        self.HEC_ab = 0.0  # 열 전달 계수
        self.rho_air = 1.2  # 공기 밀도 [kg/m³]
        self.c_p_air = 1005  # 공기 비열 [J/(kg·K)]
        self.f_vent = 0.0  # 온실 공기에서 외부 공기로의 공기 교환율 [m³/(m²·s)]
        self.R = 8314  # 기체 상수
        self.M_H = 18  # 수증기 분자량
        self.f_vent_total = 0.0  # 총 환기율 [m³/(m²·s)]
        self.f_ventForced = 0.0  # 강제 환기율 [m³/(m²·s)]
        
        # Element1D에서 상속받은 포트 사용
        # HeatPort_a/b: 열 포트 (내부/외부)
        # MassPort_a/b: 질량 포트 (내부/외부)
        
        # 환기율 계산 컴포넌트 초기화
        self.natural_vent = NaturalVentilationRate_2(
            thermalScreen=thermalScreen,
            C_d=0.75,  # 환기 방출 계수
            C_w=0.09,  # 환기 전역 풍압 계수
            eta_RfFlr=0.1,  # 최대 지붕 환기구 면적과 온실 바닥 면적의 비율
            h_vent=0.68,  # 단일 환기구의 수직 치수 [m]
            c_leakage=1.5e-4  # 온실 누설 계수
        )
        
        if forcedVentilation:
            self.forced_vent = ForcedVentilationRate(
                A=A,
                phi_VentForced=phi_VentForced
            )
    
    def update(self, SC: float, u: float, U_vents: float, T_a: float, T_b: float,
              VP_a: float, VP_b: float, U_VentForced: float = None) -> tuple:
        """
        환기 시스템 상태 업데이트
        
        Args:
            SC: 스크린 폐쇄도 (1: 닫힘, 0: 열림)
            u: 풍속 [m/s]
            U_vents: 지붕 창문 개방도 (0~1)
            T_a: 내부 공기 온도 [K]
            T_b: 외부 공기 온도 [K]
            VP_a: 내부 수증기압 [Pa]
            VP_b: 외부 수증기압 [Pa]
            U_VentForced: 강제 환기 제어 (0~1, forcedVentilation이 True일 때만 사용)
            
        Returns:
            tuple: (Q_flow, MV_flow, f_vent_total) - 열 흐름 [W], 수증기 질량 흐름 [kg/s], 총 환기율 [m³/(m²·s)]
        """
        # 입력값 업데이트
        self.SC = SC
        self.u = u
        self.U_vents = U_vents
        if self.forcedVentilation and U_VentForced is not None:
            self.U_VentForced = U_VentForced
        
        # 포트 온도 및 수증기압 업데이트
        self.HeatPort_a.T = T_a
        self.HeatPort_b.T = T_b
        self.MassPort_a.VP = VP_a
        self.MassPort_b.VP = VP_b
        
        # 자연 환기율 계산
        if not self.topAir:
            self.f_vent = self._calculate_natural_ventilation_air()
        else:
            self.f_vent = self._calculate_natural_ventilation_top()
        
        # 강제 환기율 계산
        if self.forcedVentilation:
            if not self.topAir:
                self.f_ventForced = self._calculate_forced_ventilation()
            else:
                self.f_ventForced = 0.0
        else:
            self.f_ventForced = 0.0
        
        # 총 환기율 계산
        self.f_vent_total = self.f_vent + self.f_ventForced
        
        # 열 전달 계수 계산
        self.HEC_ab = self.rho_air * self.c_p_air * self.f_vent_total
        
        # 열 흐름 계산
        dT = T_a - T_b
        Q_flow = self.A * self.HEC_ab * dT
        
        # 수증기 질량 흐름 계산
        MV_flow = (self.A * self.M_H * self.f_vent_total / self.R * 
                  (VP_a/T_a - VP_b/T_b))
        
        # 포트 흐름 업데이트
        self.HeatPort_a.Q_flow = Q_flow
        self.HeatPort_b.Q_flow = -Q_flow
        self.MassPort_a.MV_flow = MV_flow
        self.MassPort_b.MV_flow = -MV_flow
        
        return Q_flow, MV_flow
        
    def _calculate_natural_ventilation_air(self) -> float:
        """주 공기 구역의 자연 환기율 계산 [m³/(m²·s)]"""
        _, f_vent_air = self.natural_vent.update(
            SC=self.SC,
            U_roof=self.U_vents,
            u=self.u,
            dT=self.HeatPort_a.T - self.HeatPort_b.T,
            T_a=self.HeatPort_a.T,
            T_b=self.HeatPort_b.T
        )
        return f_vent_air
    
    def _calculate_natural_ventilation_top(self) -> float:
        """상부 공기 구역의 자연 환기율 계산 [m³/(m²·s)]"""
        f_vent_top, _ = self.natural_vent.update(
            SC=self.SC,
            U_roof=self.U_vents,
            u=self.u,
            dT=self.HeatPort_a.T - self.HeatPort_b.T,
            T_a=self.HeatPort_a.T,
            T_b=self.HeatPort_b.T
        )
        return f_vent_top
    
    def _calculate_forced_ventilation(self) -> float:
        """강제 환기율 계산 [m³/(m²·s)]"""
        if not hasattr(self, 'forced_vent'):
            return 0.0
        return self.forced_vent.update(U_VentForced=self.U_VentForced)
