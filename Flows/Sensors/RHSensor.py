import numpy as np
from Interfaces.Vapour.WaterMassPort_a import WaterMassPort_a
from Interfaces.Heat.HeatPorts_a import HeatPorts_a

class RHSensor:
    """
    Relative Humidity sensor
    
    This class implements a relative humidity sensor that measures the relative humidity
    of air based on temperature and water vapor pressure. The sensor itself has no thermal
    interaction with whatever it is connected to.
    """
    
    def __init__(self, P_atm=101325):
        """
        Initialize the RHSensor model
        
        Parameters:
        -----------
        P_atm : float, optional
            Atmospheric pressure [Pa], default is 101325
        """
        # Constants
        self.P_atm = P_atm  # Atmospheric pressure [Pa]
        self.R_a = 287.0  # Gas constant for dry air [J/(kg·K)]
        self.R_s = 461.5  # Gas constant for water vapor [J/(kg·K)]
        
        # Initialize ports
        self.massPort = WaterMassPort_a()  # Water mass port
        self.heatPort = HeatPorts_a(1)[0]  # Heat port
        
        # State variables
        self.w_air = 0.0  # Air humidity ratio [kg water/kg dry air]
        self.RH = 0.0  # Relative humidity [%]
        
    def calculate(self):
        """
        Calculate relative humidity based on temperature and water vapor pressure
        
        Returns:
        --------
        RH : float
            Relative humidity [%]
        """
        # Set mass and heat flow to zero (sensor doesn't affect the system)
        self.massPort.MV_flow = 0
        self.heatPort.Q_flow = 0
        
        # Calculate air humidity ratio
        self.w_air = self.massPort.VP * self.R_a / (self.P_atm - self.massPort.VP) / self.R_s
        
        # Calculate relative humidity using the moist air model
        self.RH = self._relative_humidity_pTX(
            self.P_atm,
            self.heatPort.T,
            self.w_air
        )
        
        return self.RH
        
    def _relative_humidity_pTX(self, p, T, w):
        """
        Calculate relative humidity from pressure, temperature and humidity ratio
        
        Parameters:
        -----------
        p : float
            Pressure [Pa]
        T : float
            Temperature [K]
        w : float
            Humidity ratio [kg water/kg dry air]
            
        Returns:
        --------
        RH : float
            Relative humidity [%]
        """
        # Calculate saturation vapor pressure at temperature T
        saturation_vapor_pressure = self._saturation_pressure(T)
        
        # Calculate vapor pressure
        vapor_pressure = p * w / (self.R_a/self.R_s + w)
        
        # Calculate relative humidity with safety check
        if saturation_vapor_pressure > 1e-6:  # 포화수증기압이 너무 작지 않은 경우
            RH = vapor_pressure / saturation_vapor_pressure * 100
        else:
            # 포화수증기압이 너무 작으면 RH를 0으로 설정
            RH = 0.0
        
        return RH
        
    def _saturation_pressure(self, T):
        """
        Calculate saturation vapor pressure at temperature T using Magnus-Tetens formula
        
        Parameters:
        -----------
        T : float
            Temperature [K]
            
        Returns:
        --------
        float
            Saturation vapor pressure [Pa]
        """
        # Constants for Magnus-Tetens formula
        a1 = -6096.9385
        a2 = 21.2409642
        a3 = -2.711193e-2
        a4 = 1.673952e-5
        a5 = 2.433502
        
        # Calculate saturation pressure using the Magnus-Tetens formula
        saturation_vapor_pressure = 610.78 * np.exp((a1/T + a2 + a3*T + a4*T**2 + a5*np.log(T)))
        
        return saturation_vapor_pressure
