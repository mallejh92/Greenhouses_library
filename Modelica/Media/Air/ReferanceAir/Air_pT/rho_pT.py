from .airBaseProp_pT import airBaseProp_pT, AuxiliaryProperties

def rho_props_pT(p: float, T: float, aux: AuxiliaryProperties) -> float:
    """
    압력, 온도, 보조 물성으로부터 밀도를 계산
    Modelica의 rho_props_pT 함수를 Python으로 변환
    
    Args:
        p (float): 압력 [Pa]
        T (float): 온도 [K]
        aux (AuxiliaryProperties): 보조 물성들
        
    Returns:
        float: 밀도 [kg/m³]
    """
    # 보조 물성에서 밀도를 직접 반환
    return aux.rho

def rho_pT(p: float, T: float) -> float:
    """
    압력과 온도로부터 밀도를 계산
    Modelica의 rho_pT 함수를 Python으로 변환
    
    Args:
        p (float): 압력 [Pa]
        T (float): 온도 [K]
        
    Returns:
        float: 밀도 [kg/m³]
    """
    # Modelica: rho := rho_props_pT(p, T, Air_Utilities.airBaseProp_pT(p, T));
    aux = airBaseProp_pT(p, T)
    return rho_props_pT(p, T, aux)
