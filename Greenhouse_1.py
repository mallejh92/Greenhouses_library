import numpy as np
import pandas as pd
from Components.Greenhouse.Cover import Cover
from Components.Greenhouse.Air import Air
from Components.Greenhouse.Canopy import Canopy
from Components.Greenhouse.Floor import Floor
from Components.Greenhouse.Air_Top import TopAirCompartment
from Components.Greenhouse.Solar_model import SolarModel
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

class Greenhouse_1:
    """
    Simulation of a Venlo-type greenhouse for tomato crop cultivated from 10Dec-22Nov
    (weather data from TMY)
    """
    
    def __init__(self):
        # Constants
        self.surface = 1.4e4  # Floor surface area [m²]
        
        # Initialize components
        self.cover = Cover(
            rho=2600,
            c_p=840,
            A=self.surface,
            steadystate=True,
            h_cov=1e-3,
            phi=0.43633231299858
        )
        
        self.air = Air(
            A=self.surface,
            steadystate=True,
            steadystateVP=True,
            h_Air=3.8  # Will be updated dynamically
        )
        
        self.canopy = Canopy(
            A=self.surface,
            steadystate=True,
            LAI=1.06  # Will be updated from weather if available
        )
        
        self.floor = Floor(
            rho=1,
            c_p=2e6,
            A=self.surface,
            V=0.01*self.surface,
            steadystate=True
        )
        
        self.air_top = TopAirCompartment(
            A=self.surface,
            steadystate=True,
            steadystateVP=True,
            h_Top=0.4
        )
        
        self.solar_model = SolarModel(
            A=self.surface,
            LAI=1.06,  # Will be updated from weather if available
            I_glob=0.0  # Initial value, will be updated from weather data
        )
        
        self.pipe_low = HeatingPipe(
            A=self.surface,
            d=0.051,
            freePipe=False,
            N=5,
            N_p=625,
            l=50
        )
        
        self.pipe_up = HeatingPipe(
            A=self.surface,
            freePipe=True,
            d=0.025,
            l=44,
            N=5,
            N_p=292
        )
        
        self.illu = Illumination(
            A=self.surface,
            power_input=True,
            P_el=500,
            p_el=100
        )
        
        self.thScreen = ThermalScreen(
            A=self.surface,
            SC=0,  # Will be updated from control
            steadystate=False
        )

        # Initialize CO2 components
        self.CO2_air = CO2_Air(cap_CO2=3.8)  # Will be updated dynamically
        self.CO2_top = CO2_Air(cap_CO2=0.4)
        
        # Initialize heat transfer components
        self.Q_rad_CanCov = Radiation_T4(
            A=self.surface,
            epsilon_a=1,
            epsilon_b=0.84,
            FFa=self.canopy.FF,
            FFb=1
        )
        
        self.Q_cnv_CanAir = CanopyFreeConvection(A=self.surface)
        self.Q_cnv_FlrAir = FreeConvection(phi=0, A=self.surface, floor=True)
        
        self.Q_rad_CovSky = Radiation_T4(
            epsilon_a=0.84,
            epsilon_b=1,
            A=self.surface
        )
        
        self.Q_cnv_CovOut = OutsideAirConvection(
            A=self.surface,
            phi=0.43633231299858
        )

        # Initialize ventilation components
        self.Q_ven_AirOut = Ventilation(
            A=self.surface,
            thermalScreen=True,
            topAir=False
        )
        
        self.Q_ven_TopOut = Ventilation(
            A=self.surface,
            thermalScreen=True,
            topAir=True
        )

        # Initialize control systems
        self.PID_Mdot = PID(
            PVmin=18 + 273.15,
            PVmax=22 + 273.15,
            PVstart=0.5,
            CSstart=0.5,
            CSmin=0,
            Kp=0.7,
            Ti=600,
            CSmax=86.75
        )

        self.PID_CO2 = PID(
            PVstart=0.5,
            CSstart=0.5,
            PVmin=708.1,
            PVmax=1649,
            CSmin=0,
            CSmax=1,
            Kp=0.4,
            Ti=0.5
        )

        self.SC = Control_ThScreen(
            R_Glob_can=0.0,  # Will be updated from solar model
            R_Glob_can_min=35
        )

        self.U_vents = Uvents_RH_T_Mdot()  # Initialize without parameters
        
        # State variables
        self.q_low = 0.0  # Heat flux from lower pipe [W/m²]
        self.q_up = 0.0   # Heat flux from upper pipe [W/m²]
        self.q_tot = 0.0  # Total heat flux [W/m²]
        
        self.E_th_tot_kWhm2 = 0.0  # Total thermal energy per m² [kW·h/m²]
        self.E_th_tot = 0.0        # Total thermal energy [kW·h]
        
        self.DM_Har = 0.0  # Accumulated harvested tomato dry matter [mg/m²]
        
        self.W_el_illu = 0.0       # Electrical energy for illumination per m² [kW·h/m²]
        self.E_el_tot_kWhm2 = 0.0  # Total electrical energy per m² [kW·h/m²]
        self.E_el_tot = 0.0        # Total electrical energy [kW·h]
        
        # Load weather and setpoint data
        self.weather_df = pd.read_csv("./10Dec-22Nov.txt", 
                                    delimiter="\t", skiprows=2, header=None)
        self.weather_df.columns = ["time", "T_out", "RH_out", "P_out", "I_glob", 
                                 "u_wind", "T_sky", "T_air_sp", "CO2_air_sp", "ilu_sp"]
        
        self.sp_df = pd.read_csv("./SP_10Dec-22Nov.txt",
                                delimiter="\t", skiprows=2, header=None)
        self.sp_df.columns = ["time", "T_sp", "CO2_sp"]
    
    def step(self, dt, time_idx):
        """
        Advance the simulation by one time step
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        time_idx : int
            Index for weather and setpoint data
        
        Returns:
        --------
        dict
            Dictionary containing current state variables
        """
        # Get current weather and setpoint data
        weather = self.weather_df.iloc[time_idx]
        setpoint = self.sp_df.iloc[time_idx]
        
        # Update component states with weather and setpoint
        self._update_components(dt, weather, setpoint)
        
        # Update control systems
        self._update_control_systems(weather, setpoint)
        
        # Calculate energy flows
        self._calculate_energy_flows()
        
        # Print key variables for debugging
        print(f"Step {time_idx}: T_out={weather['T_out']:.2f}°C, RH_out={weather['RH_out']:.2f}%, "
              f"I_glob={weather['I_glob']}, Illu_switch={weather['ilu_sp']}, "
              f"T_set={setpoint['T_sp']:.2f}°C")
        
        # Return current state
        return self._get_state()
        
    def _update_components(self, dt, weather, setpoint):
        """
        Update all component states with weather and setpoint data
        """
        # 1. 외부 환경 및 제어 입력 반영
        h_Air = 3.8 + (1 - self.thScreen.SC) * 0.4
        self.air.h_Air = h_Air
        self.CO2_air.cap_CO2 = h_Air

        self.air.T_out = weather['T_out'] + 273.15
        self.air.RH_out = weather['RH_out'] / 100.0
        self.solar_model.I_glob = weather['I_glob']
        self.illu.switch = weather['ilu_sp']
        self.illu.compute()

        self.Q_ven_AirOut.u = weather['u_wind']
        self.Q_ven_TopOut.u = weather['u_wind']

        self.air.T_set = setpoint['T_sp'] + 273.15
        self.air.CO2_set = setpoint['CO2_sp']

        # 2. SolarModel → Cover, Canopy, Floor 등으로 복사 전달
        self.solar_model.LAI = self.canopy.LAI
        self.solar_model.SC = self.thScreen.SC
        self.solar_model.step(dt)

        # 3. Cover 입력 연결
        self.cover.set_inputs(
            Q_flow=0.0,  # 예시: 실제로는 열전달 모델에서 계산된 값 사용
            R_SunCov_Glob=self.solar_model.R_SunCov_Glob,
            MV_flow=0.0  # 예시: 실제로는 응축 등에서 계산된 값 사용
        )
        self.cover.step(dt)

        # 4. Canopy 입력 연결
        self.canopy.set_inputs(
            Q_flow=0.0,  # 예시: 실제로는 열전달 모델에서 계산된 값 사용
            R_Can_Glob=[self.solar_model.R_PAR_Can_umol, 0.0],  # 예시
            MV_flow=0.0
        )
        self.canopy.step(dt)

        # 5. Floor 입력 연결
        self.floor.set_inputs(
            Q_flow=0.0,  # 예시
            R_Flr_Glob=[self.solar_model.R_SunFlr_Glob, self.illu.P_el]  # 예시
        )
        self.floor.step(dt)

        # 6. Air 입력 연결 (Cover, Canopy, Floor 등에서 온 에너지 합산)
        Q_flow_air = (
            self.cover.Q_flow +
            self.canopy.Q_flow +
            self.floor.Q_flow
            # + 기타 열전달(환기, 파이프 등) 필요시 추가
        )
        R_Air_Glob = [self.solar_model.R_SunAir_Glob, self.illu.P_el]  # 예시
        self.air.set_inputs(
            Q_flow=Q_flow_air,
            R_Air_Glob=R_Air_Glob,
            massPort_VP=0.0  # 예시: 실제로는 수증기 흐름 등 계산
        )
        self.air.step(dt)

        # 7. HeatingPipe, ThermalScreen, CO2 등도 필요시 연결
        self.pipe_low.step(dt)
        self.pipe_up.step(dt)
        self.thScreen.step(dt)
        self.CO2_air.step(dt)
        self.CO2_top.step(dt)
        self.air_top.step(dt)
    
    def _update_control_systems(self, weather, setpoint):
        """
        Update control systems based on current state and setpoints
        """
        # Update PID controllers
        self.PID_Mdot.PV = self.air.T
        self.PID_Mdot.SP = setpoint['T_sp'] + 273.15
        self.PID_Mdot.compute()
        
        self.PID_CO2.PV = self.CO2_air.CO2
        self.PID_CO2.SP = setpoint['CO2_sp']
        self.PID_CO2.compute()
        
        # Update screen control
        self.SC.R_Glob_can = self.solar_model.I_glob
        self.SC.T_air_sp = setpoint['T_sp'] + 273.15
        self.SC.T_out = weather['T_out'] + 273.15
        self.SC.RH_air = self.air.RH
        self.SC.compute()
        
        # Update ventilation control
        self.U_vents.T_air = self.air.T
        self.U_vents.T_air_sp = setpoint['T_sp'] + 273.15
        self.U_vents.Mdot = self.PID_Mdot.CS
        self.U_vents.RH_air_input = self.air.RH
        self.U_vents.compute()
        
        # Update screen state
        self.thScreen.SC = self.SC.SC
    
    def _calculate_energy_flows(self):
        """
        Calculate all energy flows between components
        """
        # Calculate heat fluxes
        self.q_low = -self.pipe_low.Q_tot / self.surface if hasattr(self.pipe_low, 'Q_tot') else 0.0
        self.q_up = -self.pipe_up.Q_tot / self.surface if hasattr(self.pipe_up, 'Q_tot') else 0.0
        self.q_tot = -(getattr(self.pipe_low, 'Q_tot', 0.0) + getattr(self.pipe_up, 'Q_tot', 0.0)) / self.surface
        
        # Update accumulated energies
        if self.q_tot > 0:
            self.E_th_tot_kWhm2 += self.q_tot * 1e-3 * 3600  # Convert to kW·h/m²
        self.E_th_tot = self.E_th_tot_kWhm2 * self.surface
        
        # Update electrical energy
        self.W_el_illu += self.illu.W_el / self.surface
        self.E_el_tot_kWhm2 = self.W_el_illu
        self.E_el_tot = self.E_el_tot_kWhm2 * self.surface
    
    def _get_state(self):
        """
        Get current state variables
        """
        return {
            'q_low': self.q_low,
            'q_up': self.q_up,
            'q_tot': self.q_tot,
            'E_th_tot_kWhm2': self.E_th_tot_kWhm2,
            'E_th_tot': self.E_th_tot,
            'DM_Har': self.DM_Har,
            'W_el_illu': self.W_el_illu,
            'E_el_tot_kWhm2': self.E_el_tot_kWhm2,
            'E_el_tot': self.E_el_tot,
            'T_air': getattr(self.air, 'T', 273.15) - 273.15,  # Convert to Celsius
            'RH_air': getattr(self.air, 'RH', 0.0) * 100,      # Convert to percentage
            'T_canopy': getattr(self.canopy, 'T', 273.15) - 273.15,
            'T_cover': getattr(self.cover, 'T', 273.15) - 273.15,
            'T_floor': getattr(self.floor, 'T', 273.15) - 273.15,
            'CO2_air': getattr(self.CO2_air, 'CO2', 0.0),
            'SC': self.thScreen.SC,
            'vent_opening': self.U_vents.U_vents
        }
