import numpy as np
from Interfaces.Heat.HeatPorts_a import HeatPorts_a
from Interfaces.Heat.HeatPorts_b import HeatPorts_b
from .ThermalConductor import ThermalConductor
from Components.Greenhouse.BasicComponents.Layer import Layer

class SoilConduction:
    """
    Heat conduction through soil and concrete layers
    
    This class implements the heat conduction model for soil and concrete layers
    in a greenhouse system.
    """
    
    def __init__(self, A, N_c=2, N_s=5, lambda_c=1.7, lambda_s=0.85, steadystate=False):
        """
        Initialize the SoilConduction model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        N_c : int, optional
            Number of concrete layers, default is 2
        N_s : int, optional
            Number of soil layers, default is 5
        lambda_c : float, optional
            Thermal conductivity of concrete [W/(m·K)], default is 1.7
        lambda_s : float, optional
            Thermal conductivity of soil [W/(m·K)], default is 0.85
        steadystate : bool, optional
            If true, sets the derivative of T of each layer to zero during initialization,
            default is False
        """
        if N_c < 0:
            raise ValueError("N_c must be greater than or equal to 0")
        if N_s < 1:
            raise ValueError("N_s must be greater than or equal to 1")
            
        self.A = A
        self.N_c = N_c
        self.N_s = N_s
        self.lambda_c = lambda_c
        self.lambda_s = lambda_s
        self.steadystate = steadystate
        
        # Initialize arrays
        self.G_s = np.zeros(N_s)  # Thermal conductance of soil layers
        self.G_c = np.zeros(max(0, N_c-1))  # Thermal conductance of concrete layers
        self.G_cc = 0.0  # Thermal conductance between concrete and soil
        self.th_s = np.zeros(N_s)  # Thickness of soil layers
        self.th_c = np.zeros(max(0, N_c-1))  # Thickness of concrete layers
        
        # Initialize heat ports
        self.port_a = HeatPorts_a(1)[0]  # Top heat port
        self.T_layer_Nplus1 = 283.15  # Temperature of layer N+1 (soil)
        
        # Initialize thermal conductors and layers
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize thermal conductors and layers"""
        # Initialize soil components
        self.TC_s = [ThermalConductor() for _ in range(self.N_s)]
        self.Layer_s = [Layer(rho=1, c_p=1.73e6, A=self.A, steadystate=self.steadystate) 
                       for _ in range(self.N_s)]
        
        # Initialize concrete components if needed
        if self.N_c > 0:
            self.TC_cc = ThermalConductor()
            if self.N_c > 1:
                self.TC_c = [ThermalConductor() for _ in range(self.N_c-1)]
                self.Layer_c = [Layer(rho=1, c_p=2e6, A=self.A, steadystate=self.steadystate) 
                              for _ in range(self.N_c-1)]
        
        # Initialize soil temperature source
        self.soil = HeatPorts_b(1)[0]  # Prescribed temperature for soil
        
        # Calculate thicknesses and conductances
        self._calculate_parameters()
        
    def _calculate_parameters(self):
        """Calculate layer thicknesses and thermal conductances"""
        if self.N_c == 0:
            # Just soil layers
            self.th_s[0] = 0.02
            self.G_s[0] = self.lambda_s / (self.th_s[0]/4*3) * self.A
            self.G_cc = 0
        else:
            # Concrete layers + soil layers
            self.th_s[0] = 0.02 * 2**(self.N_c-1)
            self.G_s[0] = self.lambda_s / (self.th_s[0]/2) * self.A
            
            if self.N_c == 1:
                self.G_cc = self.lambda_c / 0.005 * self.A
            else:
                self.G_cc = self.lambda_c / (self.th_c[self.N_c-2]/2) * self.A
                self.th_c[0] = 0.02
                self.G_c[0] = self.lambda_c / (self.th_c[0]/4*3) * self.A
                
                if self.N_c > 2:
                    for j in range(1, self.N_c-1):
                        self.th_c[j] = self.th_c[0] * 2**j
                        self.G_c[j] = self.lambda_c / (self.th_c[j]/4*3) * self.A
        
        # Calculate soil layer parameters
        if self.N_s > 1:
            for i in range(1, self.N_s):
                self.th_s[i] = self.th_s[0] * 2**i
                self.G_s[i] = self.lambda_s / (self.th_s[i]/4*3) * self.A
                
        # Update thermal conductors
        for i in range(self.N_s):
            self.TC_s[i].G = self.G_s[i]
            self.Layer_s[i].V = self.A * self.th_s[i]
            
        if self.N_c > 0:
            self.TC_cc.G = self.G_cc
            if self.N_c > 1:
                for i in range(self.N_c-1):
                    self.TC_c[i].G = self.G_c[i]
                    self.Layer_c[i].V = self.A * self.th_c[i]
                    
        # Initialize TC_ss (thermal conductor for soil temperature)
        self.TC_ss = ThermalConductor(G=self.lambda_s/(self.th_s[self.N_s-1]/2)*self.A)
                    
    def calculate(self):
        """
        Calculate heat transfer through soil and concrete layers
        
        Returns:
        --------
        Q_flow : float
            Heat flow rate [W]
        """
        # Connect components based on configuration
        if self.N_c == 0:
            # Just soil layers
            self.TC_s[0].port_a = self.port_a
        else:
            if self.N_c == 1:
                self.TC_cc.port_a = self.port_a
            else:
                self.TC_c[0].port_a = self.port_a
                
        # Calculate heat transfer through layers
        Q_flow = 0
        if self.N_c > 0:
            if self.N_c == 1:
                Q_flow = self.TC_cc.calculate()
            else:
                for i in range(self.N_c-1):
                    if i == 0:
                        self.TC_c[i].port_b = self.Layer_c[i].heatPort
                    else:
                        self.Layer_c[i-1].heatPort = self.TC_c[i].port_a
                        self.TC_c[i].port_b = self.Layer_c[i].heatPort
                    Q_flow = self.TC_c[i].calculate()
                    
        # Calculate heat transfer through soil layers
        for i in range(self.N_s):
            if i == 0:
                if self.N_c == 0:
                    self.TC_s[i].port_b = self.Layer_s[i].heatPort
                else:
                    self.TC_cc.port_b = self.TC_s[i].port_a
                    self.TC_s[i].port_b = self.Layer_s[i].heatPort
            else:
                self.Layer_s[i-1].heatPort = self.TC_s[i].port_a
                self.TC_s[i].port_b = self.Layer_s[i].heatPort
            Q_flow = self.TC_s[i].calculate()
            
        # Connect last soil layer to soil temperature source
        self.Layer_s[self.N_s-1].heatPort = self.TC_ss.port_a
        self.TC_ss.port_b = self.soil
        self.soil.T = self.T_layer_Nplus1
        Q_flow = self.TC_ss.calculate()
            
        return Q_flow
