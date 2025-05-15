import numpy as np
from typing import Optional, Tuple
from Functions.Enumerations.Discretizations import Discretizations

class Cell1DimInc:
    """
    1-D incompressible fluid flow model
    
    This model describes the flow of an incompressible fluid through a single cell.
    An overall flow model can be obtained by interconnecting several cells in series.
    """
    
    def __init__(self, Vi: float, Ai: float, Mdotnom: float, Unom: float,
                 pstart: float, hstart: float = 1e5,
                 Nt: int = 1, steadystate: bool = True,
                 discretization: Discretizations = Discretizations.centr_diff):
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
        
        # Constants
        self.pi = np.pi
        
        # State variables
        self.p = pstart  # Pressure [Pa]
        self.h = hstart  # Specific enthalpy [J/kg]
        self.M_dot = Mdotnom/Nt  # Mass flow rate [kg/s]
        self.hnode_su = hstart  # Inlet node enthalpy [J/kg]
        self.hnode_ex = hstart  # Outlet node enthalpy [J/kg]
        
        # Derived variables
        self.T = 0.0  # Temperature [K]
        self.rho = 0.0  # Density [kg/m3]
        self.qdot = 0.0  # Heat flux [W/m2]
        self.Q_tot = 0.0  # Total heat flux [W]
        self.M_tot = 0.0  # Total mass [kg]
        
        # Initialize heat transfer model
        self.heat_transfer = None  # To be set by user
        
    def update(self, dt: float, h_in: float, h_out: float, 
              heat_transfer: Optional[object] = None) -> Tuple[float, float, float]:
        """
        Update cell state
        
        Parameters:
            dt (float): Time step [s]
            h_in (float): Inlet enthalpy [J/kg]
            h_out (float): Outlet enthalpy [J/kg]
            heat_transfer (object, optional): Heat transfer model
            
        Returns:
            tuple: (h, Q_tot, M_tot) Updated enthalpy, total heat flux, and total mass
        """
        if heat_transfer is not None:
            self.heat_transfer = heat_transfer
            
        # Update node enthalpies based on discretization scheme
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
            
        # Update heat transfer
        if self.heat_transfer is not None:
            self.qdot = self.heat_transfer.q_dot[0]
            
        # Energy balance
        if not self.steadystate:
            dh = (self.M_dot*(self.hnode_ex - self.hnode_su) - 
                  self.Ai*self.qdot)/(self.Vi*self.rho)
            self.h += dh*dt
            
        # Update derived variables
        self.Q_tot = self.Ai*self.qdot*self.Nt
        self.M_tot = self.Vi*self.rho
        
        return self.h, self.Q_tot, self.M_tot
