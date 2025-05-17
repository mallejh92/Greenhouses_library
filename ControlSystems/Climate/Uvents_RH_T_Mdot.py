import numpy as np
from ControlSystems.PID import PID

class Uvents_RH_T_Mdot:
    """
    Controller for window opening based on air humidity and temperature.

    Mimics Modelica Greenhouses.ControlSystems.Climate.Uvents_RH_T_Mdot:
      - Uses two PID loops (humidity & temperature) and a third temp-only PID
      - Blends their outputs via sigmoid functions of mass flow rate
    """

    def __init__(self):
        # Default (Modelica) inputs if not overridden by connector
        self.RH_air_input = 0.75        # [-], default relative humidity
        self.T_air = 293.15             # [K], actual air temperature
        self.T_air_sp = 293.15          # [K], setpoint air temperature
        self.Mdot = 0.528               # [kg/s], mass flow rate through vents

        # Effective humidity input (will remain default unless externally set)
        self.RH_air = self.RH_air_input

        # Parameters
        self.Tmax_tomato = 299.15       # [K], maximum allowable tomato temp
        self.U_max = 1.0                # [-], maximum vent opening fraction

        # PID for humidity control
        self.PID = PID(
            Kp=-0.5,
            Ti=650,
            PVmin=0.1,
            PVmax=1.0,
            CSmin=0.0,
            CSmax=self.U_max,
            PVstart=0.5,
            CSstart=0.5,
            steadyStateInit=False
        )

        # PID for temperature control (with humidity)
        self.PIDT = PID(
            Kp=-0.5,
            Ti=500,
            PVmin=12 + 273.15,
            PVmax=30 + 273.15,
            CSmin=0.0,
            CSmax=self.U_max,
            PVstart=0.5,
            CSstart=0.5,
            steadyStateInit=False
        )

        # PID for temperature control (no humidity)
        self.PIDT_noH = PID(
            Kp=-0.5,
            Ti=500,
            PVmin=12 + 273.15,
            PVmax=30 + 273.15,
            CSmin=0.0,
            CSmax=self.U_max,
            PVstart=0.5,
            CSstart=0.5,
            steadyStateInit=False
        )

        # Control output (vent opening fraction)
        self.U_vents = 0.0

    @property
    def y(self):
        """
        Expose control output under attribute 'y', matching Modelica interface.
        """
        return self.U_vents

    def compute(self):
        """
        Compute the ventilation control signal based on current RH_air, T_air, and Mdot.

        Returns
        -------
        float
            Vent opening control fraction between 0 and U_max.
        """
        # If no external RH_air was set, stick with default input
        # (Modelica: if cardinality(RH_air)==0 then RH_air=RH_air_input)
        if self.RH_air is None:
            self.RH_air = self.RH_air_input

        # Update humidity PID
        self.PID.PV = self.RH_air
        self.PID.SP = self.RH_air_input  # RH_max = 0.85 in Modelica, but default input is 0.75? use 0.85?
        # To strictly follow Modelica, use:
        self.PID.SP = 0.85
        self.PID.compute()

        # Update temperature PID with humidity
        self.PIDT.PV = self.T_air
        self.PIDT.SP = self.Tmax_tomato
        self.PIDT.compute()

        # Update temperature-only PID
        self.PIDT_noH.PV = self.T_air
        self.PIDT_noH.SP = self.T_air_sp + 2.0
        self.PIDT_noH.compute()

        # Sigmoid-based blending weights
        sigmoid1 = 1.0 / (1.0 + np.exp(-200.0 * (self.Mdot - 0.05)))
        sigmoid2 = 1.0 / (1.0 + np.exp( 200.0 * (self.Mdot - 0.05)))

        # Blend the PID outputs
        # Modelica: y = sigmoid1*max(PID.CS, PIDT.CS) + sigmoid2*max(PID.CS, PIDT_noH.CS)
        self.U_vents = (
            sigmoid1 * max(self.PID.CS, self.PIDT.CS)
          + sigmoid2 * max(self.PID.CS, self.PIDT_noH.CS)
        )

        return self.U_vents
