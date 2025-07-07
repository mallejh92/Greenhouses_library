import numpy as np

# 건조공기/수증기 분자량 비 (Modelica 표준값)
k_mair = 0.62198

# 포화수증기압 계산 함수 (Tetens 공식, T[K])
def saturation_pressure(T):
    """
    포화수증기압 계산 (Tetens 공식)
    Args:
        T: 온도 [K]
    Returns:
        포화수증기압 [Pa]
    """
    T_C = T - 273.15  # K → °C
    return 610.78 * np.exp(17.2694 * T_C / (T_C + 238.3))

# 상대습도 계산 함수 (Modelica와 동일 논리)
def relativeHumidity_pTX(p, T, X):
    """
    압력(p), 온도(T), 조성(X)으로부터 상대습도(0~1)를 반환
    Args:
        p: 전체 압력 [Pa]
        T: 온도 [K]
        X: 조성 리스트 (Modelica에서는 w_air를 직접 전달)
    Returns:
        phi: 상대습도 (0~1)
    """
    # Modelica에서는 w_air (습도비)를 직접 전달
    w_air = X[0]  # kg water / kg dry air
    
    # 포화수증기압 계산
    p_steam_sat = saturation_pressure(T)
    
    # 현재 수증기 압력 계산 (w_air로부터)
    # w_air = 0.62198 * p_steam / (p - p_steam)
    # 따라서: p_steam = w_air * p / (0.62198 + w_air)
    p_steam = w_air * p / (k_mair + w_air)
    
    # 상대습도 계산
    phi = p_steam / p_steam_sat
    
    # 0~1로 제한
    phi = max(0.0, min(1.0, phi))
    return phi
