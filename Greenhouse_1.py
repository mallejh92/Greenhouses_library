import pandas as pd
import numpy as np
from Components.Greenhouse.Cover import Cover
from Components.Greenhouse.Air import Air
from Components.Greenhouse.Canopy import Canopy
from Components.Greenhouse.Floor import Floor
from Components.Greenhouse.Air_Top import Air_Top
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
from Flows.HeatAndVapourTransfer.AirThroughScreen import AirThroughScreen
from ControlSystems.PID import PID
from ControlSystems.Climate.Control_ThScreen import Control_ThScreen
from ControlSystems.Climate.Uvents_RH_T_Mdot import Uvents_RH_T_Mdot
from Components.CropYield.TomatoYieldModel import TomatoYieldModel
from Flows.HeatTransfer.PipeFreeConvection_N import PipeFreeConvection_N
from Flows.CO2MassTransfer.MC_ventilation2 import MC_ventilation2
from Flows.HeatAndVapourTransfer.Convection_Condensation import Convection_Condensation
from Flows.HeatAndVapourTransfer.Convection_Evaporation import Convection_Evaporation
from Flows.VapourMassTransfer.MV_CanopyTranspiration import MV_CanopyTranspiration
from Flows.HeatTransfer.SoilConduction import SoilConduction
from Flows.FluidFlow.Reservoirs.SourceMdot import SourceMdot
from Flows.FluidFlow.Reservoirs.SinkP import SinkP
from Flows.Sensors.RHSensor import RHSensor

class CombiTimeTable:
    """
    Python version of Modelica.Blocks.Sources.CombiTimeTable
    """
    def __init__(self, tableOnFile=True, tableName="tab", columns=None, fileName=None):
        self.tableOnFile = tableOnFile
        self.tableName = tableName
        self.columns = columns
        self.fileName = fileName
        self.data = None
        self.load_data()
        
    def load_data(self):
        """Load data from file"""
        if self.tableOnFile and self.fileName:
            try:
                # 데이터 파일 로드
                self.data = pd.read_csv(self.fileName, 
                                      delimiter="\t", 
                                      skiprows=2, 
                                      header=None)
                
                # 컬럼 이름 설정
                if self.columns:
                    self.data.columns = self.columns
                    
            except Exception as e:
                print(f"데이터 로드 중 오류 발생: {e}")
                raise
                
    def get_value(self, time, interpolate=False):
        """
        time: 실수형 시간(예: 0.0, 1.5, ...)
        interpolate: True면 시간축 보간, False면 인덱스 기반
        """
        if not interpolate:
            idx = int(time)
            if self.data is not None and idx < len(self.data):
                return self.data.iloc[idx]
            return None
        else:
            if self.data is not None:
                times = self.data['time'].values
                result = {}
                for col in self.data.columns:
                    if col == 'time':
                        result[col] = time
                    else:
                        result[col] = float(np.interp(time, times, self.data[col].values))
                return result
            return None

class TemperatureSensor:
    def __init__(self, target, attr='T'):
        self.target = target
        self.attr = attr
    @property
    def T(self):
        return getattr(self.target, self.attr, None)

class Greenhouse_1:
    """
    Simulation of a Venlo-type greenhouse for tomato crop cultivated from 10Dec-22Nov
    (weather data from TMY)
    """
    
    def __init__(self, time_unit_scaling=1.0):
        """
        time_unit_scaling: CombiTimeTable의 time 컬럼 단위(초=1, 시간=3600 등)에 맞춰 보간 시간 변환
        """
        # Constants
        self.surface = 1.4e4  # Floor surface area [m²]
        
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

        # CO2 injection parameters
        self.phi_ExtCO2 = 27  # External CO2 injection rate [mg/(m²·s)]

        # Initialize CombiTimeTables
        self.TMY_and_control = CombiTimeTable(
            tableOnFile=True,
            tableName="tab",
            columns=["time", "T_out", "RH_out", "P_out", "I_glob", 
                    "u_wind", "T_sky", "T_air_sp", "CO2_air_sp", "ilu_sp"],
            fileName="./10Dec-22Nov.txt"
        )
        
        self.SP_new = CombiTimeTable(
            tableOnFile=True,
            tableName="tab",
            columns=["time", "T_sp", "CO2_sp"],
            fileName="./SP_10Dec-22Nov.txt"
        )
        
        self.SC_usable = CombiTimeTable(
            tableOnFile=True,
            tableName="tab",
            columns=["time", "SC_usable"],
            fileName="./SC_usable_10Dec-22Nov.txt"
        )

        # # Load initial setpoint values
        # initial_setpoint = self.SP_new.get_value(0, interpolate=False)
        # T_sp = initial_setpoint['T_sp'] if initial_setpoint else 20.0
        # CO2_sp = initial_setpoint['CO2_sp'] if initial_setpoint else 400.0
        
        # Initialize components with stable initial conditions
        self.cover = Cover(
            rho=2600,
            c_p=840,
            A=self.surface,
            steadystate=True,  # 빠르게 평형을 이루는 체계
            h_cov=1e-3,
            phi=0.43633231299858
        )
        
        # # Get initial weather data
        # initial_weather = self.TMY_and_control.get_value(0, interpolate=False)
        # T_out = initial_weather['T_out'] if initial_weather else 5.0
        
        self.air = Air(
            A=self.surface,
            steadystate=True,  # 빠르게 평형을 이루는 체계
            steadystateVP=True,  # 수증기도 빠르게 평형을 이룸
            h_Air=3.8  # 초기값 설정
        )
        
        self.canopy = Canopy(
            A=self.surface,
            steadystate=True,  # 빠르게 평형을 이루는 체계
            LAI=1.06
        )
        
        self.floor = Floor(
            rho=1,
            c_p=2e6,
            A=self.surface,
            V=0.01*self.surface,
            steadystate=True  # 빠르게 평형을 이루는 체계
        )
        
        self.air_top = Air_Top(
            A=self.surface,
            steadystate=True,  # 빠르게 평형을 이루는 체계
            steadystateVP=True,  # 수증기도 빠르게 평형을 이룸
            h_Top=0.4
        )
        
        self.solar_model = Solar_model(
            A=self.surface,
            LAI=1.06,
            I_glob=0.0
        )
        
        self.pipe_low = HeatingPipe(
            A=self.surface,
            d=0.051,
            freePipe=False,
            N=5,
            N_p=625,
            l=50,
            Mdotnom=0.528
        )
        
        self.pipe_up = HeatingPipe(
            A=self.surface,
            freePipe=True,
            d=0.025,
            l=44,
            N=5,
            N_p=292,
            Mdotnom=0.528
        )
        
        self.illu = Illumination(
            A=self.surface,
            power_input=True,
            P_el=500,
            p_el=100
        )
        
        self.thScreen = ThermalScreen(
            A=self.surface,
            SC=0,
            steadystate=False  # 스크린 전개/접힘이 동적 상태 전이에 의존
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
        
        self.Q_ven_AirTop = AirThroughScreen(
            A=self.surface,
            K=0.2e-3,
            SC=self.thScreen.SC,
            W=9.6
        )
        
        # Connect ventilation ports
        # Q_ven_AirOut
        self.Q_ven_AirOut.HeatPort_a.T = self.air.heatPort.T
        self.Q_ven_AirOut.HeatPort_b.T = self.air.T
        self.Q_ven_AirOut.MassPort_a.VP = self.air.massPort.VP
        self.Q_ven_AirOut.MassPort_b.VP = self.air.VP
        self.Q_ven_AirOut.MassPort_a.P = self.air.massPort.P
        self.Q_ven_AirOut.MassPort_b.P = self.air.P_Air
        
        # Q_ven_TopOut
        self.Q_ven_TopOut.HeatPort_a.T = self.air_top.heatPort.T
        self.Q_ven_TopOut.HeatPort_b.T = self.air.T
        self.Q_ven_TopOut.MassPort_a.VP = self.air_top.massPort.VP
        self.Q_ven_TopOut.MassPort_b.VP = self.air.VP
        self.Q_ven_TopOut.MassPort_a.P = self.air_top.massPort.P
        self.Q_ven_TopOut.MassPort_b.P = self.air.P_Air
        
        # Q_ven_AirTop
        self.Q_ven_AirTop.HeatPort_a.T = self.air.heatPort.T
        self.Q_ven_AirTop.HeatPort_b.T = self.air_top.heatPort.T
        self.Q_ven_AirTop.MassPort_a.VP = self.air.massPort.VP
        self.Q_ven_AirTop.MassPort_b.VP = self.air_top.massPort.VP
        self.Q_ven_AirTop.MassPort_a.P = self.air.massPort.P
        self.Q_ven_AirTop.MassPort_b.P = self.air_top.massPort.P

        # Initialize CO2 components
        self.CO2_air = CO2_Air(cap_CO2=3.8)
        self.CO2_top = CO2_Air(cap_CO2=0.4)
        
        # Initialize MC_AirCan for CO2 exchange between air and canopy
        self.MC_AirCan = MC_AirCan(MC_AirCan=0.0)
        
        # Initialize CO2 exchange components
        self.MC_AirTop = MC_ventilation2(f_vent=self.Q_ven_AirTop.f_AirTop)
        self.MC_AirOut = MC_ventilation2(f_vent=self.Q_ven_AirOut.f_vent_total)
        self.MC_TopOut = MC_ventilation2(f_vent=self.Q_ven_TopOut.f_vent_total)

        # Initialize heat transfer components
        self.Q_rad_CanCov = Radiation_T4(
            A=self.surface,
            epsilon_a=1,
            epsilon_b=0.84,
            FFa=self.canopy.FF,
            FFb=1
        )
        
        self.Q_cnv_CanAir = CanopyFreeConvection(A=self.surface, LAI=self.canopy.LAI)
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

        # Initialize pipe heat transfer components
        self.Q_cnv_LowAir = PipeFreeConvection_N(
            A=self.surface,
            d=self.pipe_low.d,
            freePipe=False,
            N_p=self.pipe_low.N_p,
            l=self.pipe_low.l,
            N=self.pipe_low.N
        )

        self.Q_rad_LowScr = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=1,
            N=self.pipe_low.N
        )
        self.Q_rad_LowScr.FFa = self.pipe_low.FF
        self.Q_rad_LowScr.FFb = self.thScreen.FF_i
        self.Q_rad_LowScr.FFab1 = self.canopy.FF
        self.Q_rad_LowScr.FFab2 = self.pipe_up.FF

        self.Q_rad_LowFlr = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=0.89,
            N=self.pipe_low.N
        )
        self.Q_rad_LowFlr.FFa = self.pipe_low.FF
        self.Q_rad_LowFlr.FFb = 1

        self.Q_rad_LowCan = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=1,
            N=self.pipe_low.N
        )
        self.Q_rad_LowCan.FFa = self.pipe_low.FF
        self.Q_rad_LowCan.FFb = self.canopy.FF

        self.Q_rad_LowCov = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=0.84,
            N=self.pipe_low.N
        )
        self.Q_rad_LowCov.FFa = self.pipe_low.FF
        self.Q_rad_LowCov.FFb = 1
        self.Q_rad_LowCov.FFab1 = self.canopy.FF
        self.Q_rad_LowCov.FFab2 = self.pipe_up.FF
        self.Q_rad_LowCov.FFab3 = self.thScreen.FF_ij

        # Initialize additional heat transfer components
        self.Q_rad_FlrCan = Radiation_T4(
            A=self.surface,
            epsilon_a=0.89,
            epsilon_b=1,
            FFa=1,
            FFb=self.canopy.FF,
            FFab1=self.pipe_low.FF
        )

        self.Q_rad_FlrCov = Radiation_T4(
            A=self.surface,
            epsilon_a=0.89,
            epsilon_b=0.84,
            FFa=1,
            FFb=1,
            FFab1=self.pipe_low.FF,
            FFab2=self.canopy.FF,
            FFab3=self.pipe_up.FF,
            FFab4=self.thScreen.FF_ij
        )

        self.Q_rad_CanScr = Radiation_T4(
            A=self.surface,
            epsilon_a=1,
            epsilon_b=1,
            FFa=self.canopy.FF,
            FFb=self.thScreen.FF_i,
            FFab1=self.pipe_up.FF
        )

        self.Q_rad_FlrScr = Radiation_T4(
            A=self.surface,
            epsilon_a=0.89,
            epsilon_b=1,
            FFa=1,
            FFb=self.thScreen.FF_i,
            FFab1=self.canopy.FF,
            FFab2=self.pipe_up.FF,
            FFab3=self.pipe_low.FF
        )

        self.Q_rad_ScrCov = Radiation_T4(
            A=self.surface,
            epsilon_a=1,
            epsilon_b=0.84,
            FFa=self.thScreen.FF_i,
            FFb=1
        )

        # Initialize convection and evaporation components
        self.Q_cnv_AirScr = Convection_Condensation(
            A=self.surface,
            phi=0,
            floor=False,
            thermalScreen=True,
            Air_Cov=False,
            SC=self.thScreen.SC
        )
        
        self.Q_cnv_AirCov = Convection_Condensation(
            A=self.surface,
            floor=False,
            thermalScreen=True,
            Air_Cov=True,
            topAir=False,
            SC=self.thScreen.SC,
            phi=0.43633231299858
        )
        
        self.Q_cnv_TopCov = Convection_Condensation(
            A=self.surface,
            floor=False,
            thermalScreen=True,
            Air_Cov=True,
            topAir=True,
            SC=self.thScreen.SC,
            phi=0.43633231299858
        )
        
        self.Q_cnv_ScrTop = Convection_Evaporation(
            A=self.surface,
            SC=self.thScreen.SC
        )

        # Connect ports for convection components
        # Q_cnv_AirScr
        self.Q_cnv_AirScr.heatPort_a.T = self.air.heatPort.T
        self.Q_cnv_AirScr.heatPort_b.T = self.thScreen.heatPort.T
        
        # Q_cnv_AirCov
        self.Q_cnv_AirCov.heatPort_a.T = self.air.heatPort.T
        self.Q_cnv_AirCov.heatPort_b.T = self.cover.heatPort.T
        
        # Q_cnv_TopCov
        self.Q_cnv_TopCov.heatPort_a.T = self.air_top.heatPort.T
        self.Q_cnv_TopCov.heatPort_b.T = self.cover.heatPort.T
        
        # Q_cnv_ScrTop
        self.Q_cnv_ScrTop.heatPort_a.T = self.thScreen.heatPort.T
        self.Q_cnv_ScrTop.heatPort_b.T = self.air_top.heatPort.T

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
            R_Glob_can=0.0,
            R_Glob_can_min=35
        )

        self.U_vents = Uvents_RH_T_Mdot()
        
        # Load weather and setpoint data
        try:
            self.weather_df = pd.read_csv("./10Dec-22Nov.txt", 
                                        delimiter="\t", skiprows=2, header=None)
            self.weather_df.columns = ["time", "T_out", "RH_out", "P_out", "I_glob", 
                                     "u_wind", "T_sky", "T_air_sp", "CO2_air_sp", "ilu_sp"]
            
            self.sp_df = pd.read_csv("./SP_10Dec-22Nov.txt",
                                    delimiter="\t", skiprows=2, header=None)
            self.sp_df.columns = ["time", "T_sp", "CO2_sp"]
            
            # # Debug information for data loading
            # print("\n=== Data Loading Check ===")
            # print("\nWeather data sample:")
            # print(self.weather_df.head())
            # print("\nSetpoint data sample:")
            # print(self.sp_df.head())
            # print("\nWeather data size:", self.weather_df.shape)
            # print("Setpoint data size:", self.sp_df.shape)
            
        except Exception as e:
            print(f"Error during data loading: {e}")
            raise
        
        # Initialize TomatoYieldModel
        self.TYM = TomatoYieldModel(
            n_dev=50,
            LAI_MAX=3.5,
            LAI_0=1.06,
            T_canSumC_0=0,
            C_Leaf_0=40e3,
            C_Stem_0=30e3
        )
        
        # Initialize mass vapor transfer component (canopy transpiration)
        self.MV_CanAir = MV_CanopyTranspiration(A=self.surface)
        
        # SoilConduction 인스턴스 생성 (2층 콘크리트, 5층 토양)
        self.Q_cd_Soil = SoilConduction(
            A=self.surface,
            N_c=2,
            N_s=5,
            lambda_c=1.7,
            lambda_s=0.85,
            steadystate=False  # 토양은 열용량이 크고 수시간에 걸쳐 온도가 변하는 축열체
        )
        # floor와 soil conduction 포트 연결
        self.Q_cd_Soil.port_a = self.floor.heatPort
        # port_b를 지중 온도(예: 외기 온도 또는 고정값)와 연결
        self.Q_cd_Soil.port_b = type('SoilTempPort', (), {'T': 283.15})()  # 예시: 10°C 고정
        
        # Source/Sink (난방수 공급/배출) 생성
        self.sourceMdot_1ry = SourceMdot(Mdot_0=0.528, T_0=363.15)  # 90°C
        self.sinkP_2ry = SinkP(p0=1e5)  # 1 bar
        # 파이프 입출구 연결
        self.pipe_low.flow1DimInc.InFlow = self.sourceMdot_1ry.flangeB
        self.pipe_up.flow1DimInc.OutFlow = self.sinkP_2ry.flangeB
        
        # Connect all heat ports
        self._connect_heat_ports()
        
        # Set initial environmental conditions
        self.TYM.set_environmental_conditions(
            R_PAR_can=self.solar_model.R_PAR_Can_umol + self.illu.R_PAR_Can_umol if hasattr(self.illu, 'R_PAR_Can_umol') else 0,
            CO2_air=self.CO2_air.CO2_ppm if hasattr(self, 'CO2_air') else 0,
            T_canK=self.canopy.T if hasattr(self.canopy, 'T') else 293.15
        )

        # 센서 객체 생성
        self.RH_air_sensor = RHSensor()
        self.RH_out_sensor = RHSensor()
        self.Tair_sensor = TemperatureSensor(self.air)
        self.Tcover_sensor = TemperatureSensor(self.cover)
        self.Tfloor_sensor = TemperatureSensor(self.floor)
        self.Tcanopy_sensor = TemperatureSensor(self.canopy)
        # PrescribedTemperature/Pressure 역할 변수
        self.T_sky = None
        self.VP_out = None
        self.time_unit_scaling = time_unit_scaling  # 예: 데이터가 시간(h) 단위면 1, 초(s) 단위면 3600
    
    def _connect_heat_ports(self):
        """
        Connect all heat ports between components
        """
        # Connect radiation components
        # Q_rad_FlrCan (Floor to Canopy)
        self.Q_rad_FlrCan.heatPort_a.T = self.floor.heatPort.T
        self.Q_rad_FlrCan.heatPort_b.T = self.canopy.heatPort.T
        # Q_rad_FlrCov (Floor to Cover)
        self.Q_rad_FlrCov.heatPort_a.T = self.floor.heatPort.T
        self.Q_rad_FlrCov.heatPort_b.T = self.cover.heatPort.T
        # Q_rad_CanScr (Canopy to Screen)
        self.Q_rad_CanScr.heatPort_a.T = self.canopy.heatPort.T
        self.Q_rad_CanScr.heatPort_b.T = self.thScreen.heatPort.T
        # Q_rad_FlrScr (Floor to Screen)
        self.Q_rad_FlrScr.heatPort_a.T = self.floor.heatPort.T
        self.Q_rad_FlrScr.heatPort_b.T = self.thScreen.heatPort.T
        # Q_rad_ScrCov (Screen to Cover)
        self.Q_rad_ScrCov.heatPort_a.T = self.thScreen.heatPort.T
        self.Q_rad_ScrCov.heatPort_b.T = self.cover.heatPort.T
        # Q_rad_CanCov (Canopy to Cover)
        self.Q_rad_CanCov.heatPort_a.T = self.canopy.heatPort.T
        self.Q_rad_CanCov.heatPort_b.T = self.cover.heatPort.T
        # Q_rad_CovSky (Cover to Sky)
        self.Q_rad_CovSky.heatPort_a.T = self.cover.heatPort.T
        self.Q_rad_CovSky.heatPort_b.T = self.air.T
        # Connect convection components
        self.Q_cnv_CanAir.heatPort_a.T = self.canopy.heatPort.T
        self.Q_cnv_CanAir.heatPort_b.T = self.air.heatPort.T
        self.Q_cnv_FlrAir.heatPort_a.T = self.floor.heatPort.T
        self.Q_cnv_FlrAir.heatPort_b.T = self.air.heatPort.T
        self.Q_cnv_CovOut.heatPort_a.T = self.cover.heatPort.T
        self.Q_cnv_CovOut.heatPort_b.T = self.air.T
        self.Q_cnv_AirScr.heatPort_a.T = self.air.heatPort.T
        self.Q_cnv_AirScr.heatPort_b.T = self.thScreen.heatPort.T
        self.Q_cnv_AirCov.heatPort_a.T = self.air.heatPort.T
        self.Q_cnv_AirCov.heatPort_b.T = self.cover.heatPort.T
        self.Q_cnv_TopCov.heatPort_a.T = self.air_top.heatPort.T
        self.Q_cnv_TopCov.heatPort_b.T = self.cover.heatPort.T
        self.Q_cnv_ScrTop.heatPort_a.T = self.thScreen.heatPort.T
        self.Q_cnv_ScrTop.heatPort_b.T = self.air_top.heatPort.T
        # MassPort connections (vapor/gas)
        self.MV_CanAir.massPort_a.VP = self.canopy.massPort.VP
        self.MV_CanAir.massPort_b.VP = self.air.massPort.VP
        self.Q_cnv_AirScr.massPort_a.VP = self.air.massPort.VP
        self.Q_cnv_AirScr.massPort_b.VP = self.thScreen.massPort.VP
        self.Q_cnv_AirCov.massPort_a.VP = self.air.massPort.VP
        self.Q_cnv_AirCov.massPort_b.VP = self.cover.massPort.VP
        self.Q_cnv_TopCov.massPort_a.VP = self.air_top.massPort.VP
        self.Q_cnv_TopCov.massPort_b.VP = self.cover.massPort.VP
        self.Q_cnv_ScrTop.massPort_a.VP = self.thScreen.massPort.VP
        self.Q_cnv_ScrTop.massPort_b.VP = self.air_top.massPort.VP
        # ... 기존 코드 ...
    
    def step(self, dt, time_idx):
        """
        Advance the simulation by one time step
        dt: 시뮬레이션 시간 간격(초)
        time_idx: 현재 스텝 인덱스
        """
        try:
            # CombiTimeTable의 time 컬럼 단위에 맞춰 시간 변환
            current_time = time_idx * dt
            
            # 디버깅: 초기 상태 출력
            print(f"\n=== Step {time_idx} 시작 (t={current_time/3600:.2f}h) ===")
            print(f"초기 상태:")
            print(f"Air: T={self.air.T-273.15:.2f}°C, RH={self.air.RH*100:.1f}%, VP={self.air.massPort.VP:.1f} Pa")
            print(f"Cover: T={self.cover.T-273.15:.2f}°C")
            print(f"Canopy: T={self.canopy.T-273.15:.2f}°C")
            print(f"Floor: T={self.floor.T-273.15:.2f}°C")
            print(f"Air_Top: T={self.air_top.T-273.15:.2f}°C, VP={self.air_top.massPort.VP:.1f} Pa")
            
            # 보간된 weather_data 사용
            weather = self.TMY_and_control.get_value(current_time, interpolate=True)
            if weather is None:
                weather = self.TMY_and_control.get_value(len(self.TMY_and_control.data)-1)

            setpoint = self.SP_new.get_value(current_time, interpolate=True)
            if setpoint is None:
                setpoint = self.SP_new.get_value(len(self.SP_new.data)-1)

            sc_usable = self.SC_usable.get_value(current_time, interpolate=True)
            if sc_usable is None:
                sc_usable = self.SC_usable.get_value(len(self.SC_usable.data)-1)

            # PrescribedTemperature/Pressure 역할 값 할당
            self.T_sky = weather['T_sky'] + 273.15
            T_out_K = weather['T_out'] + 273.15
            RH_out = weather['RH_out'] / 100.0
            VP_sat = 610.78 * np.exp((17.269 * (weather['T_out'])) / (weather['T_out'] + 237.3))
            self.VP_out = RH_out * VP_sat

            # 디버깅: 외부 조건 출력
            print(f"\n외부 조건:")
            print(f"T_out={weather['T_out']:.2f}°C, RH_out={weather['RH_out']:.1f}%, VP_out={self.VP_out:.1f} Pa")
            print(f"T_sky={self.T_sky-273.15:.2f}°C")

            # 외기 RH 센서 입력 연결
            self.RH_out_sensor.massPort.VP = self.VP_out
            self.RH_out_sensor.heatPort.T = T_out_K
            self.RH_out_sensor.calculate()

            # 내부 RH 센서 입력 연결
            self.RH_air_sensor.massPort.VP = getattr(self.air.massPort, 'VP', 0.0)
            self.RH_air_sensor.heatPort.T = getattr(self.air.heatPort, 'T', 273.15)
            self.RH_air_sensor.calculate()

            # 보간된 조명 제어 신호 사용
            self.illu.switch = weather['ilu_sp']

            # 기존 컴포넌트 업데이트 및 제어
            self._update_components(dt, weather, setpoint)
            
            # 디버깅: 컴포넌트 업데이트 후 상태 출력
            print(f"\n컴포넌트 업데이트 후:")
            print(f"Air: T={self.air.T-273.15:.2f}°C, RH={self.air.RH*100:.1f}%, VP={self.air.massPort.VP:.1f} Pa")
            print(f"Cover: T={self.cover.T-273.15:.2f}°C")
            print(f"Canopy: T={self.canopy.T-273.15:.2f}°C")
            print(f"Floor: T={self.floor.T-273.15:.2f}°C")
            print(f"Air_Top: T={self.air_top.T-273.15:.2f}°C, VP={self.air_top.massPort.VP:.1f} Pa")
            
            self._update_control_systems(weather, setpoint, sc_usable)
            
            # 디버깅: 제어 시스템 상태 출력
            print(f"\n제어 시스템 상태:")
            print(f"PID_Mdot: PV={self.PID_Mdot.PV-273.15:.2f}°C, SP={self.PID_Mdot.SP-273.15:.2f}°C, CS={self.PID_Mdot.CS:.3f}")
            print(f"PID_CO2: PV={self.PID_CO2.PV:.1f} ppm, SP={self.PID_CO2.SP:.1f} ppm, CS={self.PID_CO2.CS:.3f}")
            print(f"SC: {self.SC.SC:.2f}, U_vents: {self.U_vents.U_vents:.2f}")
            
            self._calculate_energy_flows(dt)
            self.DM_Har = self.TYM.DM_Har  # 누적 수확 건물질 업데이트

            # 디버깅: 에너지 흐름 출력
            print(f"\n에너지 흐름:")
            print(f"q_tot={self.q_tot:.1f} W/m², E_th={self.E_th_tot_kWhm2:.2f} kWh/m²")
            print(f"Q_rad_CanCov={self.Q_rad_CanCov.Q_flow:.1f} W")
            print(f"Q_cnv_CanAir={self.Q_cnv_CanAir.Q_flow:.1f} W")
            print(f"Q_cnv_FlrAir={self.Q_cnv_FlrAir.Q_flow:.1f} W")

            return self._get_state()
        except Exception as e:
            print(f"Step {time_idx} 실행 중 오류 발생: {e}")
            raise
        
    def _update_components(self, dt, weather, setpoint):
        """
        Update all component states with weather and setpoint data
        - 환기 컴포넌트의 MassPort 연결을 매 스텝마다 갱신
        - U_vents.U_vents: 환기구 개방률(0~1, PID 등 제어 결과)
        """
        # 0. Source/Sink 업데이트 (파이프보다 먼저)
        self.sourceMdot_1ry.in_Mdot = self.PID_Mdot.CS  # PID 제어 결과로 유량 입력
        self.sourceMdot_1ry.step()
        self.sinkP_2ry.step()

        # 1. Update external environment and control inputs
        self.air.h_Air = 3.8 + (1 - self.thScreen.SC) * 0.4
        self.CO2_air.cap_CO2 = self.air.h_Air

        self.air.T_out = weather['T_out'] + 273.15
        self.air.RH_out = weather['RH_out'] / 100.0
        self.solar_model.I_glob = weather['I_glob']
        self.illu.step()

        # 환기 제어 업데이트
        self.Q_ven_AirOut.u = weather['u_wind']
        self.Q_ven_TopOut.u = weather['u_wind']
        self.Q_ven_AirOut.SC = self.thScreen.SC
        self.Q_ven_TopOut.SC = self.thScreen.SC
        self.Q_ven_AirOut.U_vents = self.U_vents.U_vents
        self.Q_ven_TopOut.U_vents = self.U_vents.U_vents

        # 스크린 관련 업데이트
        self.Q_ven_AirTop.SC = self.thScreen.SC
        self.Q_cnv_AirScr.SC = self.thScreen.SC
        self.Q_cnv_AirCov.SC = self.thScreen.SC
        self.Q_cnv_TopCov.SC = self.thScreen.SC
        self.Q_cnv_ScrTop.SC = self.thScreen.SC

        self.air.T_set = setpoint['T_sp'] + 273.15
        self.air.CO2_set = setpoint['CO2_sp']

        # 2. Update pipe components
        self.pipe_low.step(dt)
        self.pipe_up.step(dt)

        # 3. Update solar model and transfer to components
        self.solar_model.LAI = self.canopy.LAI
        self.solar_model.SC = self.thScreen.SC
        self.solar_model.step(dt)
        
        # Update CanopyFreeConvection LAI
        self.Q_cnv_CanAir.LAI = self.canopy.LAI

        # 4. Update all port connections first
        self._update_port_connections()

        # 5. Update CO2 exchange components
        # Update ventilation flow rates
        self.MC_AirTop.f_vent = self.Q_ven_AirTop.f_AirTop
        self.MC_AirOut.f_vent = self.Q_ven_AirOut.f_vent_total
        self.MC_TopOut.f_vent = self.Q_ven_TopOut.f_vent_total
        
        # Update CO2 exchange between air and canopy
        self.MC_AirCan.step(MC_AirCan=self.TYM.MC_AirCan_mgCO2m2s)
        
        # Step all CO2 components
        self.MC_AirCan.step(dt)
        self.MC_AirTop.step(dt)
        self.MC_AirOut.step(dt)
        self.MC_TopOut.step(dt)
        
        # Update CO2 concentrations with external injection
        self.CO2_air.CO2_flow = self.phi_ExtCO2  # Direct CO2 injection
        self.CO2_air.step(dt)
        self.CO2_top.step(dt)

        # 6. Update heat transfer components
        # Update radiation components
        self.Q_rad_CanCov.step(dt)
        self.Q_rad_FlrCan.step(dt)
        self.Q_rad_FlrCov.step(dt)
        self.Q_rad_CanScr.step(dt)
        self.Q_rad_FlrScr.step(dt)
        self.Q_rad_ScrCov.step(dt)
        self.Q_rad_CovSky.step(dt)
        
        # Update convection components
        self.Q_cnv_CanAir.step(dt)
        self.Q_cnv_FlrAir.step(dt)
        self.Q_cnv_CovOut.step(dt)
        self.Q_cnv_AirScr.step(dt)
        self.Q_cnv_AirCov.step(dt)
        self.Q_cnv_TopCov.step(dt)
        self.Q_cnv_ScrTop.step(dt)

        # 7. Update mass vapor transfer components
        self.MV_CanAir.step()
        
        # Update Q_cnv_ScrTop with MV_AirScr
        self.Q_cnv_ScrTop.MV_AirScr = self.Q_cnv_AirScr.MV_flow
        self.Q_cnv_ScrTop.step(dt)

        # 8. Update cover inputs with actual heat flows
        self.cover.set_inputs(
            Q_flow=self.Q_rad_CanCov.Q_flow + self.Q_rad_FlrCov.Q_flow + 
                   self.Q_rad_ScrCov.Q_flow + self.Q_cnv_AirCov.Q_flow + 
                   self.Q_cnv_TopCov.Q_flow + self.Q_cnv_CovOut.Q_flow,
            R_SunCov_Glob=self.solar_model.R_SunCov_Glob
        )
        self.cover.step(dt)

        # 9. Update canopy inputs with actual heat flows
        self.canopy.set_inputs(
            Q_flow=self.Q_rad_CanCov.Q_flow + self.Q_rad_FlrCan.Q_flow + 
                   self.Q_rad_CanScr.Q_flow + self.Q_cnv_CanAir.Q_flow,
            R_Can_Glob=[self.solar_model.R_PAR_Can_umol, self.illu.R_PAR_Can_umol]
        )
        self.canopy.step(dt)

        # 10. Update floor inputs with actual heat flows
        self.floor.set_inputs(
            Q_flow=self.Q_rad_FlrCan.Q_flow + self.Q_rad_FlrCov.Q_flow + 
                   self.Q_rad_FlrScr.Q_flow + self.Q_cnv_FlrAir.Q_flow,
            R_Flr_Glob=[self.solar_model.R_SunFlr_Glob, self.illu.P_el]
        )
        self.floor.step(dt)

        # 11. Update air inputs with actual heat flows
        Q_flow_air = (
            self.Q_cnv_CanAir.Q_flow +
            self.Q_cnv_FlrAir.Q_flow +
            self.Q_cnv_AirScr.Q_flow +
            self.Q_cnv_AirCov.Q_flow +
            self.Q_ven_AirOut.Q_flow +
            self.Q_ven_AirTop.Q_flow
        )
        R_Air_Glob = [self.solar_model.R_SunAir_Glob, self.illu.P_el]
        
        # Update air inputs with all vapor flows (Modelica와 동일하게 모든 MV_flow 합산)
        self.air.set_inputs(
            Q_flow=Q_flow_air,
            R_Air_Glob=R_Air_Glob,
            massPort_VP=(
                self.MV_CanAir.MV_flow +
                self.Q_ven_AirOut.MV_flow +
                self.Q_ven_AirTop.MV_flow +
                self.Q_cnv_AirScr.MV_flow +
                self.Q_cnv_AirCov.MV_flow +
                self.Q_cnv_TopCov.MV_flow +
                self.Q_cnv_ScrTop.MV_flow
            )
        )
        self.air.step(dt)

        # 12. Update remaining components
        self.thScreen.step(dt)
        self.CO2_air.step(dt)
        self.CO2_top.step(dt)
        self.air_top.step(dt)

        # SoilConduction: 매 스텝마다 지면 온도(외기)를 반영
        self.Q_cd_Soil.port_b.T = weather['T_out'] + 273.15 if 'T_out' in weather else 283.15
        # 1) 상태 갱신
        if hasattr(self.Q_cd_Soil, 'step'):
            self.Q_cd_Soil.step(dt)
            Q_flow_soil = getattr(self.Q_cd_Soil, 'Q_flow', 0.0)
        else:
            Q_flow_soil = self.Q_cd_Soil.calculate()
        # 2) Floor에 열흐름 반영 및 상태 갱신
        self.floor.set_inputs(Q_flow=Q_flow_soil, R_Flr_Glob=self.floor.R_Flr_Glob)
        self.floor.step(dt)
    
    def _update_port_connections(self):
        """
        Update all port connections between components (1:1 mapping with Modelica connect statements)
        """
        # Radiation connections
        self.Q_rad_CanCov.heatPort_a.T = self.canopy.heatPort.T
        self.Q_rad_CanCov.heatPort_b.T = self.cover.heatPort.T
        self.Q_rad_FlrCan.heatPort_a.T = self.floor.heatPort.T
        self.Q_rad_FlrCan.heatPort_b.T = self.canopy.heatPort.T
        self.Q_rad_FlrCov.heatPort_a.T = self.floor.heatPort.T
        self.Q_rad_FlrCov.heatPort_b.T = self.cover.heatPort.T
        self.Q_rad_CanScr.heatPort_a.T = self.canopy.heatPort.T
        self.Q_rad_CanScr.heatPort_b.T = self.thScreen.heatPort.T
        self.Q_rad_FlrScr.heatPort_a.T = self.floor.heatPort.T
        self.Q_rad_FlrScr.heatPort_b.T = self.thScreen.heatPort.T
        self.Q_rad_ScrCov.heatPort_a.T = self.thScreen.heatPort.T
        self.Q_rad_ScrCov.heatPort_b.T = self.cover.heatPort.T
        self.Q_rad_CovSky.heatPort_a.T = self.cover.heatPort.T
        self.Q_rad_CovSky.heatPort_b.T = self.air.T

        # Convection connections
        self.Q_cnv_CanAir.heatPort_a.T = self.canopy.heatPort.T
        self.Q_cnv_CanAir.heatPort_b.T = self.air.heatPort.T
        self.Q_cnv_FlrAir.heatPort_a.T = self.floor.heatPort.T
        self.Q_cnv_FlrAir.heatPort_b.T = self.air.heatPort.T
        self.Q_cnv_CovOut.heatPort_a.T = self.cover.heatPort.T
        self.Q_cnv_CovOut.heatPort_b.T = self.air.T
        self.Q_cnv_AirScr.heatPort_a.T = self.air.heatPort.T
        self.Q_cnv_AirScr.heatPort_b.T = self.thScreen.heatPort.T
        self.Q_cnv_AirCov.heatPort_a.T = self.air.heatPort.T
        self.Q_cnv_AirCov.heatPort_b.T = self.cover.heatPort.T
        self.Q_cnv_TopCov.heatPort_a.T = self.air_top.heatPort.T
        self.Q_cnv_TopCov.heatPort_b.T = self.cover.heatPort.T
        self.Q_cnv_ScrTop.heatPort_a.T = self.thScreen.heatPort.T
        self.Q_cnv_ScrTop.heatPort_b.T = self.air_top.heatPort.T

        # MassPort connections (vapor/gas)
        self.MV_CanAir.massPort_a.VP = self.canopy.massPort.VP
        self.MV_CanAir.massPort_b.VP = self.air.massPort.VP
        self.Q_cnv_AirScr.massPort_a.VP = self.air.massPort.VP
        self.Q_cnv_AirScr.massPort_b.VP = self.thScreen.massPort.VP
        self.Q_cnv_AirCov.massPort_a.VP = self.air.massPort.VP
        self.Q_cnv_AirCov.massPort_b.VP = self.cover.massPort.VP
        self.Q_cnv_TopCov.massPort_a.VP = self.air_top.massPort.VP
        self.Q_cnv_TopCov.massPort_b.VP = self.cover.massPort.VP
        self.Q_cnv_ScrTop.massPort_a.VP = self.thScreen.massPort.VP
        self.Q_cnv_ScrTop.massPort_b.VP = self.air_top.massPort.VP
        # (Add more massPort connections if needed)
        # CO2, Pipe, etc. if needed
        # ...
    
    def _update_control_systems(self, weather, setpoint, sc_usable):
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
        self.SC.SC_usable = sc_usable['SC_usable']  # SC_usable 데이터 사용
        self.SC.compute()
        
        # Update ventilation control
        self.U_vents.T_air = self.air.T
        self.U_vents.T_air_sp = setpoint['T_sp'] + 273.15
        self.U_vents.Mdot = self.PID_Mdot.CS
        self.U_vents.RH_air_input = self.air.RH
        self.U_vents.compute()
        
        # Update screen state
        self.thScreen.SC = self.SC.SC
    
    def _calculate_energy_flows(self, dt):
        """
        Calculate all energy flows between components
        dt: 시뮬레이션 시간 간격(초)
        """
        # Calculate heat fluxes from pipe components
        self.q_low = -self.pipe_low.flow1DimInc.Q_tot / self.surface
        self.q_up = -self.pipe_up.flow1DimInc.Q_tot / self.surface
        self.q_tot = -(self.pipe_low.flow1DimInc.Q_tot + self.pipe_up.flow1DimInc.Q_tot) / self.surface
        
        # Update accumulated energies (Modelica 방정식 반영)
        if self.q_tot > 0:
            # max(q_tot,0) = der(E_th_tot_kWhm2*1e3*3600)
            # E_th_tot_kWhm2의 변화량 계산 (W·s → kWh/m²)
            dE_th = (self.q_tot * dt) / (1000 * 3600)  # W·s → kWh/m²
            self.E_th_tot_kWhm2 += dE_th
            
        # E_th_tot = E_th_tot_kWhm2*surface.k
        self.E_th_tot = self.E_th_tot_kWhm2 * self.surface
        
        # Update electrical energy (Modelica 방정식 반영)
        # der(W_el_illu*1000*3600)=illu.W_el/surface.k
        dW_el = (self.illu.W_el * dt) / (self.surface * 1000 * 3600)  # W·s → kWh/m²
        self.W_el_illu = self.W_el_illu + dW_el  # 누적값 업데이트
        
        # E_el_tot_kWhm2 = W_el_illu
        self.E_el_tot_kWhm2 = self.W_el_illu
        
        # E_el_tot = E_el_tot_kWhm2*surface.k
        self.E_el_tot = self.E_el_tot_kWhm2 * self.surface

        self.DM_Har = self.TYM.DM_Har

    
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
