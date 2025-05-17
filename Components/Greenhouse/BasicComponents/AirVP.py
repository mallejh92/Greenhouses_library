# from Interfaces.Vapour.WaterMassPort import WaterMassPort
# from Flows.Sources.Vapour.PrescribedPressure import PrescribedPressure

# class AirVP:
#     """
#     Greenhouse air vapour pressure by numerical integration of the differential equation of the moisture content.
#     This model applies the mass balance on the moisture content of the air.
#     The water vapour pressure of the air is computed by numerical integration of the differential equation of the moisture content.
#     """
#     def __init__(self, V_air=1e3, VP_start=0.04e5, steadystate=True, T=291):
#         # Parameters
#         self.V_air = V_air              # Air volume [m³]
#         self.VP = VP_start              # Initial vapor pressure [Pa]
#         self.steadystate = steadystate  # Steady state flag
#         self.T = T                      # Air temperature [K]

#         # Constants
#         self.R = 8314                   # Gas constant [J/(kmol·K)]
#         self.M_H = 18e-3                # Molar mass of water vapor [kg/mol]
#         self.MV_flow = 0.0              # Water vapor mass flow rate [kg/s]

#         # Components
#         self.port = WaterMassPort(VP_start)
#         self.prescribed_pressure = PrescribedPressure()
#         self.prescribed_pressure.connect(self.port)

#     def update(self, VP_external=None, dt=1.0):
#         """
#         Update the vapor pressure
#         Args:
#             VP_external: External vapor pressure [Pa]
#             dt: Time step [s]
#         """
#         if VP_external is not None:
#             self.VP = VP_external
#             self.port.VP = VP_external
#         elif not self.steadystate:
#             # (Euler integration 등 필요시)
#             pass
#         # else: VP remains constant

#     def get_vapor_pressure(self):
#         """Get current vapor pressure [Pa]"""
#         return self.VP

#     def get_mv_flow(self):
#         """Get current mass flow rate [kg/s]"""
#         return self.MV_flow

#     def set_mv_flow(self, mv_flow):
#         """Set water vapor mass flow rate [kg/s]"""
#         self.MV_flow = mv_flow
#         self.port.MV_flow = mv_flow

#     def set_prescribed_pressure(self, VP):
#         """Set prescribed pressure [Pa]"""
#         self.prescribed_pressure.set_pressure(VP)

class AirVP:
    def __init__(self, V_air=1e3, VP_start=0.04e5, steadystate=True, T=291):
        self.V_air = V_air
        self.VP = VP_start
        self.steadystate = steadystate
        self.T = T
        self.R = 8314
        self.M_H = 18e-3
        self.MV_flow = 0.0

    def get_vapor_pressure(self):
        return self.VP