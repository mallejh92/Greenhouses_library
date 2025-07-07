from .rho_pT import rho_pT

def density_pT(p: float, T: float) -> float:
    """
    압력과 온도로부터 공기 밀도를 계산하는 함수
    Modelica의 density_pT 함수를 Python으로 변환
    
    Args:
        p (float): 압력 [Pa]
        T (float): 온도 [K]
        
    Returns:
        float: 공기 밀도 [kg/m³]
    """
    # Modelica: d := Air_Utilities.rho_pT(p, T);
    return rho_pT(p, T)
