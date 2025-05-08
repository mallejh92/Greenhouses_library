import numpy as np

class CHP:
    def __init__(self, V=0.005, A=10, Mdotnom=10, eta_tot=0.9, tau=60,
                 Th_start=773.15, Tmax=373.15, LHV=1000, Th_nom=773.15, Tc_nom=363.15):
        self.V = V
        self.A = A
        self.Mdotnom = Mdotnom
        self.eta_tot = eta_tot
        self.tau = tau
        self.Th = Th_start
        self.Th_nom = Th_nom
        self.Tc_nom = Tc_nom
        self.Tc = Tc_nom
        self.Tmax = Tmax
        self.LHV = LHV

        # Output variables
        self.Qdot = 0
        self.Wdot = 0
        self.Qdot_gas = 0
        self.T_water_ex_CHP = Tc_nom
        self.Wdot_el = 0
        self.eta_el = 0
        self.eta_th = 0
        self.on = True

        # First-order dynamics
        self.y = 0  # dynamic gain

        # Nominal efficiencies
        self.eta_el_nom = 0.4
        self.eta_th_nom = 0.5
        self.eta_II_nom = self.eta_el_nom / (1 - self.Tc_nom / self.Th_nom)

    def update(self, dt, T_ex_CHP, on_off=True):
        # Store temperature
        self.T_water_ex_CHP = T_ex_CHP
        self.Tc = self.T_water_ex_CHP
        self.Th = self.Th_nom

        # Update control signal (first-order filter)
        u = 1 if on_off else 0
        self.y += dt * (u - self.y) / self.tau

        # Efficiencies
        self.eta_el = self.eta_II_nom * (1 - self.Tc / self.Th)
        self.eta_th = self.eta_tot - self.eta_el

        # Fuel consumption (assume Mdot_nom_fuel = 1 for simplicity)
        Mdot_fuel = 1

        # Energy outputs
        self.Wdot = self.eta_el * Mdot_fuel * self.LHV
        self.Qdot = self.eta_th * Mdot_fuel * self.LHV
        self.Qdot_gas = self.y * u * self.Qdot
        self.Wdot_el = self.y * u * self.Wdot

        # Safety check
        assert self.T_water_ex_CHP < self.Tmax, "Maximum temperature reached at the CHP outlet"

        return {
            "Wdot_el": self.Wdot_el,
            "Qdot": self.Qdot,
            "T_water_ex_CHP": self.T_water_ex_CHP,
            "eta_el": self.eta_el,
            "eta_th": self.eta_th,
            "y": self.y
        }
