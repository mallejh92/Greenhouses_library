import numpy as np
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Modelica.Media.MoistAir.relativeHumidity_pTX import relativeHumidity_pTX

import numpy as np
import math
from typing import Optional, Dict, Any

class RHSensor:
    """
    상대습도 센서 클래스
    - Modelica의 RHSensor를 Python으로 변환
    - 연결된 포트의 상대습도를 계산하여 출력
    """
    
    def __init__(self, name: str = "RH_Sensor"):
        """
        센서 초기화
        
        Args:
            name: 센서 이름
        """
        self.name = name
        
        # 물리 상수
        self.P_atm = 101325.0  # 대기압 (Pa)
        self.R_a = 287.0  # 건조공기 기체상수 (J/(kg·K))
        self.R_s = 461.5  # 수증기 기체상수 (J/(kg·K))
        
        # 포트 연결
        self.massPort = WaterMassPort_a()
        self.heatPort = HeatPort_a()
        
        # 출력 변수
        self.RH = 0.0  # 상대습도 (0~1)
        self.w_air = 0.0  # 공기 습도비 (kg water / kg dry air)
        
    def connect_mass_port(self, mass_port: WaterMassPort_a):
        """수증기 질량 포트 연결"""
        self.massPort = mass_port
        
    def connect_heat_port(self, heat_port: HeatPort_a):
        """열 포트 연결"""
        self.heatPort = heat_port
        
    def calculate_saturation_pressure(self, T: float) -> float:
        """
        포화 수증기압 계산 (Antoine 방정식 사용)
        
        Args:
            T: 온도 (K)
            
        Returns:
            포화 수증기압 (Pa)
        """
        # Antoine 방정식 계수 (물)
        A = 8.07131
        B = 1730.63
        C = 233.426
        
        # 온도를 섭씨로 변환
        T_celsius = T - 273.15
        
        # 포화 수증기압 계산 (mmHg)
        log_p_sat = A - B / (C + T_celsius)
        p_sat_mmHg = 10 ** log_p_sat
        
        # Pa로 변환
        p_sat_Pa = p_sat_mmHg * 133.322
        
        return p_sat_Pa
    
    def calculate_relative_humidity_simple(self, P_atm: float, T: float, VP: float) -> float:
        """
        간단한 상대습도 계산
        
        Args:
            P_atm: 대기압 (Pa)
            T: 온도 (K)
            VP: 수증기 압력 (Pa)
            
        Returns:
            상대습도 (0~1)
        """
        # 포화 수증기압 계산
        P_sat = self.calculate_saturation_pressure(T)
        
        # 상대습도 = 실제 수증기압 / 포화 수증기압
        RH = VP / P_sat
        
        # 0과 1 사이로 제한
        return max(0.0, min(1.0, RH))
    
    def calculate_relative_humidity_detailed(self, P_atm: float, T: float, w_air: float) -> float:
        """
        상세한 상대습도 계산 (Modelica.Media.Air.MoistAir 방식)
        
        Args:
            P_atm: 대기압 (Pa)
            T: 온도 (K)
            w_air: 습도비 (kg water / kg dry air)
            
        Returns:
            상대습도 (0~1)
        """
        # 포화 수증기압 계산
        P_sat = self.calculate_saturation_pressure(T)
        
        # 현재 수증기 압력 계산
        VP = w_air * P_atm / (self.R_s / self.R_a + w_air)
        
        # 상대습도 계산
        RH = VP / P_sat
        
        # 0과 1 사이로 제한
        return max(0.0, min(1.0, RH))
    
    def update(self):
        """
        센서 값 업데이트
        - 포트 연결 상태를 확인하고 상대습도 계산
        """
        # 포트 질량 유량, 열 유량 0으로 설정
        self.massPort.MV_flow = 0.0
        self.heatPort.Q_flow = 0.0

        # 습도비 계산 (Modelica와 동일)
        if self.P_atm - self.massPort.VP > 0:
            self.w_air = (self.massPort.VP * self.R_a) / ((self.P_atm - self.massPort.VP) * self.R_s)
        else:
            self.w_air = 0.0

        # Modelica와 동일하게 조성 벡터 생성
        X_water = self.w_air / (1 + self.w_air)
        X = [X_water]

        # Modelica의 relativeHumidity_pTX 함수 사용
        self.RH = relativeHumidity_pTX(self.P_atm, self.heatPort.T, X)
    
    def get_output(self) -> Dict[str, float]:
        """
        센서 출력값 반환
        
        Returns:
            센서 출력 딕셔너리
        """
        return {
            'RH': self.RH * 100,  # 백분율로 변환
            'RH_fraction': self.RH,  # 소수점 형태
            'w_air': self.w_air,
            'temperature': self.heatPort.T,
            'vapor_pressure': self.massPort.VP
        }
    
    def __str__(self) -> str:
        """센서 상태 문자열 표현"""
        return f"{self.name}: RH={self.RH*100:.1f}%, T={self.heatPort.T:.1f}K, VP={self.massPort.VP:.1f}Pa"