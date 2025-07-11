import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.Element1D import Element1D

class FreeConvection(Element1D):
    """
    Upward or downward heat exchange by free convection from a horizontal or inclined surface.
    If studying heat exchange of Air-Floor: connect the filled port to the floor and the unfilled port to the air.
    """
    def __init__(self, phi, A, floor=False, thermalScreen=False, Air_Cov=True, topAir=False):
        """
        Initialize the FreeConvection model
        Parameters:
            phi (float): Inclination of the surface [rad]
            A (float): Floor surface area [m²]
            floor (bool): True if floor, false if cover or thermal screen heat flux
            thermalScreen (bool): Presence of a thermal screen in the greenhouse
            Air_Cov (bool): True if heat exchange air-cover, False if air-screen
            topAir (bool): False if MainAir-Cov; True for TopAir-Cov
        """
        super().__init__()
        self.phi = phi
        self.A = A
        self.floor = floor
        self.thermalScreen = thermalScreen
        self.Air_Cov = Air_Cov
        self.topAir = topAir
        self.SC = 0
        self.s = 11
        self.HEC_ab = 0.0
        self.HEC_up_flr = 0.0
        self.HEC_down_flr = 0.0
        # Modelica-style port names are now inherited from Element1D (port_a/b)

    def step(self):
        """
        Calculate heat transfer by free convection
        """
        # 온도 차이 계산 (port_a.T - port_b.T)
        dT = self.port_a.T - self.port_b.T
        
        if not self.floor:
            if self.thermalScreen:
                if self.Air_Cov:
                    if not self.topAir:
                        # Exchange main air-cover (with screen)
                        self.HEC_ab = 0
                    else:
                        # Exchange top air-cover
                        self.HEC_ab = 1.7 * max(1e-9, abs(dT))**0.33 * (np.cos(self.phi))**(-0.66)
                else:
                    # Exchange air-screen
                    self.HEC_ab = self.SC * 1.7 * max(1e-9, abs(dT))**0.33
            else:
                # Exchange main air-cover (no screen)
                self.HEC_ab = 1.7 * max(1e-9, abs(dT))**0.33 * (np.cos(self.phi))**(-0.66)
            self.HEC_up_flr = 0
            self.HEC_down_flr = 0
        else:
            # 지면 열전달의 경우 differentiable switch function 사용
            self.HEC_up_flr = 1/(1 + np.exp(-self.s * dT)) * 1.7 * abs(dT)**0.33  # dT>0일 때 사용
            self.HEC_down_flr = 1/(1 + np.exp(self.s * dT)) * 1.3 * abs(dT)**0.25  # dT<0일 때 사용
            self.HEC_ab = self.HEC_up_flr + self.HEC_down_flr
            
        # 열유량 계산
        self.Q_flow = self.A * self.HEC_ab * dT
        
        # Element1D의 update() 호출하여 포트 열유량 업데이트
        self.update()
        
        return self.Q_flow

    def _calc_h_cnv(self):
        # Implementation of _calc_h_cnv method
        # This method should return the calculated convective heat transfer coefficient
        # For now, we'll use a placeholder return value
        return 1.0  # Placeholder return value
