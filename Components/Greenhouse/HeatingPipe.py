import numpy as np
from Flows.FluidFlow.Flow1DimInc import Flow1DimInc
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a

class HeatingPipe:
    """
    Model of a heating distribution network. Pipe model using a 1-D fluid flow model
    (finite volume discretization - incompressible fluid model).
    
    The fluid in the heating pipes from the greenhouse heating circuit is modeled by means
    of the discretized model for incompressible flow (Flow1DimInc), in which a dynamic
    energy balance and static mass and momentum balances are applied on the fluid cells.
    Heat is transferred by long-wave radiation to the canopy, floor and cover, and by
    convection to the air.
    """
    
    def __init__(self, A, d, l, N=2, N_p=1, freePipe=True, Mdotnom=0.528):
        """
        Initialize HeatingPipe model
        
        Parameters:
        -----------
        A : float
            Greenhouse floor surface [m²]
        d : float
            Pipe diameter [m]
        l : float
            Length of heating pipes [m]
        N : int, optional
            Number of cells, default is 2
        N_p : int, optional
            Number of cells in parallel, default is 1
        freePipe : bool, optional
            True if pipe in free air, false if hindered pipe, default is True
        Mdotnom : float, optional
            Nominal mass flow rate of the pipes [kg/s], default is 0.528
        """
        # Parameters
        self.A = A
        self.d = d
        self.l = l
        self.N = N
        self.N_p = N_p
        self.freePipe = freePipe
        self.Mdotnom = Mdotnom
        
        # Constants
        self.pi = np.pi
        
        # Derived values
        self.c = 0.5 if self.freePipe else 0.49
        self.A_PipeFloor = self.N_p * self.pi * self.d * self.l / self.A  # [m² pipe] / [m² floor]
        self.FF = self.A_PipeFloor * self.c  # effective floor fraction
        
        # Initialize Flow1DimInc model
        self.flow1DimInc = Flow1DimInc(
            N=self.N,
            A=self.l * self.pi * self.d,
            Nt=self.N_p,
            Mdotnom=self.Mdotnom,
            Unom=1000,
            V=self.pi * ((self.d - 0.004)/2)**2 * self.l,
            pstart=200000,
            Tstart_inlet=353.15,
            Tstart_outlet=323.15,
            steadystate=False
        )
        
        # Heat ports
        self.heatPorts = [HeatPort_a() for _ in range(self.N)]  # Heat ports for each cell
        
        # Connect heat ports to Flow1DimInc
        for i in range(self.N):
            self.heatPorts[i] = self.flow1DimInc.heatPorts_a[i]
            
        # Add single heatPort for compatibility with Greenhouse_1
        self.heatPort = self.heatPorts[0]
        
        # State variables
        self.Q_tot = 0.0  # Total heat flow [W]
        
    def step(self, dt):
        """
        Advance the simulation by one time step
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        # Update Flow1DimInc model
        self.flow1DimInc.step(dt)
        
        # Calculate total heat flow
        self.Q_tot = self.flow1DimInc.Q_tot
        
    def get_effective_heat_transfer_area(self):
        """Get effective heat transfer area"""
        return self.FF
        
    def get_inlet_temperature(self):
        """Get inlet temperature"""
        return self.flow1DimInc.Summary.T[0]
        
    def get_outlet_temperature(self):
        """Get outlet temperature"""
        return self.flow1DimInc.Summary.T[-1]
