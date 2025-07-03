from dataclasses import dataclass, field
from typing import Dict, List, Optional

from Modelica.Fluid.Interfaces.FluidPort_a import FluidPort_a
from Modelica.Fluid.Interfaces.FluidPort_b import FluidPort_b
from Interfaces.Heat.ThermalPortL import ThermalPortL
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Flows.FluidFlow.HeatTransfer.MassFlowDependence import MassFlowDependence

def h_to_T(h: float, cp: float = 4180.0, h_ref: float = 1e5, T_ref: float = 300.0) -> float:
    """엔탈피를 온도로 변환"""
    return T_ref + (h - h_ref) / cp

def T_to_h(T: float, cp: float = 4180.0, h_ref: float = 1e5, T_ref: float = 300.0) -> float:
    """온도를 엔탈피로 변환"""
    return h_ref + cp * (T - T_ref)

def rho_water(T: float, rho_ref: float = 1000.0, beta: float = 0.0002, T_ref: float = 293.15) -> float:
    """물의 밀도 계산 (온도 의존성)"""
    return rho_ref * (1 - beta * (T - T_ref))

def cp_water(T: float) -> float:
    """물의 비열 (온도 의존성 포함)"""
    # 간단한 온도 의존성 모델
    return 4180.0 + 0.5 * (T - 300.0)

# ===== 최종 개선된 Cell1DimInc2Ports =====

@dataclass
class Cell1DimInc2Ports:
    """
    1차원 비압축성 유체 흐름 셀 모델
    
    주요 수정사항:
    1. 올바른 에너지 보존 방정식 구현
    2. 시간 적분 처리 추가
    3. 포트 연결 개선
    4. 초기화 로직 강화
    """
    # 파라미터
    Vi: float = 0.005        # 셀 부피 [m³]
    Ai: float = 10.0         # 측면 표면적 [m²]
    A_hx: float = 5.0        # 열교환 면적 [m²]
    Mdotnom: float = 1.0     # 공칭 질량유량 [kg/s]
    Unom: float = 100.0      # 공칭 열전달계수 [W/m²K]
    Unom_hx: float = 100.0   # HX 열전달계수 [W/m²K]
    hstart: float = 1e5      # 초기 엔탈피 [J/kg]
    pstart: float = 101325.0 # 초기 압력 [Pa]
    steadystate: bool = True
    FlowReversal: bool = False

    # 상태 변수
    h: float = field(default_factory=lambda: 1e5)
    p: float = field(default_factory=lambda: 101325.0)
    M_dot: float = 0.0
    hnode_su: float = field(default_factory=lambda: 1e5)
    hnode_ex: float = field(default_factory=lambda: 1e5)
    T: float = 300.0
    rho: float = 1000.0

    # 포트 및 열전달 모델
    InFlow: FluidPort_a = field(default_factory=FluidPort_a)
    OutFlow: FluidPort_b = field(default_factory=FluidPort_b)
    Wall_int: ThermalPortL = field(default_factory=ThermalPortL)
    HXInt: ThermalPortL = field(default_factory=ThermalPortL)
    direct_heat_port: HeatPort_a = field(default_factory=HeatPort_a)
    
    # 내부 변수
    _initialized: bool = field(default=False, init=False)
    _time: float = field(default=0.0, init=False)

    def __post_init__(self):
        """초기화 후 처리"""
        # 초기값 설정
        self.h = self.hstart
        self.p = self.pstart
        self.hnode_su = self.hstart
        self.hnode_ex = self.hstart
        
        # 초기 물성 계산
        self.T = h_to_T(self.h)
        self.rho = rho_water(self.T)
        
        # 열전달 모델 초기화
        self.heatTransfer = MassFlowDependence(
            n=1, Mdotnom=self.Mdotnom, 
            Unom_l=self.Unom, Unom_tp=self.Unom, Unom_v=self.Unom,
            M_dot=self.M_dot, x=0, T_fluid=[self.T]
        )
        self.heatTransfer1 = MassFlowDependence(
            n=1, Mdotnom=self.Mdotnom, 
            Unom_l=self.Unom_hx, Unom_tp=self.Unom_hx, Unom_v=self.Unom_hx,
            M_dot=self.M_dot, x=0, T_fluid=[self.T]
        )
        
        self._initialized = True

    def _update_fluid_properties(self):
        """유체 물성 업데이트"""
        self.T = h_to_T(self.h)
        self.rho = rho_water(self.T)

    def _handle_flow_reversal(self):
        """유량 역류 처리"""
        h_inflow = self.InFlow.h_outflow
        h_outflow_stream = self.OutFlow.h_outflow
        
        if self.FlowReversal:
            if self.M_dot >= 0:  # 정방향
                self.hnode_ex = self.h
                self.hnode_su = h_inflow
                self.InFlow.h_outflow = self.hnode_su
            else:  # 역방향
                self.hnode_ex = h_outflow_stream
                self.hnode_su = self.h
                self.InFlow.h_outflow = self.hnode_su
        else:
            # 단방향만 허용
            self.hnode_su = h_inflow
            self.hnode_ex = self.h
            self.InFlow.h_outflow = self.hstart

    def _update_heat_transfer(self):
        """열전달 모델 업데이트"""
        # Wall 열전달
        self.heatTransfer.M_dot = self.M_dot
        self.heatTransfer.T_fluid = [self.T]
        self.heatTransfer.thermalPortL[0].T = self.Wall_int.T
        self.heatTransfer.calculate()
        qdot = self.heatTransfer.q_dot[0]

        # HX 열전달  
        self.heatTransfer1.M_dot = self.M_dot
        self.heatTransfer1.T_fluid = [self.T]
        self.heatTransfer1.thermalPortL[0].T = self.HXInt.T
        self.heatTransfer1.calculate()
        qdot_hx = self.heatTransfer1.q_dot[0]
        
        return qdot, qdot_hx

    def _energy_balance(self, qdot: float, qdot_hx: float, dt: float = 0.001):
        """
        에너지 보존 방정식 (원본 Modelica와 동일)
        
        Vi*rho*der(h) + M_dot*(hnode_ex - hnode_su) - A_hx*qdot_hx = Ai*qdot + direct_heat_port.Q_flow
        
        재정리하면:
        Vi*rho*der(h) = Ai*qdot + direct_heat_port.Q_flow + A_hx*qdot_hx - M_dot*(hnode_ex - hnode_su)
        """
        energy_thermal = self.Ai * qdot + self.direct_heat_port.Q_flow
        energy_hx = self.A_hx * qdot_hx
        energy_convection = self.M_dot * (self.hnode_ex - self.hnode_su)
        
        # 에너지 변화율
        dh_dt = (energy_thermal + energy_hx - energy_convection) / (self.Vi * self.rho)
        
        # 비정상상태인 경우 엔탈피 업데이트
        if not self.steadystate:
            self.h += dh_dt * dt
            
        return dh_dt

    def _update_boundary_conditions(self):
        """경계조건 업데이트"""
        # 압력
        self.p = self.OutFlow.p
        self.InFlow.p = self.p
        
        # 질량유량
        self.M_dot = self.InFlow.m_flow
        self.OutFlow.m_flow = -self.M_dot
        
        # 엔탈피 출력
        self.OutFlow.h_outflow = self.hnode_ex
        
        # 조성
        self.InFlow.Xi_outflow = self.OutFlow.Xi_outflow.copy()
        self.OutFlow.Xi_outflow = self.InFlow.Xi_outflow.copy()
        
        # 직접 열전달 포트
        self.direct_heat_port.T = self.T

    def step(self, dt: float = 0.001) -> Dict[str, float]:
        """
        시뮬레이션 한 스텝 실행
        
        Args:
            dt: 시간 간격 [s]
            
        Returns:
            계산 결과 딕셔너리
        """
        if not self._initialized:
            raise RuntimeError("Cell not properly initialized")
            
        # 1. 포트에서 값 읽기
        self._update_boundary_conditions()
        
        # 2. 유체 물성 업데이트
        self._update_fluid_properties()
        
        # 3. 유량 역류 처리
        self._handle_flow_reversal()
        
        # 4. 열전달 계산
        qdot, qdot_hx = self._update_heat_transfer()
        
        # 5. 에너지 보존 방정식
        dh_dt = self._energy_balance(qdot, qdot_hx, dt)
        
        # 6. 시간 업데이트
        self._time += dt
        
        # 7. 계산 결과
        Q_tot = self.Ai * qdot
        M_tot = self.Vi * self.rho
        
        return {
            "time": self._time,
            "T": self.T,
            "h": self.h,
            "p": self.p,
            "rho": self.rho,
            "M_dot": self.M_dot,
            "qdot": qdot,
            "qdot_hx": qdot_hx,
            "Q_tot": Q_tot,
            "M_tot": M_tot,
            "dh_dt": dh_dt,
            "hnode_su": self.hnode_su,
            "hnode_ex": self.hnode_ex
        }

    def update(self, dt: float = 0.001) -> Dict[str, float]:
        """호환성을 위한 래퍼 함수"""
        return self.step(dt)

    def reset(self):
        """초기 상태로 리셋"""
        self.h = self.hstart
        self.p = self.pstart
        self.hnode_su = self.hstart
        self.hnode_ex = self.hstart
        self.T = h_to_T(self.h)
        self.rho = rho_water(self.T)
        self._time = 0.0