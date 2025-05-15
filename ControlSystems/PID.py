import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class PIDParameters:
    """PID controller parameters"""
    Kp: float  # Proportional gain (normalised units)
    Ti: float  # Integral time
    Td: float = 0  # Derivative time
    Nd: float = 1  # Derivative action up to Nd / Td rad/s
    Ni: float = 1  # Ni*Ti is the time constant of anti-windup compensation
    b: float = 1  # Setpoint weight on proportional action
    c: float = 0  # Setpoint weight on derivative action
    PVmin: float = 0  # Minimum value of process variable for scaling
    PVmax: float = 1  # Maximum value of process variable for scaling
    CSmin: float = 0  # Minimum value of control signal for scaling
    CSmax: float = 1  # Maximum value of control signal for scaling
    PVstart: float = 0.5  # Start value of PV (scaled)
    CSstart: float = 0.5  # Start value of CS (scaled)
    steadyStateInit: bool = False

class PID:
    """
    ISA PID controller with anti-windup
    """
    
    def __init__(self, params: PIDParameters):
        """
        Initialize PID controller
        
        Parameters:
            params (PIDParameters): PID controller parameters
        """
        self.params = params
        
        # Initialize state variables
        self.I = params.CSstart / params.Kp  # Integral action / Kp
        self.Dx = params.c * params.PVstart - params.PVstart  # State of approximated derivator
        self.CSs = params.CSstart  # Control signal scaled in per unit
        self.CSbs = params.CSstart  # Control signal scaled in per unit before saturation
        
        # Time step for numerical integration
        self.dt = 0.01  # Default time step
        
    def update(self, PV: float, SP: float, dt: Optional[float] = None) -> float:
        """
        Update PID controller and calculate control signal
        
        Parameters:
            PV (float): Process variable
            SP (float): Set point
            dt (float, optional): Time step for numerical integration
            
        Returns:
            float: Control signal
        """
        if dt is not None:
            self.dt = dt
            
        # Scaling
        SPs = (SP - self.params.PVmin) / (self.params.PVmax - self.params.PVmin)
        PVs = (PV - self.params.PVmin) / (self.params.PVmax - self.params.PVmin)
        
        # Controller actions
        P = self.params.b * SPs - PVs  # Proportional action / Kp
        
        # Integral action
        if self.params.Ti > 0:
            track = (self.CSs - self.CSbs) / (self.params.Kp * self.params.Ni)
            dI = (SPs - PVs + track) / self.params.Ti
            self.I += dI * self.dt
        else:
            self.I = 0
            
        # Derivative action
        if self.params.Td > 0:
            # State equation of approximated derivator
            dDx = (self.params.Nd / self.params.Td) * ((self.params.c * SPs - PVs) - self.Dx)
            self.Dx += dDx * self.dt
            # Output equation of approximated derivator
            D = self.params.Nd * ((self.params.c * SPs - PVs) - self.Dx)
        else:
            self.Dx = 0
            D = 0
            
        # Calculate control signal
        self.CSbs = self.params.Kp * (P + self.I + D)  # Control signal before saturation
        self.CSs = np.clip(self.CSbs, 0, 1)  # Saturated control signal
        
        # Convert to actual control signal
        CS = self.params.CSmin + self.CSs * (self.params.CSmax - self.params.CSmin)
        
        return CS
