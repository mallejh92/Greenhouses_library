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
        Initialize Greenhouse_1 model
        
        Parameters:
        -----------
        time_unit_scaling : float, optional
            Time unit scaling factor (default: 1.0)
        """
        # Initialize time unit scaling
        self.time_unit_scaling = time_unit_scaling
        
        # Initialize surface area
        self.surface = 1.4e4  # [m²]
        
        # Initialize weather data
        initial_weather = {
            'T_out': 10.0,  # [°C]
            'VP_out': 1000.0,  # [Pa]
            'u_wind': 2.0,  # [m/s]
            'I_glob': 0.0,  # [W/m²]
            'T_sky': 10.0  # [°C]
        }
        
        # Set initial values
        self.T_out = initial_weather['T_out'] + 273.15  # [K]
        self.VP_out = initial_weather['VP_out']  # [Pa]
        self.u_wind = initial_weather['u_wind']  # [m/s]
        self.I_glob = initial_weather['I_glob']  # [W/m²]
        self.T_sky = initial_weather['T_sky'] + 273.15  # [K]
        
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

        # Initialize components with stable initial conditions
        self.cover = Cover(
            rho=2600,
            c_p=840,
            A=self.surface,
            steadystate=True,  # 빠르게 평형을 이루는 체계
            h_cov=1e-3,
            phi=0.43633231299858
        )
        
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
            steadystateVP=True  # 수증기도 빠르게 평형을 이룸
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
            topAir=False,
            forcedVentilation=False
        )
        
        self.Q_ven_TopOut = Ventilation(
            A=self.surface,
            thermalScreen=True,
            topAir=True,
            forcedVentilation=False
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
        self.Q_ven_AirOut.HeatPort_b.T = initial_weather['T_out'] + 273.15  # out.port.T
        self.Q_ven_AirOut.MassPort_a.VP = self.air.massPort.VP
        self.Q_ven_AirOut.MassPort_b.VP = self.VP_out  # prescribedVPout.port.VP
        
        # Q_ven_TopOut
        self.Q_ven_TopOut.HeatPort_a.T = self.air_top.heatPort.T
        self.Q_ven_TopOut.HeatPort_b.T = initial_weather['T_out'] + 273.15
        self.Q_ven_TopOut.MassPort_a.VP = self.air_top.massPort.VP
        self.Q_ven_TopOut.MassPort_b.VP = self.VP_out
        
        # Q_ven_AirTop
        self.Q_ven_AirTop.HeatPort_a.T = self.air.heatPort.T
        self.Q_ven_AirTop.HeatPort_b.T = self.air_top.heatPort.T
        self.Q_ven_AirTop.MassPort_a.VP = self.air.massPort.VP
        self.Q_ven_AirTop.MassPort_b.VP = self.air_top.massPort.VP

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

        # Initialize radiation components for lower pipe
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

        # Initialize radiation components for upper pipe
        self.Q_rad_UpFlr = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=0.89,
            N=self.pipe_up.N
        )
        self.Q_rad_UpFlr.FFa = self.pipe_up.FF
        self.Q_rad_UpFlr.FFb = 1
        self.Q_rad_UpFlr.FFab1 = self.canopy.FF
        self.Q_rad_UpFlr.FFab2 = self.pipe_low.FF

        self.Q_rad_UpCan = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=1,
            N=self.pipe_up.N
        )
        self.Q_rad_UpCan.FFa = self.pipe_up.FF
        self.Q_rad_UpCan.FFb = self.canopy.FF

        self.Q_rad_UpCov = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=0.84,
            N=self.pipe_up.N
        )
        self.Q_rad_UpCov.FFa = self.pipe_up.FF
        self.Q_rad_UpCov.FFb = 1
        self.Q_rad_UpCov.FFab1 = self.thScreen.FF_ij

        self.Q_rad_UpScr = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=1,
            N=self.pipe_up.N
        )
        self.Q_rad_UpScr.FFa = self.pipe_low.FF
        self.Q_rad_UpScr.FFb = self.thScreen.FF_i

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
    
    def _connect_heat_ports(self):
        """Connect heat ports between components"""
        # Connect floor radiation
        self.Q_rad_FlrCan.port_a.T = self.floor.heatPort.T
        self.Q_rad_FlrCan.port_b.T = self.canopy.heatPort.T
        
        self.Q_rad_FlrCov.port_a.T = self.floor.heatPort.T
        self.Q_rad_FlrCov.port_b.T = self.cover.heatPort.T
        
        self.Q_rad_FlrScr.port_a.T = self.floor.heatPort.T
        self.Q_rad_FlrScr.port_b.T = self.thScreen.heatPort.T
        
        # Connect canopy radiation
        self.Q_rad_CanCov.port_a.T = self.canopy.heatPort.T
        self.Q_rad_CanCov.port_b.T = self.cover.heatPort.T
        
        self.Q_rad_CanScr.port_a.T = self.canopy.heatPort.T
        self.Q_rad_CanScr.port_b.T = self.thScreen.heatPort.T
        
        # Connect cover radiation
        self.Q_rad_CovSky.port_a.T = self.cover.heatPort.T
        self.Q_rad_CovSky.port_b.T = self.T_sky
        
        self.Q_rad_ScrCov.port_a.T = self.thScreen.heatPort.T
        self.Q_rad_ScrCov.port_b.T = self.cover.heatPort.T
        
        # Connect pipe radiation
        self.Q_rad_LowFlr.set_heatPorts_a_temperature(self.pipe_low.heatPorts.T)
        self.Q_rad_LowFlr.port_b.T = self.floor.heatPort.T
        
        self.Q_rad_LowCan.set_heatPorts_a_temperature(self.pipe_low.heatPorts.T)
        self.Q_rad_LowCan.port_b.T = self.canopy.heatPort.T
        
        self.Q_rad_LowCov.set_heatPorts_a_temperature(self.pipe_low.heatPorts.T)
        self.Q_rad_LowCov.port_b.T = self.cover.heatPort.T
        
        self.Q_rad_LowScr.set_heatPorts_a_temperature(self.pipe_low.heatPorts.T)
        self.Q_rad_LowScr.port_b.T = self.thScreen.heatPort.T
        
        self.Q_rad_UpFlr.set_heatPorts_a_temperature(self.pipe_up.heatPorts.T)
        self.Q_rad_UpFlr.port_b.T = self.floor.heatPort.T
        
        self.Q_rad_UpCan.set_heatPorts_a_temperature(self.pipe_up.heatPorts.T)
        self.Q_rad_UpCan.port_b.T = self.canopy.heatPort.T
        
        self.Q_rad_UpCov.set_heatPorts_a_temperature(self.pipe_up.heatPorts.T)
        self.Q_rad_UpCov.port_b.T = self.cover.heatPort.T
        
        self.Q_rad_UpScr.set_heatPorts_a_temperature(self.pipe_up.heatPorts.T)
        self.Q_rad_UpScr.port_b.T = self.thScreen.heatPort.T
    
    def step(self, dt, time_idx):
        """
        Advance simulation by one time step
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        time_idx : int
            Time index for data lookup
        """
        # 1) 현재 날씨 데이터 읽기 (CombiTimeTable은 시간(h) 단위)
        t_h = time_idx * dt / 3600.0
        weather = self.TMY_and_control.get_value(t_h, interpolate=True)
        setpoint = self.SP_new.get_value(t_h, interpolate=True)
        sc_usable = self.SC_usable.get_value(t_h, interpolate=True)

        # 2) 외기 온도/상대습도로부터 VP_out 계산
        T_out_C = weather['T_out']
        RH_out_frac = weather['RH_out'] / 100.0
        VP_sat = 610.78 * np.exp((17.27 * T_out_C) / (T_out_C + 237.3))  # Tetens 식
        self.VP_out = RH_out_frac * VP_sat  # [Pa]

        # 3) 외부 온도/풍속/일사/스카이온도 업데이트
        self.T_out = T_out_C + 273.15
        self.u_wind = weather['u_wind']
        self.I_glob = weather['I_glob']
        self.T_sky = weather['T_sky'] + 273.15
        
        # Update components
        self._update_components(dt, weather, setpoint)
        
        # Update port connections
        self._update_port_connections()
        
        # Update control systems
        self._update_control_systems(weather, setpoint, sc_usable)
        
        # Calculate energy flows
        self._calculate_energy_flows(dt)
        
        # Update air humidity before printing state
        self.air.update_humidity()
        
        # Print current state
        print(f"\n=== Step {time_idx} 시작 (t={time_idx*dt/3600:.2f}h) ===")
        if time_idx == 0:
            print("초기 상태:")
        print(f"Air: T={self.air.T-273.15:.2f}°C, RH={self.air.RH*100:.1f}%, VP={self.air.massPort.VP:.1f} Pa")
        print(f"Cover: T={self.cover.T-273.15:.2f}°C")
        print(f"Canopy: T={self.canopy.T-273.15:.2f}°C")
        print(f"Floor: T={self.floor.T-273.15:.2f}°C")
        print(f"Screen: T={self.thScreen.T-273.15:.2f}°C, SC={self.thScreen.SC:.2f}")
        # print(f"Pipe_low: T={self.pipe_low.T-273.15:.2f}°C")
        # print(f"Pipe_up: T={self.pipe_up.T-273.15:.2f}°C")
        print(f"Outside: T={self.T_out-273.15:.2f}°C, VP={self.VP_out:.1f} Pa")
        print(f"Wind: u={self.u_wind:.1f} m/s")
        print(f"Global: I={self.I_glob:.0f} W/m²")
        print(f"Screen: SC={self.thScreen.SC:.2f}, vent={self.Q_ven_AirOut.U_vents:.2f}, DM_Har={self.TYM.DM_Har:.2f} mg/m²")
        
        # Get current state
        return self._get_state()
    
    def _update_components(self, dt, weather, setpoint):
        """
        Update all component states with weather and setpoint data
        - 환기 컴포넌트의 MassPort 연결을 매 스텝마다 갱신
        - U_vents.U_vents: 환기구 개방률(0~1, PID 등 제어 결과)
        """
        # 모든 컴포넌트의 열 수지(Q_flow) 초기화
        self.air.Q_flow = 0.0
        self.air_top.Q_flow = 0.0
        self.cover.Q_flow = 0.0
        self.canopy.Q_flow = 0.0
        self.floor.Q_flow = 0.0
        self.thScreen.Q_flow = 0.0
        
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
        Q_flow_AirOut, MV_flow_AirOut, f_vent_AirOut = self.Q_ven_AirOut.update(
            SC=self.thScreen.SC,
            u=weather['u_wind'],
            U_vents=self.U_vents.U_vents,
            T_a=self.air.T,
            T_b=weather['T_out'] + 273.15,
            VP_a=self.air.VP,
            VP_b=self.VP_out
        )
        
        Q_flow_TopOut, MV_flow_TopOut, f_vent_TopOut = self.Q_ven_TopOut.update(
            SC=self.thScreen.SC,
            u=weather['u_wind'],
            U_vents=self.U_vents.U_vents,
            T_a=self.air_top.T,
            T_b=weather['T_out'] + 273.15,
            VP_a=self.air_top.massPort.VP,
            VP_b=self.VP_out
        )

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
        Update all port connections between components
        - 매 스텝마다 시야계수 업데이트
        - 열 수지를 한 번만 계산
        - 스크린 개폐율 반영
        """
        # 1. 모든 컴포넌트의 열 수지 초기화
        self.air.Q_flow = 0.0
        self.air_top.Q_flow = 0.0
        self.cover.Q_flow = 0.0
        self.canopy.Q_flow = 0.0
        self.floor.Q_flow = 0.0
        self.thScreen.Q_flow = 0.0

        # 2. Update heat port temperatures for all components
        self.air.heatPort.T = self.air.T
        self.air_top.heatPort.T = self.air_top.T
        self.cover.heatPort.T = self.cover.T
        self.canopy.heatPort.T = self.canopy.T
        self.floor.heatPort.T = self.floor.T
        self.thScreen.heatPort.T = self.thScreen.T
        
        # 3. Update mass port vapor pressures
        self.air.massPort.VP = self.air.VP
        self.air_top.massPort.VP = self.air.massPort.VP
        self.cover.massPort.VP = self.cover.surfaceVP.VP
        self.canopy.massPort.VP = self.canopy.surfaceVP.VP
        self.thScreen.massPort.VP = self.thScreen.surfaceVP.VP

        # 4. Update view factors for all radiation components
        # 스크린 개폐율에 따른 시야계수 업데이트
        screen_open = 1.0 - self.thScreen.SC  # 스크린이 열린 비율

        # 덮개→하늘 복사열 시야계수 업데이트
        self.Q_rad_CovSky.FFa = screen_open  # 스크린이 열린 부분만 하늘과 복사열 교환
        
        # 스크린 관련 시야계수 업데이트
        self.Q_rad_CanScr.FFb = self.thScreen.FF_i * self.thScreen.SC  # 캔오피→스크린
        self.Q_rad_FlrScr.FFb = self.thScreen.FF_i * self.thScreen.SC  # 바닥→스크린
        self.Q_rad_ScrCov.FFa = self.thScreen.FF_i * self.thScreen.SC  # 스크린→덮개
        
        # 파이프 관련 시야계수 업데이트
        self.Q_rad_LowScr.FFb = self.thScreen.FF_i * self.thScreen.SC  # 하부파이프→스크린
        self.Q_rad_UpScr.FFb = self.thScreen.FF_i * self.thScreen.SC   # 상부파이프→스크린

        # 5. Calculate all heat flows
        # 복사열 계산
        Q_rad_CanCov = self.Q_rad_CanCov.step(0) or 0.0  # 캔오피→덮개
        Q_rad_FlrCan = self.Q_rad_FlrCan.step(0) or 0.0  # 바닥→캔오피
        Q_rad_FlrCov = self.Q_rad_FlrCov.step(0) or 0.0  # 바닥→덮개
        Q_rad_CanScr = self.Q_rad_CanScr.step(0) or 0.0  # 캔오피→스크린
        Q_rad_FlrScr = self.Q_rad_FlrScr.step(0) or 0.0  # 바닥→스크린
        Q_rad_ScrCov = self.Q_rad_ScrCov.step(0) or 0.0  # 스크린→덮개
        Q_rad_CovSky = self.Q_rad_CovSky.step(0) or 0.0  # 덮개→하늘 (스크린 개폐율 반영됨)

        # 대류열 계산 (스크린 개폐율 반영)
        Q_cnv_CanAir = self.Q_cnv_CanAir.step(0) or 0.0  # 캔오피↔공기
        Q_cnv_FlrAir = self.Q_cnv_FlrAir.step(0) or 0.0  # 바닥↔공기
        Q_cnv_AirScr = self.Q_cnv_AirScr.step(0) or 0.0  # 공기↔스크린
        Q_cnv_AirCov = self.Q_cnv_AirCov.step(0) or 0.0  # 공기↔덮개
        Q_cnv_TopCov = self.Q_cnv_TopCov.step(0) or 0.0  # 상부공기↔덮개
        Q_cnv_ScrTop = self.Q_cnv_ScrTop.step(0) or 0.0  # 스크린↔상부공기

        # 6. Update component heat flows (한 번만 계산)
        # 캔오피 열 수지
        self.canopy.Q_flow = (
            -Q_rad_CanCov  # 캔오피→덮개
            +Q_rad_FlrCan  # 바닥→캔오피
            -Q_rad_CanScr  # 캔오피→스크린
            +Q_cnv_CanAir  # 캔오피↔공기
        )

        # 바닥 열 수지
        self.floor.Q_flow = (
            -Q_rad_FlrCan  # 바닥→캔오피
            -Q_rad_FlrCov  # 바닥→덮개
            -Q_rad_FlrScr  # 바닥→스크린
            +Q_cnv_FlrAir  # 바닥↔공기
        )

        # 스크린 열 수지
        self.thScreen.Q_flow = (
            +Q_rad_CanScr  # 캔오피→스크린
            +Q_rad_FlrScr  # 바닥→스크린
            -Q_rad_ScrCov  # 스크린→덮개
            +Q_cnv_AirScr  # 공기↔스크린
            -Q_cnv_ScrTop  # 스크린↔상부공기
        )

        # 덮개 열 수지
        self.cover.Q_flow = (
            +Q_rad_CanCov  # 캔오피→덮개
            +Q_rad_FlrCov  # 바닥→덮개
            +Q_rad_ScrCov  # 스크린→덮개
            -Q_rad_CovSky  # 덮개→하늘 (스크린 개폐율 반영됨)
            +Q_cnv_AirCov  # 공기↔덮개
            +Q_cnv_TopCov  # 상부공기↔덮개
        )

        # 공기 열 수지
        self.air.Q_flow = (
            -Q_cnv_CanAir  # 캔오피↔공기
            -Q_cnv_FlrAir  # 바닥↔공기
            -Q_cnv_AirScr  # 공기↔스크린
            -Q_cnv_AirCov  # 공기↔덮개
        )

        # 상부공기 열 수지
        self.air_top.Q_flow = (
            -Q_cnv_TopCov  # 상부공기↔덮개
            +Q_cnv_ScrTop  # 스크린↔상부공기
        )

        # 디버깅을 위한 열전달 값 출력
        print("\n=== 열전달 값 디버깅 ===")
        print(f"Screen SC: {self.thScreen.SC:.2f}, Screen Open: {screen_open:.2f}")
        print(f"Q_rad_CanCov: {Q_rad_CanCov:.2f} W")
        print(f"Q_rad_FlrCan: {Q_rad_FlrCan:.2f} W")
        print(f"Q_rad_FlrCov: {Q_rad_FlrCov:.2f} W")
        print(f"Q_rad_CanScr: {Q_rad_CanScr:.2f} W")
        print(f"Q_rad_FlrScr: {Q_rad_FlrScr:.2f} W")
        print(f"Q_rad_ScrCov: {Q_rad_ScrCov:.2f} W")
        print(f"Q_rad_CovSky: {Q_rad_CovSky:.2f} W")
        print(f"Q_cnv_CanAir: {Q_cnv_CanAir:.2f} W")
        print(f"Q_cnv_FlrAir: {Q_cnv_FlrAir:.2f} W")
        print(f"Q_cnv_AirScr: {Q_cnv_AirScr:.2f} W")
        print(f"Q_cnv_AirCov: {Q_cnv_AirCov:.2f} W")
        print(f"Q_cnv_TopCov: {Q_cnv_TopCov:.2f} W")
        print(f"Q_cnv_ScrTop: {Q_cnv_ScrTop:.2f} W")

        # 디버깅을 위한 열 수지 값 출력
        print("\n=== 열 수지 값 디버깅 ===")
        print(f"Canopy Q_flow: {self.canopy.Q_flow:.2f} W")
        print(f"Floor Q_flow: {self.floor.Q_flow:.2f} W")
        print(f"Screen Q_flow: {self.thScreen.Q_flow:.2f} W")
        print(f"Cover Q_flow: {self.cover.Q_flow:.2f} W")
        print(f"Air Q_flow: {self.air.Q_flow:.2f} W")
        print(f"Air Top Q_flow: {self.air_top.Q_flow:.2f} W")

        # 7. Update mass transfer connections
        # ... (기존 mass transfer 코드 유지) ...
    
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
