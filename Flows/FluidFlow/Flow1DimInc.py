import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass
from Functions.Enumerations.Discretizations import Discretizations
from .Cell1DimInc import Cell1DimInc
from .HeatTransfer.MassFlowDependence import MassFlowDependence
from .HeatTransfer.BaseClasses.PartialHeatTransferZones import PartialHeatTransferZones
from Interfaces.Heat.ThermalPortConverter import ThermalPortConverter
from Interfaces.Heat.HeatPortConverter_ThermoCycle_Modelica import HeatPortConverter_ThermoCycle_Modelica
from Interfaces.Heat.HeatPorts_a import HeatPorts_a

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

class Flow1DimInc:
    """
    1-D fluid flow model (finite volume discretization - incompressible fluid model).
    Based on the Cell component
    """
    
    def __init__(self, N: int = 10, Nt: int = 1, A: float = 16.18, V: float = 0.03781,
                 Mdotnom: float = 0.2588, Unom: float = 1000.0, pstart: float = 1e5,
                 Tstart_inlet: float = 293.15, Tstart_outlet: float = 283.15,
                 steadystate: bool = True,
                 discretization: Discretizations = Discretizations.centr_diff,
                 heat_transfer_model: Optional[PartialHeatTransferZones] = None):
        """
        Initialize flow model
        
        Parameters:
            N (int): Number of cells
            Nt (int): Number of cells in parallel
            A (float): Lateral surface of the tube [m2]
            V (float): Volume of the tube [m3]
            Mdotnom (float): Nominal fluid flow rate [kg/s]
            Unom (float): Nominal heat transfer coefficient [W/(m2.K)]
            pstart (float): Fluid pressure start value [Pa]
            Tstart_inlet (float): Inlet temperature start value [K]
            Tstart_outlet (float): Outlet temperature start value [K]
            steadystate (bool): If true, sets the derivative of h to zero during initialization
            discretization (Discretizations): Spatial discretization scheme
            heat_transfer_model (PartialHeatTransferZones): Heat transfer model
        """
        # Parameters
        self.N = N
        self.Nt = Nt
        self.A = A
        self.V = V
        self.Mdotnom = Mdotnom
        self.Unom = Unom
        self.pstart = pstart
        self.steadystate = steadystate
        self.discretization = discretization
        
        # Constants
        self.pi = np.pi
        
        # Calculate initial enthalpy vector
        hstart = np.linspace(
            self._specific_enthalpy_pTX(pstart, Tstart_inlet),
            self._specific_enthalpy_pTX(pstart, Tstart_outlet),
            N
        )
        
        # Initialize heat transfer model if not provided
        if heat_transfer_model is None:
            heat_transfer_model = MassFlowDependence()
        
        # Create cells
        self.Cells = [
            Cell1DimInc(
                Vi=V/N,
                Ai=A/N,
                Mdotnom=Mdotnom,
                Unom=Unom,
                pstart=pstart,
                hstart=hstart[i],
                Nt=Nt,
                steadystate=steadystate,
                discretization=discretization,
                heat_transfer=heat_transfer_model
            )
            for i in range(N)
        ]
        
        # Initialize port converters
        self.thermalPortConverter = ThermalPortConverter(N=N)
        self.heatPort_ThermoCycle_Modelica = HeatPortConverter_ThermoCycle_Modelica(
            N=N, A=A, Nt=Nt
        )
        self.heatPorts_a = [HeatPorts_a() for _ in range(N)]
        
        # State variables
        self.hnode_ = np.zeros(N+1)  # Node enthalpies
        self.Q_tot = 0.0  # Total heat flux [W]
        self.M_tot = 0.0  # Total mass [kg]
        
        # Summary
        self.Summary = SummaryClass(
            n=N,
            T_cell=np.zeros(N),
            h=np.zeros(N),
            T=np.zeros(N),
            hnode=np.zeros(N+1),
            rho=np.zeros(N),
            Mdot=0.0,
            p=0.0
        )
        
        # Connect cells
        self._connect_cells()
        
    def _connect_cells(self):
        """Connect cells and ports"""
        # Connect cells in series
        for i in range(self.N-1):
            self.Cells[i].OutFlow = self.Cells[i+1].InFlow
            
        # Connect thermal ports
        for i in range(self.N):
            self.thermalPortConverter.thermalPorts[i] = self.Cells[i].Wall_int
            self.heatPort_ThermoCycle_Modelica.heatPorts[i] = self.heatPorts_a[i]
        
    def _specific_enthalpy_pTX(self, p: float, T: float, X: Optional[np.ndarray] = None) -> float:
        """
        Calculate specific enthalpy from pressure, temperature and composition
        
        Parameters:
            p (float): Pressure [Pa]
            T (float): Temperature [K]
            X (np.ndarray, optional): Composition vector
            
        Returns:
            float: Specific enthalpy [J/kg]
        """
        # Simplified water properties
        c_p = 4186.0  # Specific heat capacity of water [J/(kg.K)]
        return c_p * T
        
    def update(self, dt: float, h_in: float, h_out: float,
              heat_transfer: Optional[PartialHeatTransferZones] = None) -> Tuple[float, float]:
        """
        Update flow model state
        
        Parameters:
            dt (float): Time step [s]
            h_in (float): Inlet enthalpy [J/kg]
            h_out (float): Outlet enthalpy [J/kg]
            heat_transfer (PartialHeatTransferZones, optional): Heat transfer model
            
        Returns:
            tuple: (Q_tot, M_tot) Total heat flux and total mass
        """
        # Update cells
        for i in range(self.N):
            if i == 0:
                h_in_cell = h_in
            else:
                h_in_cell = self.Cells[i-1].h
                
            if i == self.N-1:
                h_out_cell = h_out
            else:
                h_out_cell = self.Cells[i+1].h
                
            self.Cells[i].update(dt, h_in_cell, h_out_cell, heat_transfer)
            
        # Update node enthalpies
        self.hnode_[0] = h_in
        for i in range(self.N):
            self.hnode_[i+1] = self.Cells[i].hnode_ex
            
        # Calculate total heat flux and mass
        self.Q_tot = self.A/self.N * sum(cell.qdot for cell in self.Cells) * self.Nt
        self.M_tot = self.V/self.N * sum(cell.rho for cell in self.Cells)
        
        # Update summary
        self.Summary.T_cell = np.array([cell.T for cell in self.Cells])
        self.Summary.h = np.array([cell.h for cell in self.Cells])
        self.Summary.T = np.array([cell.T for cell in self.Cells])
        self.Summary.hnode = self.hnode_
        self.Summary.rho = np.array([cell.rho for cell in self.Cells])
        self.Summary.Mdot = self.Cells[0].M_dot * self.Nt
        self.Summary.p = self.Cells[0].p
        
        return self.Q_tot, self.M_tot
