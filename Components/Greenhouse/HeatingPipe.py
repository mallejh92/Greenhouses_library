import numpy as np
from Flows.FluidFlow.Flow1DimInc import Flow1DimInc
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a import HeatPort_a
from Modelica.Fluid.Interfaces.FluidPort_a import FluidPort_a
from Modelica.Fluid.Interfaces.FluidPort_b import FluidPort_b

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
    
    def __init__(self, A, d, l, N=2, N_p=1, freePipe=True, Mdotnom=0.528, steadystate=True):
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
            Number of cells (default: 2)
        N_p : int, optional
            Number of cells in parallel (default: 1)
        freePipe : bool, optional
            True if pipe in free air, false if hindered pipe (default: True)
        Mdotnom : float, optional
            Nominal mass flow rate of the pipes [kg/s] (default: 0.528)
        steadystate : bool, optional
            If true, sets the derivative of h to zero during initialization (default: True)
        """
        # Parameters
        self.A = A
        self.d = d
        self.l = l
        self.N = N
        self.N_p = N_p
        self.freePipe = freePipe
        self.Mdotnom = Mdotnom
        self.steadystate = steadystate
        
        # Constants
        self.c = 0.5 if freePipe else 0.49
        
        # Calculate areas and shape factors
        self.A_PipeFloor = N_p * np.pi * d * l / A  # [m² pipe/m² floor]
        self.FF = self.A_PipeFloor * self.c
        
        # Initialize flow model with steadystate parameter
        self.flow1DimInc = Flow1DimInc(
            N=N,
            A=l * np.pi * d,
            Nt=N_p,
            Mdotnom=Mdotnom,
            Unom=1000,
            V=np.pi * ((d - 0.004)/2)**2 * l,
            pstart=200000,
            Tstart_inlet=353.15,
            Tstart_outlet=323.15,
            steadystate=steadystate  # steadystate 파라미터 전달
        )
        
        # Initialize heat ports as NumPy array of HeatPort_a objects
        self.heatPorts = np.array([HeatPort_a() for _ in range(N)], dtype=object)
        
        # Initialize fluid ports (Modelica 원본과 동일)
        self.pipe_in = FluidPort_a()   # 입구 포트
        self.pipe_out = FluidPort_b()  # 출구 포트
        
        # Connect heat ports to flow model (Modelica의 connect(heatPorts, flow1DimInc.heatPorts_a)와 동일)
        self.flow1DimInc.heatPorts_a = self.heatPorts
        
        # Connect fluid ports to flow model (Modelica의 connect(pipe_in, flow1DimInc.InFlow)와 동일)
        self.flow1DimInc.InFlow = self.pipe_in
        self.flow1DimInc.OutFlow = self.pipe_out
    
    def step(self, dt):
        """
        Advance simulation by one time step
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        # Step flow model
        self.flow1DimInc.step(dt)
        
        # Update heat port temperatures from flow model's Summary
        # Modelica에서는 connect(heatPorts, flow1DimInc.heatPorts_a)로 자동 연결되지만,
        # Python에서는 명시적으로 업데이트해야 함
        for i in range(self.N):
            self.heatPorts[i].T = self.flow1DimInc.Summary.T[i]
    
    def get_effective_heat_transfer_area(self):
        """Get effective heat transfer area [m²]"""
        return self.A_PipeFloor
    
    def get_inlet_temperature(self):
        """Get inlet temperature [K]"""
        return self.flow1DimInc.Summary.T[0]
    
    def get_outlet_temperature(self):
        """Get outlet temperature [K]"""
        return self.flow1DimInc.Summary.T[-1]
    
    @property
    def T(self) -> float:
        """
        파이프의 평균 온도를 반환합니다 [K]
        Modelica에서는 직접적인 평균 온도 계산이 없지만,
        Python에서는 복사 열전달 계산을 위해 필요
        """
        return np.mean([port.T for port in self.heatPorts])
