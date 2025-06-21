import numpy as np
import sys
import os

# 현재 파일의 디렉토리를 기준으로 상위 디렉토리들을 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(current_dir, '..', '..')
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Modelica 모듈 경로 확인 및 추가
modelica_path = os.path.join(root_dir, 'Modelica')
if modelica_path not in sys.path:
    sys.path.insert(0, modelica_path)

try:
    from Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
    from Thermal.HeatTransfer.Interfaces.HeatPort_b import HeatPort_b
except ImportError:
    try:
        from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
        from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_b import HeatPort_b
    except ImportError as e:
        print(f"Import 오류: {e}")
        print(f"현재 Python 경로: {sys.path}")
        print(f"루트 디렉토리: {root_dir}")
        print(f"Modelica 디렉토리 존재: {os.path.exists(os.path.join(root_dir, 'Modelica'))}")
        raise

class Radiation_N:
    """
    Lumped thermal element for radiation heat transfer between N discrete volumes and a single surface.
    
    This model describes thermal radiation (electromagnetic radiation) emitted between bodies
    as a result of their temperatures. The constitutive equation used is:
        Q_flow = Gr * sigma * (T_a^4 - T_b^4)
    where Gr is the radiation conductance and sigma is the Stefan-Boltzmann constant.
    """
    
    def __init__(self, A, epsilon_a, epsilon_b, N=2, FFa=1.0, FFb=1.0, 
                 FFab1=0.0, FFab2=0.0, FFab3=0.0, FFab4=0.0):
        """
        Initialize Radiation_N model
        
        Parameters:
        -----------
        A : float
            Floor surface area [m²]
        epsilon_a : float
            Emissivity coefficient of surface A (0-1)
        epsilon_b : float
            Emissivity coefficient of surface B (0-1)
        N : int, optional
            Number of discrete flow volumes (default: 2)
        FFa : float, optional
            View factor of element A (default: 1.0)
        FFb : float, optional
            View factor of element B (default: 1.0)
        FFab1-FFab4 : float, optional
            View factors of intermediate elements (default: 0.0)
        """
        # Parameters
        self.A = A
        self.epsilon_a = epsilon_a
        self.epsilon_b = epsilon_b
        self.N = N
        
        # View factors
        self.FFa = FFa
        self.FFb = FFb
        self.FFab1 = FFab1
        self.FFab2 = FFab2
        self.FFab3 = FFab3
        self.FFab4 = FFab4
        
        # Stefan-Boltzmann constant [W/(m²·K⁴)]
        self.sigma = 5.670374419e-8
        
        # Initialize heat ports (이 부분이 중요!)
        self.heatPorts_a = [HeatPort_a() for _ in range(N)]
        self.port_b = HeatPort_b()
        
        # State variables
        self.dT4 = np.zeros(N)
        self.Q_flow_ports = np.zeros(N)
        self.Q_flow_total = 0.0
        self.REC_ab = 0.0
        
        # Initialize all ports to same temperature
        for port in self.heatPorts_a:
            port.T = 293.15
        self.port_b.T = 293.15
        
        self._update_REC_ab()
    
    def _update_REC_ab(self):
        """Update radiation exchange coefficient [W/(m²·K⁴)]"""
        if self.FFa <= 0 or self.FFb <= 0:
            self.REC_ab = 0.0
        else:
            self.REC_ab = (self.epsilon_a * self.epsilon_b * self.FFa * self.FFb * 
                          (1 - self.FFab1) * (1 - self.FFab2) * 
                          (1 - self.FFab3) * (1 - self.FFab4) * self.sigma)
    
    def set_heatPorts_a_temperature(self, T):
        """
        Set temperature for all heatPorts_a
        
        Parameters:
        -----------
        T : float or array-like
            Temperature value(s) to set [K]. If float, same value is set for all ports.
            If array-like, must have length equal to N.
        """
        if isinstance(T, (int, float)):
            for port in self.heatPorts_a:
                port.T = T
        else:
            if len(T) != self.N:
                raise ValueError(f"Temperature array length must match N={self.N}")
            for port, t in zip(self.heatPorts_a, T):
                port.T = t
    
    def set_port_b_temperature(self, T):
        """Set temperature for port_b [K]"""
        self.port_b.T = T
    
    def set_temperatures_celsius(self, T_a_celsius, T_b_celsius):
        """
        Set temperatures in Celsius (convenience method)
        
        Parameters:
        -----------
        T_a_celsius : float or array-like
            Temperature(s) for ports A [°C]
        T_b_celsius : float
            Temperature for port B [°C]
        """
        # Convert to Kelvin
        if isinstance(T_a_celsius, (int, float)):
            T_a_kelvin = T_a_celsius + 273.15
        else:
            T_a_kelvin = np.array(T_a_celsius) + 273.15
        
        T_b_kelvin = T_b_celsius + 273.15
        
        # Set temperatures
        self.set_heatPorts_a_temperature(T_a_kelvin)
        self.set_port_b_temperature(T_b_kelvin)
    
    def step(self):
        """
        Calculate radiation heat transfer
        
        Returns:
        --------
        float : Total heat flow rate [W]
        """
        # Update radiation exchange coefficient
        self._update_REC_ab()
        
        # Calculate temperature differences to the 4th power
        for i in range(self.N):
            self.dT4[i] = self.heatPorts_a[i].T**4 - self.port_b.T**4
        
        # Calculate heat flows for each port [W]
        for i in range(self.N):
            heat_flow = (self.A / self.N) * self.REC_ab * self.dT4[i]
            self.heatPorts_a[i].Q_flow = heat_flow
            self.Q_flow_ports[i] = heat_flow
        
        # Calculate total heat flow
        self.Q_flow_total = np.sum(self.Q_flow_ports)
        
        # Set port_b heat flow (negative of total, energy conservation)
        self.port_b.Q_flow = -self.Q_flow_total
        
        return self.Q_flow_total
    
    def get_heat_flux_density(self):
        """Get heat flux density [W/m²]"""
        return self.Q_flow_total / self.A if self.A > 0 else 0.0
    
    def get_results_summary(self):
        """Get formatted results summary"""
        return {
            'total_heat_flow_kW': self.Q_flow_total / 1000,
            'heat_flux_density_W_per_m2': self.get_heat_flux_density(),
            'port_heat_flows_kW': self.Q_flow_ports / 1000,
            'REC_ab': self.REC_ab,
            'temperatures_K': {
                'T_a': [port.T for port in self.heatPorts_a],
                'T_b': self.port_b.T
            },
            'temperatures_C': {
                'T_a': [port.T - 273.15 for port in self.heatPorts_a],
                'T_b': self.port_b.T - 273.15
            }
        }