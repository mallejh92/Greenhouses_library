from ControlSystems.PID import PID
import numpy as np

class Uvents_T_Mdot:
    """
    PI controller for window's opening based on maximum air temperature
    """
    
    def __init__(self):
        # Parameters
        self.Tmax_tomato = 299.15  # Maximum temperature for tomato
        self.U_max = 1  # Maximum control signal
        
        # PID controllers
        pid_temp_params = PID(
            Kp=-0.5,
            Ti=500,
            Td=0,
            CSstart=0.5,
            steadyStateInit=False,
            CSmin=0,
            PVmin=12 + 273.15,
            PVmax=30 + 273.15,
            CSmax=self.U_max,
            PVstart=0.5
        )
        self.PIDT = PID(pid_temp_params)
        
        pid_temp_noH_params = PID(
            Kp=-0.5,
            Ti=500,
            Td=0,
            CSstart=0.5,
            steadyStateInit=False,
            CSmin=0,
            PVmin=12 + 273.15,
            PVmax=30 + 273.15,
            CSmax=self.U_max,
            PVstart=0.5
        )
        self.PIDT_noH = PID(pid_temp_noH_params)
        
        # Inputs
        self.T_air = 293.15  # Air temperature [K]
        self.T_air_sp = 293.15  # Air temperature setpoint [K]
        self.Mdot = 0.0  # Mass flow rate [kg/s]
        
        # Output
        self.U_vents = 0.0  # Control signal
        
    def compute(self):
        """
        Compute control signal based on current state and inputs
        
        Returns:
        --------
        float
            Ventilation control signal (0-1)
        """
        # Update PID controllers
        self.PIDT.compute()
        self.PIDT_noH.compute()
        
        # Calculate sigmoid functions for mass flow rate
        sigmoid1 = 1 / (1 + np.exp(-200 * (self.Mdot - 0.05)))
        sigmoid2 = 1 / (1 + np.exp(200 * (self.Mdot - 0.05)))
        
        # Calculate control signal
        self.U_vents = sigmoid1 * self.PIDT.CS + sigmoid2 * self.PIDT_noH.CS
        
        return self.U_vents
