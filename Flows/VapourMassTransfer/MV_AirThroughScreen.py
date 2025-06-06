from Interfaces.Vapour.Element1D import Element1D
from Media.Air.ReferenceAir.Air_pT import Air_pT

class MV_AirThroughScreen(Element1D):
    """
    Vapour mass flow exchanged from the greenhouse main air zone (below the thermal screen)
    to the top air zone (above the screen).
    
    This model calculates the vapour mass flow through a screen based on:
    - Screen closure state
    - Temperature difference
    - Air density
    - Screen properties
    
    Attributes:
        A (float): Floor surface in m2
        input_f_AirTop (bool): True if input the exchange rate, False to compute it
        f_AirTop (float): Air exchange rate when input_f_AirTop is True
        W (float): Length of the screen when closed (SC=1) in m
        K (float): Screen flow coefficient
        SC (float): Screen closure (1:closed, 0:open)
        T_a (float): Temperature at port a in K
        T_b (float): Temperature at port b in K
    """
    
    def __init__(self, A: float, input_f_AirTop: bool = True, f_AirTop: float = 0.0,
                 W: float = 0.0, K: float = 0.0):
        """
        Initialize the MV_AirThroughScreen model.
        
        Args:
            A (float): Floor surface in m2
            input_f_AirTop (bool): True if input the exchange rate, False to compute it
            f_AirTop (float): Air exchange rate when input_f_AirTop is True
            W (float): Length of the screen when closed (SC=1) in m
            K (float): Screen flow coefficient
        """
        super().__init__()
        
        # Parameters
        self.A = A
        self.input_f_AirTop = input_f_AirTop
        self.f_AirTop = f_AirTop
        self.W = W
        self.K = K
        
        # Varying inputs
        self.SC = 0.0  # Screen closure 1:closed, 0:open
        self.T_a = 300.0  # Temperature at port a in K
        self.T_b = 300.0  # Temperature at port b in K
        
        # Constants
        self.c_p_air = 1005.0  # Specific heat capacity of air
        self.R = 8314.0  # Gas constant
        self.M_H = 18.0  # Molar mass of water
        self.g_n = 9.81  # Gravitational acceleration
        
        # Variables
        self.f_AirTopp = 0.0  # Computed air exchange rate
        self.rho_air = 0.0  # Air density at port a
        self.rho_top = 0.0  # Air density at port b
        self.rho_mean = 0.0  # Mean air density
        self.dT = 0.0  # Temperature difference
        self.VEC_AirTop = 0.0  # Mass transfer coefficient in kg/(s.Pa.m2)
        self.dP = 0.0  # Pressure difference between ports
        
        # Modelica-style mass port names
        if not hasattr(self, 'massPort_a'):
            self.massPort_a = type('MassPort', (), {'VP': 0.0, 'P': 1e5})()
        if not hasattr(self, 'massPort_b'):
            self.massPort_b = type('MassPort', (), {'VP': 0.0, 'P': 1e5})()
        
    def connect_ports(self, HeatPort_a, HeatPort_b) -> None:
        """
        Connect two ports and calculate the pressure difference.
        
        Args:
            HeatPort_a: First port (filled square)
            HeatPort_b: Second port (empty square)
        """
        super().connect_ports(HeatPort_a, HeatPort_b)
        
    def step(self, dt=None):
        """
        Calculate the vapour mass flow through the screen.
        
        Parameters:
        -----------
        dt : float, optional
            Time step [s]. Not used in calculations but included for compatibility.
            
        Returns:
        --------
        MV_flow : float
            Mass flow rate [kg/s]
        """
        # Update pressure difference (Modelica: dP = port_a.VP - port_b.VP)
        self.dP = self.massPort_a.VP - self.massPort_b.VP
        
        # Calculate air exchange rate (Modelica equations)
        if self.input_f_AirTop:
            self.f_AirTopp = self.f_AirTop
            self.rho_air = 999.0  # Dummy value as in Modelica
            self.rho_top = 999.0
            self.rho_mean = 999.0
            self.dT = 999.0
        else:
            # Calculate air densities using Air_pT model (Modelica: Air_pT.density_pT)
            self.rho_air = Air_pT.density_pT(1e5, self.T_a)
            self.rho_top = Air_pT.density_pT(1e5, self.T_b)
            self.rho_mean = (self.rho_air + self.rho_top) / 2
            self.dT = self.T_a - self.T_b
            
            # Calculate air exchange rate (Modelica equation)
            self.f_AirTopp = (self.SC * self.K * abs(self.dT)**0.66 + 
                            (1 - self.SC) / self.rho_mean * 
                            (0.5 * self.rho_mean * self.W * (1 - self.SC) * 
                             self.g_n * abs(self.rho_air - self.rho_top))**0.5)
        
        # Calculate mass exchange coefficient and mass flow (Modelica equations)
        self.VEC_AirTop = self.M_H * self.f_AirTopp / self.R / 287.0
        self.MV_flow = self.A * self.VEC_AirTop * self.dP
        
        # Update parent class
        super().update()
        
        return self.MV_flow
        
    def __str__(self) -> str:
        """String representation of the MV_AirThroughScreen model"""
        return (f"MV_AirThroughScreen\n"
                f"A = {self.A:.2f} m2\n"
                f"SC = {self.SC:.2f}\n"
                f"T_a = {self.T_a:.2f} K\n"
                f"T_b = {self.T_b:.2f} K\n"
                f"dP = {self.dP:.2f} Pa\n"
                f"VEC_AirTop = {self.VEC_AirTop:.2e} kg/(s.Pa.m2)\n"
                f"MV_flow = {self.MV_flow:.2e} kg/s")
