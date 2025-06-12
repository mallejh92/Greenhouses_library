import pandas as pd
import numpy as np
from Components.Greenhouse.Cover import Cover
from Components.Greenhouse.Air import Air
from Components.Greenhouse.Canopy import Canopy
from Components.Greenhouse.Floor import Floor
from Components.Greenhouse.Air_Top import TopAirCompartment
from Components.Greenhouse.Solar_model import Solar_model
from Components.Greenhouse.HeatingPipe import HeatingPipe
from Components.Greenhouse.Illumination import Illumination
from Components.Greenhouse.ThermalScreen import ThermalScreen
from Flows.HeatTransfer.CanopyFreeConvection import CanopyFreeConvection
from Flows.HeatTransfer.FreeConvection import FreeConvection
from Flows.HeatTransfer.OutsideAirConvection import OutsideAirConvection
from Flows.HeatTransfer.Radiation_T4 import Radiation_T4
from Flows.HeatTransfer.Radiation_N import Radiation_N
from Flows.CO2MassTransfer.MC_AirCan import MC_AirCan
from Flows.CO2MassTransfer.CO2_Air import CO2_Air
from Flows.HeatAndVapourTransfer.Ventilation import Ventilation
from ControlSystems.PID import PID
from ControlSystems.Climate.Control_ThScreen import Control_ThScreen
from ControlSystems.Climate.Uvents_RH_T_Mdot import Uvents_RH_T_Mdot
from Components.CropYield.TomatoYieldModel import TomatoYieldModel

class Greenhouse_2:
    """
    Python implementation of the Modelica Greenhouse_1 model with enhancements:
    - Updates tomato yield model each step and records DM_Har
    - Initializes air temperature and CO2 from first weather data row
    - Adds extra outputs (LAI, radiation variables)
    """
    def __init__(self):
        # Main greenhouse floor area [m2]
        self.surface = 1.4e4

        # Instantiate components
        self.cover = Cover(rho=2600, c_p=840, A=self.surface, steadystate=True, h_cov=1e-3, phi=0.43633231299858)
        self.air = Air(A=self.surface, steadystate=True, steadystateVP=True, h_Air=3.8)
        self.canopy = Canopy(A=self.surface, steadystate=True, LAI=1.06)
        self.floor = Floor(rho=1, c_p=2e6, A=self.surface, V=0.01*self.surface, steadystate=True)
        self.illu = Illumination(A=self.surface, power_input=True, P_el=500, p_el=100)
        self.thScreen = ThermalScreen(A=self.surface, SC=0, steadystate=False)
        self.air_top = TopAirCompartment(A=self.surface, steadystate=True, steadystateVP=True, h_Top=0.4)
        self.solar_model = Solar_model(A=self.surface, LAI=1.06, SC=0, I_glob=0)
        self.pipe_low = HeatingPipe(A=self.surface, d=0.051, freePipe=False, N=5, N_p=625, l=50)
        self.pipe_up = HeatingPipe(A=self.surface, freePipe=True, d=0.025, l=44, N=5, N_p=292)
        self.CO2_air = CO2_Air(cap_CO2=3.8)
        self.CO2_top = CO2_Air(cap_CO2=0.4)

        # Control systems
        self.PID_Mdot = PID(PVmin=18+273.15, PVmax=22+273.15, PVstart=0.5,
                            CSstart=0.5, CSmin=0, Kp=0.7, Ti=600, CSmax=86.75)
        self.PID_CO2 = PID(PVstart=0.5, CSstart=0.5, PVmin=708.1,
                           PVmax=1649, CSmin=0, CSmax=1, Kp=0.4, Ti=0.5)
        self.SC = Control_ThScreen(R_Glob_can=0.0, R_Glob_can_min=35)
        self.U_vents = Uvents_RH_T_Mdot()

        # Crop yield model
        self.TYM = TomatoYieldModel(LAI_MAX=2.7, LAI_0=1.06,
                                    C_Leaf_0=40e3, C_Stem_0=30e3)

        # Flows
        self.Q_rad_CanCov = Radiation_T4(A=self.surface, epsilon_a=1,
                                         epsilon_b=0.84, FFa=self.canopy.FF, FFb=1)
        self.Q_cnv_CanAir = CanopyFreeConvection(A=self.surface)
        self.Q_cnv_FlrAir = FreeConvection(phi=0, A=self.surface, floor=True)
        self.Q_rad_CovSky = Radiation_T4(epsilon_a=0.84, epsilon_b=1, A=self.surface)
        self.Q_cnv_CovOut = OutsideAirConvection(A=self.surface, phi=0.43633231299858)
        self.Q_ven_AirOut = Ventilation(A=self.surface, thermalScreen=True, topAir=False)
        self.Q_ven_TopOut = Ventilation(A=self.surface, thermalScreen=True, topAir=True)

        # State variables initialization
        self.q_low = 0.0
        self.q_up = 0.0
        self.q_tot = 0.0
        self.E_th_tot_kWhm2 = 0.0
        self.E_th_tot = 0.0
        self.DM_Har = 0.0
        self.W_el_illu = 0.0
        self.E_el_tot_kWhm2 = 0.0
        self.E_el_tot = 0.0

        # Load weather and setpoint data
        self.weather_df = pd.read_csv("./10Dec-22Nov.txt", delimiter="\t", skiprows=2, header=None)
        self.weather_df.columns = ["time", "T_out", "RH_out", "P_out", "I_glob",
                                   "u_wind", "T_sky", "T_air_sp", "CO2_air_sp", "ilu_sp"]
        self.sp_df = pd.read_csv("./SP_10Dec-22Nov.txt", delimiter="\t", skiprows=2, header=None)
        self.sp_df.columns = ["time", "T_sp", "CO2_sp"]

        # Set initial environmental states
        init_weather = self.weather_df.iloc[0]
        self.air.T = init_weather['T_out'] + 273.15
        self.air.RH = init_weather['RH_out'] / 100.0
        self.CO2_air.CO2 = init_weather['CO2_air_sp']

    def step(self, dt, time_idx):
        """
        Advance the simulation by one time step dt (in seconds).
        :param dt: time step duration [s]
        :param time_idx: index in weather_df and sp_df
        :return: dict of current state variables
        """
        weather = self.weather_df.iloc[time_idx]
        setpoint = self.sp_df.iloc[time_idx]

        self._update_components(dt, weather, setpoint)
        self._update_control_systems(weather, setpoint)
        self._calculate_energy_flows()

        return self._get_state()

    def _update_components(self, dt, weather, setpoint):
        """
        Update component states given current weather and setpoint.
        """
        # Update boundary conditions
        h_Air = 3.8 + (1 - self.thScreen.SC) * 0.4
        self.air.h_Air = h_Air
        self.CO2_air.cap_CO2 = h_Air

        self.air.T_out = weather['T_out'] + 273.15
        self.air.RH_out = weather['RH_out'] / 100.0
        self.solar_model.I_glob = weather['I_glob']
        self.illu.switch = weather['ilu_sp']
        self.illu.step()

        self.Q_ven_AirOut.u = weather['u_wind']
        self.Q_ven_TopOut.u = weather['u_wind']

        self.air.T_set = setpoint['T_sp'] + 273.15
        self.air.CO2_set = setpoint['CO2_sp']

        # Propagate to solar model and components
        self.solar_model.LAI = self.canopy.LAI
        self.solar_model.SC = self.thScreen.SC
        self.solar_model.step(dt)

        # Cover
        self.cover.set_inputs(Q_flow=0.0,
                              R_SunCov_Glob=self.solar_model.R_SunCov_Glob,
                              MV_flow=0.0)
        self.cover.step(dt)

        # Canopy
        self.canopy.set_inputs(Q_flow=0.0,
                               R_Can_Glob=[self.solar_model.R_PAR_Can_umol, 0.0],
                               MV_flow=0.0)
        self.canopy.step(dt)

        # Floor
        self.floor.set_inputs(
            Q_flow=0.0,
            R_Flr_Glob=[
                self.solar_model.R_SunFlr_Glob,
                getattr(self.illu.R_IluFlr_Glob, "value", 0.0),
            ],
        )
        self.floor.step(dt)

        # Air
        Q_flow_air = self.cover.Q_flow + self.canopy.Q_flow + self.floor.Q_flow
        R_Air_Glob = [
            self.solar_model.R_SunAir_Glob,
            getattr(self.illu.R_IluAir_Glob, "value", 0.0),
        ]
        self.air.set_inputs(
            Q_flow=Q_flow_air,
            R_Air_Glob=R_Air_Glob,
            massPort_VP=0.0,
        )
        self.air.step(dt)

        # Pipes and screens
        self.pipe_low.step(dt)
        self.pipe_up.step(dt)
        self.thScreen.step(dt)

        # CO2 and top air
        self.CO2_air.step(dt)
        self.CO2_top.step(dt)
        self.air_top.step(dt)

        # Crop yield model and DM_Har
        self.TYM.simulate(dt)
        self.DM_Har = self.TYM.DM_Har

    def _update_control_systems(self, weather, setpoint):
        """
        Update all control loops.
        """
        # Temperature control
        self.PID_Mdot.PV = self.air.T
        self.PID_Mdot.SP = setpoint['T_sp'] + 273.15
        self.PID_Mdot.compute()

        # CO2 control
        self.PID_CO2.PV = self.CO2_air.CO2
        self.PID_CO2.SP = setpoint['CO2_sp']
        self.PID_CO2.compute()

        # Screen control
        self.SC.R_Glob_can = self.solar_model.I_glob
        self.SC.T_air_sp = setpoint['T_sp'] + 273.15
        self.SC.T_out = weather['T_out'] + 273.15
        self.SC.RH_air = self.air.RH
        self.SC.compute()
        self.thScreen.SC = self.SC.SC

        # Ventilation control
        self.U_vents.T_air = self.air.T
        self.U_vents.T_air_sp = setpoint['T_sp'] + 273.15
        self.U_vents.Mdot = self.PID_Mdot.CS
        self.U_vents.RH_air_input = self.air.RH
        self.U_vents.compute()

    def _calculate_energy_flows(self):
        """
        Compute energy balances for heating and illumination.
        """
        # Heat flux through pipes
        q_low_tot = getattr(self.pipe_low, 'Q_tot', 0.0)
        q_up_tot = getattr(self.pipe_up, 'Q_tot', 0.0)
        self.q_low = -q_low_tot / self.surface
        self.q_up = -q_up_tot / self.surface
        self.q_tot = -(q_low_tot + q_up_tot) / self.surface

        # Cumulative thermal energy [kWh/m2]
        if self.q_tot > 0:
            self.E_th_tot_kWhm2 += self.q_tot * 1e-3 * 3600
        self.E_th_tot = self.E_th_tot_kWhm2 * self.surface

        # Illumination energy
        self.W_el_illu += self.illu.W_el / self.surface
        self.E_el_tot_kWhm2 = self.W_el_illu
        self.E_el_tot = self.E_el_tot_kWhm2 * self.surface

    def _get_state(self):
        """
        Return dictionary of current key state variables.
        """
        return {
            'time': None,
            'T_air': self.air.T - 273.15,
            'RH_air': self.air.RH * 100,
            'T_canopy': self.canopy.T - 273.15,
            'LAI': self.canopy.LAI,
            'R_SunCov_Glob': self.solar_model.R_SunCov_Glob,
            'R_PAR_Can_umol': self.solar_model.R_PAR_Can_umol,
            'q_low': self.q_low,
            'q_up': self.q_up,
            'q_tot': self.q_tot,
            'E_th_tot_kWhm2': self.E_th_tot_kWhm2,
            'E_th_tot': self.E_th_tot,
            'W_el_illu': self.W_el_illu,
            'E_el_tot_kWhm2': self.E_el_tot_kWhm2,
            'E_el_tot': self.E_el_tot,
            'DM_Har': self.DM_Har,
            'CO2_air': self.CO2_air.CO2,
            'SC': self.thScreen.SC,
            'vent_opening': self.U_vents.U_vents
        }
