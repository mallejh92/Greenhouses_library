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
        
    def update(self, T_air: float, T_air_sp: float, Mdot: float, dt: float):
        """
        Update control system and outputs
        
        Parameters:
            T_air (float): Air temperature [K]
            T_air_sp (float): Air temperature setpoint [K]
            Mdot (float): Mass flow rate [kg/s]
            dt (float): Time step [s]
        """
        # Update PID controllers
        self.PIDT.update(T_air, self.Tmax_tomato, dt)
        self.PIDT_noH.update(T_air, T_air_sp + 2, dt)
        
        # Calculate sigmoid functions for mass flow rate
        sigmoid1 = 1 / (1 + np.exp(-200 * (Mdot - 0.05)))
        sigmoid2 = 1 / (1 + np.exp(200 * (Mdot - 0.05)))
        
        # Calculate control signal
        y = sigmoid1 * self.PIDT.CS + sigmoid2 * self.PIDT_noH.CS
        
        return y
