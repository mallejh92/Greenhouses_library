import numpy as np
from Modelica.Thermal.HeatTransfer.Interfaces.Element1D import Element1D
from HeatAndVapourTransfer.VentilationRates.NaturalVentilationRate_1 import NaturalVentilationRate_1

class FreeVentilation(Element1D):
    """
    Heat exchange by ventilation
    
    This model computes the heat transfer between the inside and outside air due to natural ventilation 
    as a function of the air exchange rate. It also takes into account the leakage rate through the 
    greenhouse structure, which is dependent on the wind speed and the leakage coefficient of the greenhouse.
    
    Note:
    - port_a.T and port_b.T must be in Kelvin
    - Window opening angles (theta_l, theta_w) must be between 0 and π/2 radians
    - Wind speed (u) must be non-negative
    - Leakage coefficient (f_leakage) must be positive
    """
    
    def __init__(self, A, phi=np.radians(25), fr_window=0.078, l=0, h=0, 
                 f_leakage=1.5e-4, thermalScreen=False, topAir=False):
        """
        Initialize the FreeVentilation model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        phi : float, optional
            Inclination of the roof [rad], default is 25 degrees
        fr_window : float, optional
            Number of windows per m² greenhouse, default is 0.078
        l : float, optional
            Length of the window [m]
        h : float, optional
            Width of the window [m]
        f_leakage : float, optional
            Greenhouse leakage coefficient, default is 1.5e-4
        thermalScreen : bool, optional
            Presence of a thermal screen in the greenhouse, default is False
        topAir : bool, optional
            False for: Main air zone; True for: Top air zone, default is False
            
        Raises:
            ValueError: If any parameter is outside its valid range
        """
        super().__init__()  # Element1D의 __init__ 호출
        
        # 입력값 검증
        if A <= 0:
            raise ValueError(f"Surface area A must be positive, got {A}")
        if not (0 <= phi <= np.pi/2):
            raise ValueError(f"Roof inclination phi must be between 0 and π/2, got {phi}")
        if fr_window < 0:
            raise ValueError(f"Window frequency must be non-negative, got {fr_window}")
        if l < 0:
            raise ValueError(f"Window length must be non-negative, got {l}")
        if h < 0:
            raise ValueError(f"Window height must be non-negative, got {h}")
        if f_leakage <= 0:
            raise ValueError(f"Leakage coefficient must be positive, got {f_leakage}")
        
        # Parameters (Modelica parameters)
        self.A = A
        self.phi = phi
        self.fr_window = fr_window
        self.l = l
        self.h = h
        self.f_leakage = f_leakage
        self.thermalScreen = thermalScreen
        self.topAir = topAir
        
        # Constants (Modelica variables with fixed values)
        self.rho_air = 1.2  # Air density [kg/m³]
        self.c_p_air = 1005  # Specific heat capacity of air [J/(kg·K)]
        
        # State variables (Modelica varying inputs)
        self.theta_l = 0  # Window opening at the leeside side [rad]
        self.theta_w = 0  # Window opening at the windward side [rad]
        self.u = 0  # Wind speed [m/s]
        
        # Internal variables (Modelica variables)
        self.HEC_ab = 0  # Heat exchange coefficient
        self.f_vent = 0  # Ventilation rate
        
        # Initialize ventilation rate calculator
        self.airExchangeRate = NaturalVentilationRate_1(
            phi=phi,
            fr_window=fr_window,
            l=l,
            h=h,
            thermalScreen=thermalScreen
        )
        
    def set_window_openings(self, theta_l, theta_w):
        """
        Set window opening angles
        
        Parameters:
        -----------
        theta_l : float
            Window opening at the leeside side [rad]
        theta_w : float
            Window opening at the windward side [rad]
            
        Raises:
            ValueError: If angles are outside valid range
        """
        if not (0 <= theta_l <= np.pi/2):
            raise ValueError(f"Leeside window angle must be between 0 and π/2, got {theta_l}")
        if not (0 <= theta_w <= np.pi/2):
            raise ValueError(f"Windward window angle must be between 0 and π/2, got {theta_w}")
        
        self.theta_l = theta_l
        self.theta_w = theta_w
        
    def set_wind_speed(self, u):
        """
        Set wind speed
        
        Parameters:
        -----------
        u : float
            Wind speed [m/s]
            
        Raises:
            ValueError: If wind speed is negative
        """
        if u < 0:
            raise ValueError(f"Wind speed must be non-negative, got {u}")
        self.u = u
        
    def step(self):
        """
        Calculate and update ventilation heat transfer.
        
        Returns:
            float: Heat flow rate [W] from port_a to port_b
            
        Raises:
            RuntimeError: If ports are not properly connected
        """
        # 포트 연결 확인
        if not hasattr(self, 'port_a') or not hasattr(self, 'port_b'):
            raise RuntimeError("Both port_a and port_b must be connected before calling step()")
            
        # Get temperatures from ports
        T_a = self.port_a.T
        T_b = self.port_b.T
        
        # 온도 검증
        if T_a <= 0 or T_b <= 0:
            raise ValueError("Temperatures must be positive (in Kelvin)")
        
        # Calculate temperature difference
        dT = T_b - T_a
        
        # Update ventilation rate calculator
        self.airExchangeRate.update(u=self.u, theta_l=self.theta_l, theta_w=self.theta_w, dT=dT)
        
        # Calculate ventilation rate (Modelica equation)
        if not self.topAir:
            self.f_vent = self.airExchangeRate.f_vent_air
        else:
            self.f_vent = self.airExchangeRate.f_vent_top
            
        # Calculate heat exchange coefficient (Modelica equation)
        if self.thermalScreen:
            if self.topAir:
                self.HEC_ab = self.rho_air * self.c_p_air * (self.f_vent + max(0.25, self.u) * self.f_leakage)
            else:
                self.HEC_ab = 0
        else:
            self.HEC_ab = self.rho_air * self.c_p_air * (self.f_vent + max(0.25, self.u) * self.f_leakage)
            
        # Calculate heat flow (Modelica equation)
        Q_flow = self.A * self.HEC_ab * dT
        
        # Update ports
        self.port_a.Q_flow = Q_flow
        self.port_b.Q_flow = -Q_flow
        
        # Update Element1D
        self.update()
        
        return Q_flow
