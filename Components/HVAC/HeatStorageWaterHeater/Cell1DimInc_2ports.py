from dataclasses import dataclass

@dataclass
class Cell1DimInc2Ports:
    # Parameters
    Vi: float = 0.005  # Volume of a single cell [m^3]
    Ai: float = 10.0   # Lateral surface of a single cell [m^2]
    A_hx: float = 5.0  # Heat exchange area [m^2]
    Mdotnom: float = 1.0  # Nominal fluid flow rate [kg/s]
    Unom: float = 100.0  # Nominal heat transfer coefficient [W/m2K]
    Unom_hx: float = 100.0  # Nominal HX heat transfer coefficient [W/m2K]
    hstart: float = 1e5  # Start value of enthalpy [J/kg]
    pstart: float = 101325.0  # Start pressure [Pa]
    steadystate: bool = True
    FlowReversal: bool = False

    # States and variables
    h: float = 1e5     # Specific enthalpy [J/kg]
    p: float = 101325  # Pressure [Pa]
    M_dot: float = 1.0  # Mass flow rate [kg/s]
    hnode_su: float = 1e5  # Inlet node enthalpy
    hnode_ex: float = 1e5  # Outlet node enthalpy

    # Calculated properties
    def update(self, h_inflow: float, h_outflow_stream: float, qdot_direct: float, T_wall_hx: float, T_wall_int: float):
        from scipy.constants import pi

        # Compute temperature and density from enthalpy (simplified water properties)
        T = 300  # Placeholder: assume 300 K for simplicity
        rho = 1000  # Placeholder: water density [kg/m3]

        # Update inlet/outlet enthalpies depending on flow direction
        if self.FlowReversal:
            self.hnode_ex = self.h if self.M_dot >= 0 else h_outflow_stream
            self.hnode_su = self.h if self.M_dot <= 0 else h_inflow
        else:
            self.hnode_su = h_inflow
            self.hnode_ex = self.h

        # Simple heat transfer model
        qdot = self.Unom * (T_wall_int - T)  # W/m2
        qdot_hx = self.Unom_hx * (T_wall_hx - T)  # W/m2

        # Energy balance: Vi*rho*dh/dt + Mdot*(h_out - h_in) - A_hx*qdot_hx = Ai*qdot + Q_direct
        dh_dt = (self.Ai * qdot + qdot_direct - self.M_dot * (self.hnode_ex - self.hnode_su) + self.A_hx * qdot_hx) / (self.Vi * rho)

        if not self.steadystate:
            self.h += dh_dt  # integrate enthalpy over time (Euler forward)

        # Save some results
        Q_tot = self.Ai * qdot
        M_tot = self.Vi * rho
        T_out = T

        return {
            "T": T_out,
            "h": self.h,
            "qdot": qdot,
            "qdot_hx": qdot_hx,
            "Q_tot": Q_tot,
            "M_tot": M_tot,
            "dh_dt": dh_dt if not self.steadystate else 0.0
        }
