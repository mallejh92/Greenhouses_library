from dataclasses import dataclass
from typing import Optional
import numpy as np
from Modelica.Media.Common.HelmholtzDerivs import HelmholtzDerivs

@dataclass
class AuxiliaryProperties:
    """공기 물성의 보조 속성들을 저장하는 클래스"""
    p: float = 0.0          # 압력 [Pa]
    T: float = 0.0          # 온도 [K]
    R_s: float = 287.0      # 기체상수 [J/(kg·K)]
    rho: float = 0.0        # 밀도 [kg/m³]
    h: float = 0.0          # 비엔탈피 [J/kg]
    s: float = 0.0          # 비엔트로피 [J/(kg·K)]
    pd: float = 0.0         # 압력의 밀도 미분 [Pa/(kg/m³)]
    pt: float = 0.0         # 압력의 온도 미분 [Pa/K]
    cv: float = 0.0         # 정적비열 [J/(kg·K)]
    cp: float = 0.0         # 정압비열 [J/(kg·K)]
    vp: float = 0.0         # 비체적의 압력 미분 [m³/(kg·Pa)]
    vt: float = 0.0         # 비체적의 온도 미분 [m³/(kg·K)]

class Air_Utilities:
    """공기 물성 계산을 위한 유틸리티 클래스"""
    
    class Basic:
        class Constants:
            R_s = 287.0      # 공기의 기체상수 [J/(kg·K)]
            h_off = 0.0      # 엔탈피 오프셋 [J/kg]
            s_off = 0.0      # 엔트로피 오프셋 [J/(kg·K)]
    
    @staticmethod
    def airBaseProp_pT(p: float, T: float) -> AuxiliaryProperties:
        """
        압력과 온도로부터 공기의 기본 물성을 계산
        Modelica의 airBaseProp_pT 함수를 Python으로 변환
        
        Args:
            p (float): 압력 [Pa]
            T (float): 온도 [K]
            
        Returns:
            AuxiliaryProperties: 공기의 보조 물성들
        """
        aux = AuxiliaryProperties()
        
        # 기본 속성 설정
        aux.p = p
        aux.T = T
        aux.R_s = Air_Utilities.Basic.Constants.R_s
        
        # 밀도 계산 (단순화된 이상기체 방정식 사용)
        aux.rho = p / (aux.R_s * T)
        
        # Helmholtz 함수 계산 (단순화된 버전)
        f = Air_Utilities._helmholtz(aux.rho, T)
        
        # 엔탈피 계산
        aux.h = aux.R_s * T * (f.tau * f.ftau + f.delta * f.fdelta) - Air_Utilities.Basic.Constants.h_off
        
        # 엔트로피 계산
        aux.s = aux.R_s * (f.tau * f.ftau - f.f) - Air_Utilities.Basic.Constants.s_off
        
        # 압력 미분 계산
        aux.pd = aux.R_s * T * f.delta * (2 * f.fdelta + f.delta * f.fdeltadelta)
        aux.pt = aux.R_s * aux.rho * f.delta * (f.fdelta - f.tau * f.fdeltatau)
        
        # 비열 계산 (0으로 나누기 방지)
        aux.cv = aux.R_s * (-f.tau * f.tau * f.ftautau)
        
        # aux.pd가 0이 아닌 경우에만 계산
        if abs(aux.pd) > 1e-10:  # 매우 작은 값보다 클 때만
            aux.cp = aux.cv + aux.T * aux.pt * aux.pt / (aux.rho * aux.rho * aux.pd)
        else:
            # 이상기체 근사 사용
            aux.cp = aux.cv + aux.R_s
        
        # 비체적 미분 계산 (0으로 나누기 방지)
        if abs(aux.pd) > 1e-10:
            aux.vp = -1 / (aux.rho * aux.rho) / aux.pd
            aux.vt = aux.pt / (aux.rho * aux.rho * aux.pd)
        else:
            # 이상기체 근사 사용
            aux.vp = -aux.rho / (aux.p * aux.rho * aux.rho)
            aux.vt = aux.rho / (aux.T * aux.rho * aux.rho)
        
        return aux
    
    @staticmethod
    def _helmholtz(rho: float, T: float) -> HelmholtzDerivs:
        """
        Helmholtz 함수와 그 미분값들을 계산 (단순화된 버전)
        
        Args:
            rho (float): 밀도 [kg/m³]
            T (float): 온도 [K]
            
        Returns:
            HelmholtzDerivs: Helmholtz 함수와 미분값들
        """
        # 단순화된 Helmholtz 함수 (이상기체 근사)
        # 실제로는 복잡한 다항식이나 표 형태의 데이터를 사용해야 함
        
        f = HelmholtzDerivs()
        
        # 이상기체 근사에서의 Helmholtz 함수
        R = 287.0  # 공기의 기체상수
        rho_ref = 1.225  # 기준 밀도 (15°C, 1atm)
        T_ref = 288.15   # 기준 온도
        
        # 무차원 변수
        delta = rho / rho_ref
        tau = T_ref / T
        
        # HelmholtzDerivs 객체에 tau와 delta 속성 추가
        f.tau = tau
        f.delta = delta
        
        # 단순화된 Helmholtz 함수 (로그 항만 포함)
        f.f = np.log(delta) - np.log(tau)
        f.fdelta = 1.0 / delta
        f.fdeltadelta = -1.0 / (delta * delta)
        f.ftau = -1.0 / tau
        f.ftautau = 1.0 / (tau * tau)
        f.fdeltatau = 0.0
        
        return f

def airBaseProp_pT(p: float, T: float) -> AuxiliaryProperties:
    """
    압력과 온도로부터 공기의 기본 물성을 계산하는 함수
    Modelica의 airBaseProp_pT 함수를 Python으로 변환
    
    Args:
        p (float): 압력 [Pa]
        T (float): 온도 [K]
        
    Returns:
        AuxiliaryProperties: 공기의 보조 물성들
    """
    return Air_Utilities.airBaseProp_pT(p, T)
