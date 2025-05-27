from typing import List, Optional
import numpy as np

class Medium:
    """
    기본 매체 클래스 (Modelica.Media.Interfaces.PartialMedium의 간단한 구현)
    """
    def __init__(self, nXi=0, nC=0):
        self.nXi = nXi  # 독립적인 혼합물 질량 분율의 수
        self.nC = nC    # 추가 속성의 수

class FluidPort:
    """
    Modelica의 기본 유체 포트 인터페이스
    
    이 클래스는 Modelica의 기본 유체 포트를 구현합니다.
    포트는 압력(p), 질량유량(m_flow), 엔탈피(h_outflow) 등을 포함합니다.
    
    속성:
        medium (class): 매체 모델
        m_flow (float): 질량유량 (양수는 포트로 들어가는 방향) [kg/s]
        p (float): 포트 압력 [Pa]
        h_outflow (float): m_flow < 0일 때 연결점 근처의 비엔탈피 [J/kg]
        Xi_outflow (np.ndarray): m_flow < 0일 때 연결점 근처의 독립적인 혼합물 질량 분율 [kg/kg]
        C_outflow (np.ndarray): m_flow < 0일 때 연결점 근처의 추가 속성
    """
    def __init__(self, medium=None, p_start=1e5, h_start=0.0):
        """
        유체 포트 초기화
        
        매개변수:
            medium (class): 매체 모델
            p_start (float): 초기 압력 [Pa]
            h_start (float): 초기 비엔탈피 [J/kg]
        """
        if medium is None:
            medium = Medium()  # 기본 Medium 인스턴스 생성
        self.medium = medium
        self.m_flow = 0.0  # 질량유량 [kg/s]
        self.p = p_start   # 포트 압력 [Pa]
        self.h_outflow = h_start  # 비엔탈피 [J/kg]
        self.Xi_outflow = np.zeros(self.medium.nXi)  # 혼합물 질량 분율
        self.C_outflow = np.zeros(self.medium.nC)    # 추가 속성
    
    def connect(self, other):
        """
        다른 유체 포트와 연결
        
        매개변수:
            other (FluidPort): 연결할 다른 유체 포트
            
        설명:
            - 연결된 포트들의 압력(p)은 같아야 합니다.
            - 질량유량(m_flow)의 합은 0이어야 합니다 (Modelica의 flow 변수 특성).
            - 스트림 변수(h_outflow, Xi_outflow, C_outflow)는 m_flow < 0일 때만 사용됩니다.
        """
        if not isinstance(other, FluidPort):
            raise TypeError("FluidPort 타입의 포트만 연결 가능합니다")
        
        # 연결된 포트들의 압력은 같아야 함
        self.p = other.p
        
        # Modelica에서 연결점의 m_flow 합은 0이어야 함
        # m_flow가 양수이면 포트로 들어가는 방향
        self.m_flow = -other.m_flow
        
        # 스트림 변수 업데이트 (m_flow < 0일 때만)
        if self.m_flow < 0:
            self.h_outflow = other.h_outflow
            self.Xi_outflow = other.Xi_outflow.copy()
            self.C_outflow = other.C_outflow.copy()
    
    def __str__(self):
        """유체 포트의 문자열 표현"""
        return (f"FluidPort(p={self.p:.2f} Pa, m_flow={self.m_flow:.2f} kg/s, "
                f"h_outflow={self.h_outflow:.2f} J/kg)") 