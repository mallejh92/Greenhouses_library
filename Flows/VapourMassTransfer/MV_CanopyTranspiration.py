from Interfaces.Vapour.Element1D import Element1D
import numpy as np

class MV_CanopyTranspiration(Element1D):
    """
    Vapour mass flow released by the canopy due to transpiration processes.
    The model must be connected like the following: canopy (filled port) - air (unfilled port)
    
    This is a Python implementation of Greenhouses.Flows.VapourMassTransfer.MV_CanopyTranspiration
    """
    
    def __init__(self, A=1.0, LAI=1.0, CO2_ppm=350.0, R_can=100.0, T_can=300.0):
        """
        Initialize the MV_CanopyTranspiration model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        LAI : float
            Leaf Area Index
        CO2_ppm : float
            CO2 concentration in ppm of internal air
        R_can : float
            Global irradiation above the canopy [W/m²]
        T_can : float
            Temperature of the canopy (port a) [K]
        """
        super().__init__()
        
        # Parameters
        self.A = A
        
        # Varying inputs
        self.CO2_ppm = CO2_ppm  # CO2 concentration in ppm of internal air
        self.LAI = LAI         # Leaf Area Index
        self.R_can = R_can     # Global irradiation above the canopy [W/m²]
        self.T_can = T_can     # Temperature of the canopy (port a)
        
        # Constants
        self.gamma = 65.8     # Psychometric constant
        self.rho = 1.23       # Air density [kg/m³]
        self.C_p = 1005       # Air specific heat capacity [J/(kg·K)]
        self.Le = 0.89        # Lewis number for vapour
        self.DELTAH = 2.45e6  # Latent heat of water vaporization [J/kg]
        
        # Variables
        self.E_kgsm2 = 0.0    # Canopy transpiration [kg/(s·m²)]
        self.E_Wm2 = 0.0      # Canopy transpiration [W/m²]
        self.r_s = 0.0        # Stomatal resistance of the leaves [s/m]
        self.r_bV = 275.0     # Boundary layer resistance to heat mass of the leaves [s/m]
        self.r_min = 82.0     # Minimum possible canopy resistance [s/m]
        self.r_I = 0.0        # Short-wave radiation resistance
        self.r_T = 0.0        # Temperature resistance
        self.r_CO2 = 0.0      # CO2 resistance
        self.r_VP = 0.0       # Vapour pressure deficit resistance
        self.VP_can = 0.0     # Vapour pressure of the canopy [Pa]
        self.VP_air = 0.0     # Vapour pressure of interior air [Pa]
        self.VEC_canAir = 0.0 # Mass transfer coefficient [kg/(s·Pa·m²)]
        
        # Model coefficients
        self.C_1 = 4.3        # [W/m²]
        self.C_2 = 0.54       # [W/m²]
        self.C_3 = 0.0        # [1/K²]
        self.C_4 = 0.0        # [1/Pa²]
        self.C_5 = 0.0        # [1/Pa²]
        self.T_m = 0.0        # Temperature for minimum resistance [K]
        self.S_rs = 0.0       # Switch for day/night conditions
        
        # Modelica-style mass port names
        if not hasattr(self, 'massPort_a'):
            self.massPort_a = type('MassPort', (), {'VP': 0.0, 'P': 1e5})()
        if not hasattr(self, 'massPort_b'):
            self.massPort_b = type('MassPort', (), {'VP': 0.0, 'P': 1e5})()
        
    def step(self, dt=None):
        """
        Calculate the transpiration rate
        
        Parameters:
        -----------
        dt : float, optional
            Time step [s]. Not used in calculations but included for compatibility.
            
        Returns:
        --------
        MV_flow : float
            Mass flow rate [kg/s]
        """
        # Get vapour pressures from ports
        self.VP_can = self.massPort_a.VP
        self.VP_air = self.massPort_b.VP
        
        # Calculate day/night switch (Modelica: S_rs = 1/(1+exp(-(R_can-5))))
        self.S_rs = 1 / (1 + np.exp(-(self.R_can - 5)))
        
        # Update model coefficients based on day/night conditions (Modelica equations)
        self.C_3 = 0.5e-2 * (1 - self.S_rs) + 2.3e-2 * self.S_rs
        self.T_m = (33.6 + 273.15) * (1 - self.S_rs) + (24.5 + 273.15) * self.S_rs
        self.C_4 = 1.1e-11 * (1 - self.S_rs) + 6.1e-7 * self.S_rs
        self.C_5 = 5.2e-6 * (1 - self.S_rs) + 4.3e-6 * self.S_rs
        
        # Calculate resistances (Modelica equations)
        self.r_I = (self.R_can/(2*self.LAI) + self.C_1) / (self.R_can/(2*self.LAI) + self.C_2)
        self.r_CO2 = min(1.5, 1 + self.C_4 * (self.CO2_ppm - 200)**2)
        self.r_VP = min(3.8, 1 + self.C_5 * (self.VP_can - self.VP_air)**2)
        self.r_T = 1 + self.C_3 * (self.T_can - self.T_m)**2
        
        # Calculate total stomatal resistance (Modelica: r_s = r_min * r_I * r_CO2 * r_VP * r_T)
        self.r_s = self.r_min * self.r_I * self.r_CO2 * self.r_VP * self.r_T
        
        # Calculate mass transfer coefficient (Modelica: VEC_canAir = 2*rho*C_p*LAI / (DELTAH*gamma*(r_bV + r_s)))
        self.VEC_canAir = 2 * self.rho * self.C_p * self.LAI / (self.DELTAH * self.gamma * (self.r_bV + self.r_s))
        
        # Calculate mass flow (Modelica: MV_flow = A*VEC_canAir*(VP_can - VP_air))
        self.MV_flow = self.A * self.VEC_canAir * (self.VP_can - self.VP_air)
        
        # Calculate transpiration rates (Modelica equations)
        self.E_kgsm2 = self.MV_flow / self.A
        self.E_Wm2 = self.E_kgsm2 * self.DELTAH
        
        # Update parent class
        super().update()
        
        return self.MV_flow
