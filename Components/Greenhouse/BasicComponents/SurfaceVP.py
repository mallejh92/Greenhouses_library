class SurfaceVP:
    def __init__(self, T=300.0):
        """
        T: 표면 온도 [K]
        """
        self.T = T      # 입력 온도 [K]
        self.VP = 0.0   # 출력 수증기압 [Pa]
        self.update()

    def saturated_vapor_pressure(self, temp_C):
        """
        포화 수증기압 계산 [Pa]
        Antoine 식 또는 Tetens 공식을 사용할 수 있음.
        여기선 Tetens 공식 기반으로 작성:

        e_s = 610.78 * exp(17.269 * T / (T + 237.3))  # T in °C
        """
        from math import exp
        return 610.78 * exp(17.269 * temp_C / (temp_C + 237.3))

    def update(self):
        """
        주어진 온도 T[K]에서 포화 수증기압 계산
        """
        T_C = self.T - 273.15
        self.VP = self.saturated_vapor_pressure(T_C)

    def get_vapor_pressure(self):
        return self.VP
