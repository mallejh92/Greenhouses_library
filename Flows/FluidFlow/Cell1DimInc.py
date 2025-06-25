import numpy as np
from typing import Optional, Tuple, List
from Functions.Enumerations.Discretizations import Discretizations
from Modelica.Fluid.Interfaces.FluidPort_a import FluidPort_a
from Modelica.Fluid.Interfaces.FluidPort_b import FluidPort_b
from Interfaces.Heat.ThermalPortL import ThermalPortL
from Flows.FluidFlow.HeatTransfer.MassFlowDependence import MassFlowDependence

class Cell1DimInc:
    """
    1-D incompressible fluid flow model
    
    This model describes the flow of an incompressible fluid through a single cell.
    An overall flow model can be obtained by interconnecting several cells in series.
    
    This is a Python implementation of the Modelica Cell1DimInc model from the Greenhouses library.
    """
    
    def __init__(self, Vi: float, Ai: float, Mdotnom: float, Unom: float,
                 pstart: float, hstart: float = 1e5,
                 Nt: int = 1, steadystate: bool = True,
                 discretization: Discretizations = Discretizations.centr_diff,
                 Medium=None):
        """
        Initialize cell model
        
        Parameters:
            Vi (float): Volume of a single cell [m3]
            Ai (float): Lateral surface of a single cell [m2]
            Mdotnom (float): Nominal fluid flow rate [kg/s]
            Unom (float): Nominal heat transfer coefficient [W/(m2.K)]
            pstart (float): Fluid pressure start value [Pa]
            hstart (float): Start value of enthalpy [J/kg]
            Nt (int): Number of cells in parallel
            steadystate (bool): If true, sets the derivative of h to zero during initialization
            discretization (Discretizations): Spatial discretization scheme
            Medium: Fluid medium model
        """
        # Geometric characteristics
        self.Vi = Vi
        self.Ai = Ai
        self.Nt = Nt
        
        # Parameters
        self.Mdotnom = Mdotnom
        self.Unom = Unom
        self.pstart = pstart
        self.hstart = hstart
        self.steadystate = steadystate
        self.discretization = discretization
        self.Medium = Medium
        
        # Constants
        self.pi = np.pi
        
        # Fluid ports
        self.InFlow = FluidPort_a(Medium=Medium, p_start=pstart, h_start=hstart)
        self.OutFlow = FluidPort_b(Medium=Medium, p_start=pstart, h_start=hstart)
        
        # Thermal port
        self.Wall_int = ThermalPortL()
        
        # State variables
        self.p = pstart  # Pressure [Pa]
        self.h = hstart  # Specific enthalpy [J/kg]
        self.M_dot = Mdotnom/Nt  # Mass flow rate [kg/s]
        self.hnode_su = hstart  # Inlet node enthalpy [J/kg]
        self.hnode_ex = hstart  # Outlet node enthalpy [J/kg]
        
        # Fluid state
        self.fluidState = self._calculate_fluid_state()
        
        # Derived variables
        self.T = 0.0  # Temperature [K]
        self.rho = 0.0  # Density [kg/m3]
        self.qdot = 0.0  # Heat flux [W/m2]
        self.Q_tot = 0.0  # Total heat flux [W]
        self.M_tot = 0.0  # Total mass [kg]
        
        # Initialize heat transfer model
        self.heatTransfer = MassFlowDependence(
            n=1,
            Mdotnom=Mdotnom/Nt,
            Unom_l=Unom,
            Unom_tp=Unom,
            Unom_v=Unom,
            M_dot=self.M_dot,
            x=0.0,
            T_fluid=[293.15]  # Use reasonable initial temperature
        )
        
        # Connect heat transfer model to thermal port
        self.heatTransfer.thermalPortL = [self.Wall_int]
        
        # Initialize fluid properties
        self._update_fluid_properties()
        
        # Set initial heat transfer parameters
        self.heatTransfer.T_fluid = [self.T]
        self.heatTransfer.FluidState = [self.fluidState]
        
    def _calculate_fluid_state(self) -> dict:
        """
        Calculate fluid thermodynamic state from pressure and enthalpy
        
        Returns:
            dict: Fluid state containing temperature, density, etc.
        """
        if self.Medium is None:
            # Simple ideal gas approximation for testing
            # Use more realistic values for water-like fluid
            # Calculate temperature from enthalpy with proper reference
            h_ref = 4.2e5  # Reference enthalpy at 273.15 K [J/kg]
            cp = 4200.0    # Specific heat capacity [J/(kg·K)]
            T_ref = 273.15 # Reference temperature [K]
            
            # Temperature calculation: T = T_ref + (h - h_ref) / cp
            T = T_ref + (self.h - h_ref) / cp
            # T = max(273.15, T)  # 이 줄을 주석 처리
            
            # Density calculation using ideal gas law
            rho = max(1.0, self.p / (287.0 * T))
            
            return {
                'temperature': T,
                'density': rho,
                'pressure': self.p,
                'enthalpy': self.h
            }
        else:
            # Use actual medium model
            return self.Medium.setState_ph(self.p, self.h)
    
    def _update_fluid_properties(self):
        """Update fluid properties from current state"""
        self.fluidState = self._calculate_fluid_state()
        
        if self.Medium is None:
            # 온도 제한 해제
            self.T = self.fluidState['temperature']
            self.rho = max(1.0, self.fluidState['density'])  # Minimum density of 1 kg/m³
        else:
            self.T = self.Medium.temperature(self.fluidState)
            self.rho = max(1.0, self.Medium.density(self.fluidState))  # Safety check
    
    def _update_node_enthalpies(self, h_in: float, h_out: float):
        """
        Update node enthalpies based on discretization scheme
        
        Parameters:
            h_in (float): Inlet enthalpy [J/kg]
            h_out (float): Outlet enthalpy [J/kg]
        """
        if self.discretization == Discretizations.centr_diff:
            self.hnode_su = h_in
            self.hnode_ex = 2*self.h - self.hnode_su
            
        elif self.discretization == Discretizations.centr_diff_AllowFlowReversal:
            if self.M_dot >= 0:
                self.hnode_su = h_in
                self.hnode_ex = 2*self.h - self.hnode_su
            else:
                self.hnode_ex = h_out
                self.hnode_su = 2*self.h - self.hnode_ex
                
        elif self.discretization == Discretizations.upwind_AllowFlowReversal:
            self.hnode_ex = self.h if self.M_dot >= 0 else h_out
            self.hnode_su = self.h if self.M_dot <= 0 else h_in
            
        elif self.discretization == Discretizations.upwind:
            self.hnode_su = h_in
            self.hnode_ex = self.h
            
        else:  # Upwind with smoothing
            self.hnode_ex = self.h if self.M_dot >= 0 else h_out
            self.hnode_su = self.h if self.M_dot <= 0 else h_in
    
    def _update_boundary_conditions(self):
        """Update boundary conditions for fluid ports"""
        # Enthalpies
        self.hnode_su = self.InFlow.h_outflow
        self.OutFlow.h_outflow = self.hnode_ex
        
        # Pressures
        self.p = self.OutFlow.p
        self.InFlow.p = self.p
        
        # Mass flow
        self.M_dot = self.InFlow.m_flow / self.Nt
        self.OutFlow.m_flow = -self.M_dot * self.Nt
        
        # Composition (for multi-component fluids)
        if hasattr(self.InFlow, 'Xi_outflow') and hasattr(self.OutFlow, 'Xi_outflow'):
            self.InFlow.Xi_outflow = self.OutFlow.Xi_outflow.copy()
            self.OutFlow.Xi_outflow = self.InFlow.Xi_outflow.copy()
    
    def _update_heat_transfer(self):
        """Update heat transfer model"""
        # Update heat transfer model parameters
        self.heatTransfer.M_dot = self.M_dot
        self.heatTransfer.T_fluid = [self.T]
        self.heatTransfer.FluidState = [self.fluidState]
        
        # Calculate heat transfer
        self.heatTransfer.calculate()
        
        # Get heat flux
        self.qdot = self.heatTransfer.q_dot[0]
    
    def _energy_balance(self, dt: float):
        """
        Solve energy balance equation
        
        Parameters:
            dt (float): Time step [s]
        """
        if not self.steadystate:
            # Energy balance: Vi*rho*der(h) + M_dot*(hnode_ex - hnode_su) = Ai*qdot
            # Add safety checks to prevent numerical issues
            if self.rho > 0 and self.Vi > 0:
                dh = (self.M_dot*(self.hnode_ex - self.hnode_su) - 
                      self.Ai*self.qdot)/(self.Vi*self.rho)
                
                # Limit the change to prevent numerical instability
                max_dh = 1e6  # Maximum enthalpy change per time step [J/kg]
                dh = max(-max_dh, min(max_dh, dh))
                
                self.h += dh*dt
                
                # Ensure enthalpy stays within reasonable bounds
                self.h = max(1e4, min(1e7, self.h))  # Between 10 kJ/kg and 10 MJ/kg
    
    def update(self, dt: float, h_in: float = None, h_out: float = None) -> Tuple[float, float, float]:
        """
        Update cell state
        
        Parameters:
            dt (float): Time step [s]
            h_in (float, optional): Inlet enthalpy [J/kg]
            h_out (float, optional): Outlet enthalpy [J/kg]
            
        Returns:
            tuple: (h, Q_tot, M_tot) Updated enthalpy, total heat flux, and total mass
        """
        # Update boundary conditions
        self._update_boundary_conditions()
        
        # Get enthalpies from ports if not provided
        if h_in is None:
            h_in = self.InFlow.h_outflow
        if h_out is None:
            h_out = self.OutFlow.h_outflow
        
        # Update node enthalpies based on discretization scheme
        self._update_node_enthalpies(h_in, h_out)
        
        # Update fluid properties
        self._update_fluid_properties()
        
        # Update heat transfer
        self._update_heat_transfer()
        
        # Solve energy balance
        self._energy_balance(dt)
        
        # Update derived variables
        self.Q_tot = self.Ai * self.qdot * self.Nt
        self.M_tot = self.Vi * self.rho
        
        return self.h, self.Q_tot, self.M_tot
    
    def connect_inlet(self, other_port):
        """
        Connect inlet port to another fluid port
        
        Parameters:
            other_port: Fluid port to connect to inlet
        """
        self.InFlow.connect(other_port)
    
    def connect_outlet(self, other_port):
        """
        Connect outlet port to another fluid port
        
        Parameters:
            other_port: Fluid port to connect to outlet
        """
        self.OutFlow.connect(other_port)
    
    def connect_thermal(self, thermal_port):
        """
        Connect thermal port
        
        Parameters:
            thermal_port: Thermal port to connect
        """
        self.Wall_int.connect(thermal_port)
    
    def __str__(self):
        """String representation of the cell"""
        return (f"Cell1DimInc\n"
                f"Vi = {self.Vi:.2f} m³\n"
                f"Ai = {self.Ai:.2f} m²\n"
                f"M_dot = {self.M_dot:.2f} kg/s\n"
                f"p = {self.p:.2f} Pa\n"
                f"h = {self.h:.2f} J/kg\n"
                f"T = {self.T:.2f} K\n"
                f"rho = {self.rho:.2f} kg/m³\n"
                f"Q_tot = {self.Q_tot:.2f} W")
