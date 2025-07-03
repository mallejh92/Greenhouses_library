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
        X: 조성 리스트 (예: [X_water, X_air, ...])
    Returns:
        phi: 상대습도 (0~1)
    """
    # 포화수증기압 계산
    p_steam_sat = min(saturation_pressure(T), 0.999 * p)
    X_water = X[0]  # 물의 질량분율 (Modelica convention)
    X_air = 1 - X_water
    # 상대습도 계산
    phi = p / p_steam_sat * X_water / (X_water + k_mair * X_air)
    # 0~1로 제한
    phi = max(0.0, min(1.0, phi))
    return phi
