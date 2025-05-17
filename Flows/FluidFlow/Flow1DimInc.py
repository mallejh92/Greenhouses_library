import numpy as np
from dataclasses import dataclass
from typing import List, Optional
from Interfaces.Heat.ThermalPortConverter import ThermalPortConverter
from Interfaces.Heat.HeatPortConverter_ThermoCycle_Modelica import HeatPortConverter_ThermoCycle_Modelica
from Interfaces.Heat.HeatPorts_a import HeatPorts_a
from Interfaces.Heat.ThermalPortL import ThermalPortL
from Flows.FluidFlow.HeatTransfer.MassFlowDependence import MassFlowDependence

@dataclass
class SummaryClass:
    """Summary class for storing simulation results"""
    n: int
    T_cell: np.ndarray
    h: np.ndarray
    T: np.ndarray
    hnode: np.ndarray
    rho: np.ndarray
    Mdot: float
    p: float

class Cell1DimInc:
    """One-dimensional incompressible fluid cell model"""
    def __init__(self, Vi, Ai, Nt, Mdotnom, Unom, pstart, hstart, steadystate=True):
        self.Vi = Vi  # Cell volume [m³]
        self.Ai = Ai  # Cell surface area [m²]
        self.Nt = Nt  # Number of parallel tubes
        self.Mdotnom = Mdotnom  # Nominal mass flow rate [kg/s]
        self.Unom = Unom  # Heat transfer coefficient [W/(m²·K)]
        self.p = pstart  # Pressure [Pa]
        self.h = hstart  # Specific enthalpy [J/kg]
        self.steadystate = steadystate
        
        # Constants
        self.rho = 1000.0  # Water density [kg/m³]
        self.c_p = 4186.0  # Water specific heat capacity [J/(kg·K)]
        
        # Ports
        self.InFlow = None  # Will be set during connection
        self.OutFlow = None  # Will be set during connection
        self.Wall_int = ThermalPortL()  # Initialize with ThermalPortL
        
        # Heat transfer model
        self.heatTransfer = MassFlowDependence(
            n=1,
            Mdotnom=Mdotnom/Nt,
            Unom_l=Unom,
            Unom_tp=Unom,
            Unom_v=Unom
        )
        # Connect heat transfer model to wall
        self.heatTransfer.thermalPortL[0] = self.Wall_int
        
        # State variables
        self.T = self.h / self.c_p + 273.15  # Temperature [K]
        self.qdot = 0.0  # Heat flow rate [W]
        self.hnode_su = 0.0  # Upstream node enthalpy [J/kg]
        self.hnode_ex = 0.0  # Downstream node enthalpy [J/kg]
        
    def update(self, dt):
        """Update cell state"""
        # Update enthalpy
        if not self.steadystate and self.InFlow is not None and self.OutFlow is not None:
            self.h += (self.InFlow.h - self.OutFlow.h) * dt / self.Vi
            
        # Update temperature
        self.T = self.h / self.c_p + 273.15
        
        # Calculate heat flow
        if self.Wall_int is not None:
            self.qdot = self.Unom * self.Ai * (self.T - self.Wall_int.T)
        
        # Update node enthalpies
        if self.InFlow is not None:
            self.hnode_su = self.InFlow.h
        self.hnode_ex = self.h

class Flow1DimInc:
    """
    1-D fluid flow model (finite volume discretization - incompressible fluid model).
    Based on the Cell component.
    """
    
    def __init__(self, N=10, A=16.18, Nt=1, Mdotnom=0.2588, Unom=1000.0,
                 V=0.03781, pstart=1e5, Tstart_inlet=293.15, Tstart_outlet=283.15,
                 steadystate=True):
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
        """
        # Parameters
        self.N = N
        self.A = A
        self.Nt = Nt
        self.Mdotnom = Mdotnom
        self.Unom = Unom
        self.V = V
        self.steadystate = steadystate
        
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
                steadystate=steadystate
            )
            for i in range(N)
        ]
        
        # Initialize ports and converters
        self.thermalPortConverter = ThermalPortConverter(N)
        self.heatPort_ThermoCycle_Modelica = HeatPortConverter_ThermoCycle_Modelica(N, A, Nt)
        self.heatPorts_a = HeatPorts_a(size=N)
        
        # Connect cells
        for i in range(N-1):
            self.Cells[i].OutFlow = self.Cells[i+1].InFlow
        
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
    
    def update(self, dt):
        """
        Update flow model state
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        # Update cells
        for cell in self.Cells:
            cell.update(dt)
        
        # Update converters
        self.thermalPortConverter.update()
        self.heatPort_ThermoCycle_Modelica.update()
        
        # Update node enthalpies
        self.hnode_[1:] = np.array([cell.h for cell in self.Cells])
        
        # Calculate total heat flux and mass
        self.Q_tot = self.A/self.N * sum(cell.qdot for cell in self.Cells) * self.Nt
        self.M_tot = self.V/self.N * sum(cell.rho for cell in self.Cells)
        
        # Update summary
        self.Summary.T_cell = np.array([cell.T for cell in self.Cells])
        self.Summary.h = np.array([cell.h for cell in self.Cells])
        self.Summary.T = np.array([cell.T for cell in self.Cells])
        self.Summary.hnode = self.hnode_
        self.Summary.rho = np.array([cell.rho for cell in self.Cells])
        self.Summary.p = self.Cells[0].p
