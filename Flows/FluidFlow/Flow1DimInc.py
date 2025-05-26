import numpy as np
from dataclasses import dataclass
from typing import List, Optional
from Modelica.Fluid.Interfaces.FluidPort_a import FluidPort_a
from Modelica.Fluid.Interfaces.FluidPort_b import FluidPort_b
from Interfaces.Heat.ThermalPortConverter import ThermalPortConverter
from Interfaces.Heat.HeatPortConverter_ThermoCycle_Modelica import HeatPortConverter_ThermoCycle_Modelica
from Interfaces.Heat.HeatPorts_a import HeatPorts_a
from Interfaces.Heat.ThermalPortL import ThermalPortL
from Flows.FluidFlow.HeatTransfer.MassFlowDependence import MassFlowDependence
from Modelica.Fluid.Interfaces.FluidPort import Medium

@dataclass
class SummaryClass:
    """Summary class for storing simulation results"""
    class Arrays:
        def __init__(self, n: int, T_cell: np.ndarray):
            self.n = n
            self.T_cell = T_cell
    
    def __init__(self, n: int, T_cell: np.ndarray, h: np.ndarray, T: np.ndarray,
                 hnode: np.ndarray, rho: np.ndarray, Mdot: float, p: float):
        self.T_profile = self.Arrays(n, T_cell)
        self.n = n
        self.h = h
        self.T = T
        self.hnode = hnode
        self.rho = rho
        self.Mdot = Mdot
        self.p = p

@dataclass
class Cell1DimInc:
    """
    Single cell of the Flow1DimInc model.
    """
    Vi: float  # Volume of the cell [m³]
    Ai: float  # Lateral surface of the cell [m²]
    Nt: int    # Number of cells in parallel
    Mdotnom: float  # Nominal fluid flow rate [kg/s]
    Unom: float     # Heat transfer coefficient [W/(m²·K)]
    pstart: float   # Fluid pressure start value [Pa]
    hstart: float   # Fluid specific enthalpy start value [J/kg]
    steadystate: bool  # If true, sets the derivative of h to zero during initialization
    Medium: Medium = Medium()  # Medium model
    
    def __post_init__(self):
        # Initialize ports
        self.InFlow = FluidPort_a(Medium=self.Medium, p_start=self.pstart, h_start=self.hstart)
        self.OutFlow = FluidPort_b(Medium=self.Medium, p_start=self.pstart, h_start=self.hstart)
        self.Wall_int = ThermalPortL()
        
        # Initialize state variables
        self.h = self.hstart  # Fluid specific enthalpy [J/kg]
        self.rho = 1000.0     # Water density [kg/m³]
        self.c_p = 4186.0     # Water specific heat capacity [J/(kg·K)]
        
        # Initialize heat transfer
        self.heatTransfer = MassFlowDependence(
            n=1,
            Mdotnom=self.Mdotnom,
            Unom_l=self.Unom,
            Unom_tp=self.Unom,
            Unom_v=self.Unom
        )
        
        # Initialize node enthalpies
        self.hnode_su = self.hstart  # Upstream node enthalpy
        self.hnode_ex = self.hstart  # Downstream node enthalpy
        
        # Initialize summary
        self.Summary = SummaryClass(
            n=1,
            T_cell=np.array([self.T]),
            h=np.array([self.h]),
            T=np.array([self.T]),
            hnode=np.array([self.hnode_su, self.hnode_ex]),
            rho=np.array([self.rho]),
            Mdot=self.Mdotnom,
            p=self.pstart
        )
    
    @property
    def T(self) -> float:
        """Calculate temperature from enthalpy"""
        return self.h / self.c_p
    
    def step(self, dt: float):
        """
        Perform one simulation step
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        # Update mass flow rate
        self.heatTransfer.M_dot = self.InFlow.m_flow
        
        # Calculate heat transfer coefficient
        self.heatTransfer.calculate()
        U = self.heatTransfer.U[0]  # 첫 번째 노드의 열전달 계수 사용
        
        # Calculate heat flux
        Q = U * self.Ai * (self.Wall_int.T - self.T)
        
        # Calculate enthalpy change
        dh = (Q + self.InFlow.m_flow * (self.InFlow.h_outflow - self.h)) / (self.rho * self.Vi)
        
        # Update enthalpy
        if not self.steadystate:
            self.h += dh * dt
        
        # Update node enthalpies
        self.hnode_su = self.InFlow.h_outflow
        self.hnode_ex = self.h
        
        # Update outlet enthalpy
        self.OutFlow.h_outflow = self.h
        
        # Update outlet pressure
        self.OutFlow.p = self.InFlow.p
        
        # Update mass flow
        self.OutFlow.m_flow = -self.InFlow.m_flow
        
        # Update summary
        self.Summary.T_profile.T_cell[0] = self.T
        self.Summary.h[0] = self.h
        self.Summary.T[0] = self.T
        self.Summary.hnode[0] = self.hnode_su
        self.Summary.hnode[1] = self.hnode_ex
        self.Summary.rho[0] = self.rho
        self.Summary.Mdot = self.InFlow.m_flow
        self.Summary.p = self.InFlow.p

class Flow1DimInc:
    """
    1-D fluid flow model (finite volume discretization - incompressible fluid model).
    Based on the Cell component.
    """
    
    def __init__(self, N=10, A=16.18, Nt=1, Mdotnom=0.2588, Unom=1000.0,
                 V=0.03781, pstart=1e5, Tstart_inlet=293.15, Tstart_outlet=283.15,
                 steadystate=True, Medium=Medium()):
        """
        Initialize flow model
        
        Parameters:
        -----------
        N : int
            Number of cells
        A : float
            Lateral surface of the tube [m²]
        Nt : int
            Number of cells in parallel
        Mdotnom : float
            Nominal fluid flow rate [kg/s]
        Unom : float
            Heat transfer coefficient [W/(m²·K)]
        V : float
            Volume of the tube [m³]
        pstart : float
            Fluid pressure start value [Pa]
        Tstart_inlet : float
            Inlet temperature start value [K]
        Tstart_outlet : float
            Outlet temperature start value [K]
        steadystate : bool
            If true, sets the derivative of h to zero during initialization
        Medium : Medium
            Medium model
        """
        # Parameters
        self.N = N
        self.A = A
        self.Nt = Nt
        self.Mdotnom = Mdotnom
        self.Unom = Unom
        self.V = V
        self.steadystate = steadystate
        self.Medium = Medium
        
        # Constants
        self.rho = 1000.0  # Water density [kg/m³]
        self.c_p = 4186.0  # Water specific heat capacity [J/(kg·K)]
        
        # Calculate initial enthalpy vector
        hstart = np.linspace(
            self.specific_enthalpy(pstart, Tstart_inlet),
            self.specific_enthalpy(pstart, Tstart_outlet),
            N
        )
        
        # Initialize cells
        self.Cells = [
            Cell1DimInc(
                Vi=V/N,
                Ai=A/N,
                Nt=Nt,
                Mdotnom=Mdotnom,
                Unom=Unom,
                pstart=pstart,
                hstart=hstart[i],
                steadystate=steadystate,
                Medium=Medium
            )
            for i in range(N)
        ]
        
        # Initialize ports and converters
        self.InFlow = FluidPort_a(Medium=Medium, p_start=pstart, h_start=hstart[0])
        self.OutFlow = FluidPort_b(Medium=Medium, p_start=pstart, h_start=hstart[-1])
        self.thermalPortConverter = ThermalPortConverter(N)
        self.heatPort_ThermoCycle_Modelica = HeatPortConverter_ThermoCycle_Modelica(N, A, Nt)
        
        # Initialize heat ports with correct size
        self.heatPorts_a = [HeatPorts_a() for _ in range(N)]
        for port in self.heatPorts_a:
            port.set_size(1)  # 각 포트는 하나의 열 포트를 가짐
        
        # Connect cells
        for i in range(N-1):
            self.Cells[i].OutFlow = self.Cells[i+1].InFlow
        
        # Connect inlet and outlet
        self.Cells[0].InFlow = self.InFlow
        self.Cells[-1].OutFlow = self.OutFlow
        
        # Connect thermal ports
        self.thermalPortConverter.single = [cell.Wall_int for cell in self.Cells]
        self.heatPort_ThermoCycle_Modelica.connect_heat_ports(self.heatPorts_a)
        
        # Initialize node enthalpies
        self.hnode_ = np.zeros(N+1)
        self.hnode_[0] = hstart[0]
        self.hnode_[1:] = hstart
        
        # Initialize summary
        self.Summary = SummaryClass(
            n=N,
            T_cell=np.array([cell.T for cell in self.Cells]),
            h=np.array([cell.h for cell in self.Cells]),
            T=np.array([cell.T for cell in self.Cells]),
            hnode=self.hnode_,
            rho=np.array([cell.rho for cell in self.Cells]),
            Mdot=Mdotnom,
            p=pstart
        )
        
        # State variables
        self.Q_tot = 0.0  # Total heat flux [W]
        self.M_tot = 0.0  # Total mass [kg]
    
    def specific_enthalpy(self, p, T):
        """Calculate specific enthalpy of water"""
        return self.c_p * (T - 273.15)
    
    def step(self, dt):
        """
        Advance the simulation by one time step
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        # Update cells
        for cell in self.Cells:
            cell.step(dt)
        
        # Update converters
        self.thermalPortConverter.update()
        self.heatPort_ThermoCycle_Modelica.update()
        
        # Update node enthalpies
        self.hnode_[1:] = np.array([cell.h for cell in self.Cells])
        
        # Calculate total heat flux and mass
        self.Q_tot = self.A/self.N * sum(cell.heatTransfer.q_dot[0] for cell in self.Cells) * self.Nt
        self.M_tot = self.V/self.N * sum(cell.rho for cell in self.Cells)
        
        # Update summary
        self.Summary.T_cell = np.array([cell.T for cell in self.Cells])
        self.Summary.h = np.array([cell.h for cell in self.Cells])
        self.Summary.T = np.array([cell.T for cell in self.Cells])
        self.Summary.hnode = self.hnode_
        self.Summary.rho = np.array([cell.rho for cell in self.Cells])
        self.Summary.p = self.Cells[0].InFlow.p
