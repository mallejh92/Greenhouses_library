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
        
        self.Q_cnv_CanAir = CanopyFreeConvection(
            A=self.surface,
            LAI=self.canopy.LAI,
            u=self.u_wind,
            h_Air=self.air.h_Air
        )
        self.Q_cnv_FlrAir = FreeConvection(phi=0, A=self.surface, floor=True)
        
        self.Q_rad_CovSky = Radiation_T4(
            epsilon_a=0.84,
            epsilon_b=1,
            A=self.surface
        )
        
        self.Q_cnv_CovOut = OutsideAirConvection(
            A=self.surface,
            phi=0.43633231299858,
            u=self.u_wind  # 초기 풍속 설정
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

        # Initialize radiation components for lower pipe (not used in heat-balance here)
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

        # Initialize radiation components for upper pipe (not used here)
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
        self.Q_cnv_ScrTop.HeatPort_a.T = self.thScreen.heatPort.T
        self.Q_cnv_ScrTop.HeatPort_b.T = self.air_top.heatPort.T
        self.Q_cnv_ScrTop.MassPort_a.VP = self.thScreen.massPort.VP
        self.Q_cnv_ScrTop.MassPort_b.VP = self.air_top.massPort.VP

        # Initialize control systems
        self.PID_Mdot = PID(
            PVmin=18 + 273.15,
            PVmax=22 + 273.15,
            PVstart=self.air.T,
            CSstart=0.0,
            steadyStateInit=True,
            CSmin=0,
            Kp=0.7,
            Ti=600,
            CSmax=86.75
        )

        self.PID_CO2 = PID(
            PVstart=0.5,
            CSstart=0.5,
            steadyStateInit=False,
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
            
        except Exception as e:
            print(f"Error during data loading: {e}")
            raise
        
        # Initialize TomatoYieldModel
        self.TYM = TomatoYieldModel(
            n_dev=50,
            LAI_MAX=2.7,
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

        # Soil conduction heat flux placeholder
        self.Q_cd_Soil_val = 0.0
        
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
        # 복사 열전달 연결
        self.Q_rad_CanCov.port_a = self.canopy.heatPort
        self.Q_rad_CanCov.port_b = self.cover.heatPort
        
        self.Q_rad_FlrCan.port_a = self.floor.heatPort
        self.Q_rad_FlrCan.port_b = self.canopy.heatPort
        
        self.Q_rad_FlrCov.port_a = self.floor.heatPort
        self.Q_rad_FlrCov.port_b = self.cover.heatPort
        
        self.Q_rad_CanScr.port_a = self.canopy.heatPort
        self.Q_rad_CanScr.port_b = self.thScreen.heatPort
        
        self.Q_rad_FlrScr.port_a = self.floor.heatPort
        self.Q_rad_FlrScr.port_b = self.thScreen.heatPort
        
        self.Q_rad_ScrCov.port_a = self.thScreen.heatPort
        self.Q_rad_ScrCov.port_b = self.cover.heatPort
        
        self.Q_rad_CovSky.port_a = self.cover.heatPort
        
        # 대류 열전달 연결
        self.Q_cnv_CanAir.port_a = self.canopy.heatPort
        self.Q_cnv_CanAir.port_b = self.air.heatPort
        
        self.Q_cnv_FlrAir.port_a = self.floor.heatPort
        self.Q_cnv_FlrAir.port_b = self.air.heatPort
        
        self.Q_cnv_AirScr.HeatPort_a = self.air.heatPort
        self.Q_cnv_AirScr.HeatPort_b = self.thScreen.heatPort
        
        self.Q_cnv_CovOut.port_a = self.cover.heatPort
        
        self.Q_cnv_AirCov.HeatPort_a = self.air.heatPort
        self.Q_cnv_AirCov.HeatPort_b = self.cover.heatPort
        
        self.Q_cnv_TopCov.HeatPort_a = self.air_top.heatPort
        self.Q_cnv_TopCov.HeatPort_b = self.cover.heatPort
        
        self.Q_cnv_ScrTop.HeatPort_a = self.thScreen.heatPort
        self.Q_cnv_ScrTop.HeatPort_b = self.air_top.heatPort
        
        # 수증기 전달 연결
        self.Q_cnv_AirScr.MassPort_a = self.air.massPort
        self.Q_cnv_AirScr.MassPort_b = self.thScreen.massPort
        
        self.Q_cnv_AirCov.MassPort_a = self.air.massPort
        self.Q_cnv_AirCov.MassPort_b = self.cover.massPort
        
        self.Q_cnv_TopCov.MassPort_a = self.air_top.massPort
        self.Q_cnv_TopCov.MassPort_b = self.cover.massPort
        
        self.Q_cnv_ScrTop.MassPort_a = self.thScreen.massPort
        self.Q_cnv_ScrTop.MassPort_b = self.air_top.massPort

        # Radiation port connections
        self.Q_rad_FlrCan.port_a.T = self.floor.heatPort.T
        self.Q_rad_FlrCan.port_b.T = self.canopy.heatPort.T

        self.Q_rad_CanCov.port_a.T = self.canopy.heatPort.T
        self.Q_rad_CanCov.port_b.T = self.cover.heatPort.T

        self.Q_rad_FlrCov.port_a.T = self.floor.heatPort.T
        self.Q_rad_FlrCov.port_b.T = self.cover.heatPort.T

    def step(self, dt, time_idx):
        """
        시뮬레이션 한 스텝 진행
        Args:
            dt: 시간 간격 (초)
            time_idx: 현재 시간 인덱스
        """
        # 작은 시간 단계로 분할하여 안정성 향상
        sub_steps = 10
        sub_dt = dt / sub_steps
        
        # 현재 날씨와 설정값 가져오기
        current_weather = self.weather_df.iloc[time_idx % len(self.weather_df)]
        current_sp = self.sp_df.iloc[time_idx % len(self.sp_df)]
        sc_usable = self.SC_usable.get_value(time_idx, interpolate=True)
        
        for _ in range(sub_steps):
            # 1. 제어 시스템 업데이트
            self._update_control_systems(sub_dt, current_weather, current_sp, sc_usable)
            
            # 2. 구성요소 상태 업데이트
            self._update_components(sub_dt, current_weather, current_sp)
            
            # 3. 열전달 계산
            self._update_heat_transfer(sub_dt)
            
            # 4. 포트 연결 업데이트
            self._update_port_connections_ports_only(sub_dt)
            
            # 5. 에너지 흐름 계산
            self._calculate_energy_flows(sub_dt)
            
            # 6. 상태 검증
            self._verify_state()
        
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
        Q_flow_AirOut, MV_flow_AirOut = self.Q_ven_AirOut.update(
            SC=self.thScreen.SC,
            u=weather['u_wind'],
            U_vents=self.U_vents.U_vents,
            T_a=self.air.T,
            T_b=weather['T_out'] + 273.15,
            VP_a=self.air.VP,
            VP_b=self.VP_out
        )
        
        Q_flow_TopOut, MV_flow_TopOut = self.Q_ven_TopOut.update(
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

        # Update tomato yield model with the latest environmental conditions
        self.TYM.step(
            dt,
            R_PAR_can=self.solar_model.R_PAR_Can_umol + self.illu.R_PAR_Can_umol,
            CO2_air=self.CO2_air.CO2_ppm,
            T_canK=self.canopy.T,
        )
        
        # Update CanopyFreeConvection LAI
        self.Q_cnv_CanAir.LAI = self.canopy.LAI

        # 4. Update all port connections first (heat ports, radiation view factors, etc.)
        self._update_port_connections_ports_only(dt)

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
        
        # External CO2 injection directly sets the mass flow rate of CO2
        self.CO2_air.MC_flow = self.phi_ExtCO2
        self.CO2_air.step(dt)
        self.CO2_top.step(dt)

        # Note: Radiation & Convection steps have been moved to _update_heat_transfer()
    
    def _update_port_connections_ports_only(self, dt):
        """
        Update only the port temperatures and view factors (no step calls here)
        This function is called inside _update_components to refresh port assignments
        before radiation/convection steps in _update_heat_transfer().
        """
        # 1) 모든 컴포넌트의 열 포트(heatPort) 온도 갱신
        self.air.heatPort.T       = self.air.T
        self.air_top.heatPort.T   = self.air_top.T
        self.cover.heatPort.T     = self.cover.T
        self.canopy.heatPort.T    = self.canopy.T
        self.floor.heatPort.T     = self.floor.T
        self.thScreen.heatPort.T  = self.thScreen.T

        # 2) 복사 시야계수 업데이트
        screen_open = 1.0 - self.thScreen.SC  # 스크린이 열린 비율

        # 캔오피→스크린
        self.Q_rad_CanScr.FFa = self.canopy.FF
        self.Q_rad_CanScr.FFb = self.thScreen.FF_i * self.thScreen.SC
        
        # 바닥→스크린
        self.Q_rad_FlrScr.FFa = 1.0
        self.Q_rad_FlrScr.FFb = self.thScreen.FF_i * self.thScreen.SC
        self.Q_rad_FlrScr.FFab1 = self.canopy.FF
        self.Q_rad_FlrScr.FFab2 = self.pipe_up.FF
        self.Q_rad_FlrScr.FFab3 = self.pipe_low.FF

        # 스크린→덮개
        self.Q_rad_ScrCov.FFa = self.thScreen.FF_i * self.thScreen.SC
        self.Q_rad_ScrCov.FFb = 1.0

        # 덮개→하늘
        self.Q_rad_CovSky.FFa = screen_open
        self.Q_rad_CovSky.FFb = 1.0

        # 파이프 관련 시야계수
        self.Q_rad_LowScr.FFb = self.thScreen.FF_i * self.thScreen.SC
        self.Q_rad_UpScr.FFb  = self.thScreen.FF_i * self.thScreen.SC

        # 대류 열 연결 (ports만 갱신, step은 _update_heat_transfer 에서)
        self.Q_cnv_CanAir.port_a.T = self.canopy.heatPort.T
        self.Q_cnv_CanAir.port_b.T = self.air.heatPort.T
        
        self.Q_cnv_FlrAir.port_a.T = self.floor.heatPort.T  # 바닥
        self.Q_cnv_FlrAir.port_b.T = self.air.heatPort.T    # 공기
        
        self.Q_cnv_AirScr.port_a.T = self.air.heatPort.T
        self.Q_cnv_AirScr.port_b.T = self.thScreen.heatPort.T
        self.Q_cnv_AirScr.SC     = self.thScreen.SC
        
        self.Q_cnv_AirCov.port_a.T = self.air.heatPort.T
        self.Q_cnv_AirCov.port_b.T = self.cover.heatPort.T
        self.Q_cnv_AirCov.SC     = self.thScreen.SC
        
        self.Q_cnv_TopCov.port_a.T = self.air_top.heatPort.T
        self.Q_cnv_TopCov.port_b.T = self.cover.heatPort.T
        self.Q_cnv_TopCov.SC      = self.thScreen.SC
        
        self.Q_cnv_ScrTop.HeatPort_a.T = self.thScreen.heatPort.T
        self.Q_cnv_ScrTop.HeatPort_b.T = self.air_top.heatPort.T
        self.Q_cnv_ScrTop.SC            = self.thScreen.SC

        # MassPort.VP 갱신
        self.Q_cnv_AirScr.MassPort_a.VP = self.air.massPort.VP
        self.Q_cnv_AirScr.MassPort_b.VP = self.thScreen.massPort.VP

        self.Q_cnv_AirCov.MassPort_a.VP = self.air.massPort.VP
        self.Q_cnv_AirCov.MassPort_b.VP = self.cover.surfaceVP.VP

        self.Q_cnv_TopCov.MassPort_a.VP = self.air_top.massPort.VP
        self.Q_cnv_TopCov.MassPort_b.VP = self.cover.surfaceVP.VP

        self.Q_cnv_ScrTop.MassPort_a.VP = self.thScreen.surfaceVP.VP
        self.Q_cnv_ScrTop.MassPort_b.VP = self.air_top.massPort.VP

        # Radiation port connections
        self.Q_rad_FlrCan.port_a.T = self.floor.heatPort.T
        self.Q_rad_FlrCan.port_b.T = self.canopy.heatPort.T

        self.Q_rad_CanCov.port_a.T = self.canopy.heatPort.T
        self.Q_rad_CanCov.port_b.T = self.cover.heatPort.T

        self.Q_rad_FlrCov.port_a.T = self.floor.heatPort.T
        self.Q_rad_FlrCov.port_b.T = self.cover.heatPort.T

    def _update_heat_transfer(self, dt):
        """
        Perform Radiation.step(), Convection.step(), and compute heat balances.
        현재 방사 및 대류 계산 후, 각 컴포넌트의 Q_flow를 업데이트.
        """
        # 1) Radiation 계산
        self.Q_rad_CanCov_val = self.Q_rad_CanCov.step() or 0.0
        self.Q_rad_FlrCan_val = self.Q_rad_FlrCan.step() or 0.0
        self.Q_rad_FlrCov_val = self.Q_rad_FlrCov.step() or 0.0
        self.Q_rad_CanScr_val = self.Q_rad_CanScr.step() or 0.0
        self.Q_rad_FlrScr_val = self.Q_rad_FlrScr.step() or 0.0
        self.Q_rad_ScrCov_val = self.Q_rad_ScrCov.step() or 0.0
        self.Q_rad_CovSky_val = self.Q_rad_CovSky.step() or 0.0
        self.Q_rad_LowCan_val = self.Q_rad_LowCan.step() or 0.0
        self.Q_rad_UpCan_val  = self.Q_rad_UpCan.step()  or 0.0

        # Soil conduction heat flux (computed once per step)
        self.Q_cd_Soil_val = self.Q_cd_Soil.step(dt)

        # 2) Convection 계산 (단, u, VP는 이미 포트 업데이트에서 할당됨)
        self.Q_cnv_CanAir_val = self.Q_cnv_CanAir.step() or 0.0
        self.Q_cnv_FlrAir_val = self.Q_cnv_FlrAir.step() or 0.0
        self.Q_cnv_CovOut_val = self.Q_cnv_CovOut.step() or 0.0
        self.Q_cnv_AirScr_val = self.Q_cnv_AirScr.step() or 0.0
        self.Q_cnv_AirCov_val = self.Q_cnv_AirCov.step() or 0.0
        self.Q_cnv_TopCov_val = self.Q_cnv_TopCov.step() or 0.0
        self.Q_cnv_ScrTop_val = self.Q_cnv_ScrTop.step() or 0.0

        # 3) Heat balance 계산 (각 컴포넌트의 Q_flow 할당)
        self.canopy.Q_flow = (
            + self.Q_rad_FlrCan_val      # floor→canopy
            + self.Q_rad_LowCan_val      # lower‐pipe→canopy
            + self.Q_rad_UpCan_val       # upper‐pipe→canopy
            - self.Q_rad_CanCov_val      # canopy→cover
            - self.Q_rad_CanScr_val      # canopy→screen
            - self.Q_cnv_CanAir_val      # canopy→air 대류
        )
        self.floor.Q_flow = (
            -self.Q_rad_FlrCan_val
            -self.Q_rad_FlrCov_val
            -self.Q_rad_FlrScr_val
            -self.Q_cnv_FlrAir_val
            -self.Q_cd_Soil_val  # SoilConduction의 열유량
        )
        self.thScreen.Q_flow = (
            +self.Q_rad_CanScr_val
            +self.Q_rad_FlrScr_val
            -self.Q_rad_ScrCov_val
            +self.Q_cnv_AirScr_val
            -self.Q_cnv_ScrTop_val
        )
        self.cover.Q_flow = (
            +self.Q_rad_CanCov_val
            +self.Q_rad_FlrCov_val
            +self.Q_rad_ScrCov_val
            -self.Q_rad_CovSky_val
            +self.Q_cnv_AirCov_val
            -self.Q_cnv_TopCov_val
        )
        self.air.Q_flow = (
            +self.Q_cnv_CanAir_val
            +self.Q_cnv_FlrAir_val
            -self.Q_cnv_AirScr_val
            -self.Q_cnv_AirCov_val
            -self.Q_cnv_CovOut_val
        )
        self.air_top.Q_flow = (
            -self.Q_cnv_TopCov_val
            +self.Q_cnv_ScrTop_val
        )

        # 디버깅을 위한 열전달 값 출력
        screen_open = 1.0 - self.thScreen.SC
        print("\n=== 열전달 값 디버깅 ===")
        print(f"Screen SC: {self.thScreen.SC:.2f}, Screen Open: {screen_open:.2f}")
        print(f"View Factors:")
        print(f"  CanScr: FFa={self.Q_rad_CanScr.FFa:.3f}, FFb={self.Q_rad_CanScr.FFb:.3f}")
        print(f"  FlrScr: FFa={self.Q_rad_FlrScr.FFa:.3f}, FFb={self.Q_rad_FlrScr.FFb:.3f}")
        print(f"  ScrCov: FFa={self.Q_rad_ScrCov.FFa:.3f}, FFb={self.Q_rad_ScrCov.FFb:.3f}")
        print(f"Radiation:")
        print(f"  Q_rad_CanCov: {self.Q_rad_CanCov_val:.2f} W (캔오피→덮개)")
        print(f"  Q_rad_FlrCan: {self.Q_rad_FlrCan_val:.2f} W (바닥→캔오피)")
        print(f"  Q_rad_FlrCov: {self.Q_rad_FlrCov_val:.2f} W (바닥→덮개)")
        print(f"  Q_rad_CanScr: {self.Q_rad_CanScr_val:.2f} W (캔오피→스크린)")
        print(f"  Q_rad_FlrScr: {self.Q_rad_FlrScr_val:.2f} W (바닥→스크린)")
        print(f"  Q_rad_ScrCov: {self.Q_rad_ScrCov_val:.2f} W (스크린→덮개)")
        print(f"  Q_rad_CovSky: {self.Q_rad_CovSky_val:.2f} W (덮개→하늘)")
        print(f"Convection:")
        print(f"  Q_cnv_CanAir: {self.Q_cnv_CanAir_val:.2f} W (캔오피↔공기)")
        print(f"  Q_cnv_FlrAir: {self.Q_cnv_FlrAir_val:.2f} W (바닥↔공기)")
        print(f"  Q_cnv_AirScr: {self.Q_cnv_AirScr_val:.2f} W (공기↔스크린)")
        print(f"  Q_cnv_CovOut: {self.Q_cnv_CovOut_val:.2f} W (공기↔외부)")
        print(f"  Q_cnv_AirCov: {self.Q_cnv_AirCov_val:.2f} W (공기↔덮개)")
        print(f"  Q_cnv_TopCov: {self.Q_cnv_TopCov_val:.2f} W (상부공기↔덮개)")
        print(f"  Q_cnv_ScrTop: {self.Q_cnv_ScrTop_val:.2f} W (스크린↔상부공기)")

        # 디버깅을 위한 열 수지 값 출력
        print("\n=== 열 수지 값 디버깅 ===")
        print(f"Canopy Q_flow: {self.canopy.Q_flow:.2f} W")
        print(f"Floor Q_flow: {self.floor.Q_flow:.2f} W")
        print(f"Screen Q_flow: {self.thScreen.Q_flow:.2f} W")
        print(f"Cover Q_flow: {self.cover.Q_flow:.2f} W")
        print(f"Air Q_flow: {self.air.Q_flow:.2f} W")
        print(f"Air Top Q_flow: {self.air_top.Q_flow:.2f} W")
    
    def _update_control_systems(self, dt, weather, setpoint, sc_usable):
        """
        Update control systems based on current state and setpoints
        
        Parameters
        ----------
        dt : float
            Simulation time step [s]
        weather : dict
            Current weather data
        setpoint : dict
            Climate setpoints
        sc_usable : dict
            Screen usability information
        """
        # PID_Mdot 업데이트 (온도 제어)
        self.PID_Mdot.PV = self.air.T
        self.PID_Mdot.SP = setpoint['T_sp'] + 273.15
        self.PID_Mdot.compute()
        
        # PID 출력을 난방 파이프에 연결
        self.pipe_low.flow1DimInc.Q_tot = -self.PID_Mdot.CS * 14000  # 총 열량으로 변환
        
        # PID_CO2 업데이트 (CO2 제어)
        self.PID_CO2.PV = self.CO2_air.CO2
        self.PID_CO2.SP = setpoint['CO2_sp'] * 1.94  # ppm to mg/m3
        self.PID_CO2.compute()
        
        # 스크린 제어 업데이트
        self.SC.R_Glob_can = weather['I_glob']
        self.SC.T_air_sp = setpoint['T_sp'] + 273.15
        self.SC.T_out = weather['T_out'] + 273.15
        self.SC.RH_air = self.air.RH
        self.SC.SC_usable = sc_usable['SC_usable'] if isinstance(sc_usable, dict) else sc_usable
        self.SC.compute()
        
        # 환기 제어 업데이트
        self.U_vents.T_air = self.air.T
        self.U_vents.T_air_sp = setpoint['T_sp'] + 273.15
        self.U_vents.Mdot = self.PID_Mdot.CS
        self.U_vents.RH_air_input = self.air.RH
        self.U_vents.compute(dt)
        
        # 스크린 상태 업데이트
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
            # dE_th = (q_tot * dt) / (1000 * 3600)
            dE_th = (self.q_tot * dt) / (1000 * 3600)
            self.E_th_tot_kWhm2 += dE_th
            
        self.E_th_tot = self.E_th_tot_kWhm2 * self.surface
        
        # Update electrical energy
        dW_el = (self.illu.W_el * dt) / (self.surface * 1000 * 3600)
        self.W_el_illu += dW_el
        
        self.E_el_tot_kWhm2 = self.W_el_illu
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

    def _verify_state(self):
        """
        시뮬레이션 상태 검증
        - 온도 범위 검사
        - 열수지 검증
        - 수증기 수지 검증
        """
        # 1. 온도 범위 검사
        if not (273.15 <= self.air.T <= 323.15):  # 0°C ~ 50°C
            print(f"경고: 공기 온도가 비정상 범위입니다: {self.air.T-273.15:.2f}°C")
        
        if not (273.15 <= self.canopy.T <= 323.15):
            print(f"경고: 캔오피 온도가 비정상 범위입니다: {self.canopy.T-273.15:.2f}°C")
        
        if not (273.15 <= self.floor.T <= 323.15):
            print(f"경고: 바닥 온도가 비정상 범위입니다: {self.floor.T-273.15:.2f}°C")
        
        if not (273.15 <= self.cover.T <= 323.15):
            print(f"경고: 덮개 온도가 비정상 범위입니다: {self.cover.T-273.15:.2f}°C")
        
        # 2. 열수지 검증
        total_heat_flow = (
            self.canopy.Q_flow +
            self.floor.Q_flow +
            self.air.Q_flow +
            self.cover.Q_flow +
            self.thScreen.Q_flow +
            self.air_top.Q_flow
        )
        
        if abs(total_heat_flow) > 1000:  # 1kW 이상의 불균형
            print(f"경고: 열수지 불균형이 발생했습니다: {total_heat_flow:.2f} W")
        
        # 3. 수증기 수지 검증
        total_vapor_flow = (
            self.air.massPort.MV_flow +
            self.canopy.massPort.MV_flow +
            self.cover.massPort.MV_flow +
            self.thScreen.massPort.MV_flow +
            self.air_top.massPort.MV_flow
        )
        
        if abs(total_vapor_flow) > 0.1:  # 0.1 kg/s 이상의 불균형
            print(f"경고: 수증기 수지 불균형이 발생했습니다: {total_vapor_flow:.3f} kg/s")
        
        # 4. 제어 시스템 검증
        if self.PID_Mdot.CS < 0 or self.PID_Mdot.CS > self.PID_Mdot.CSmax:
            print(f"경고: PID_Mdot 제어 신호가 범위를 벗어났습니다: {self.PID_Mdot.CS:.2f}")
        
        if self.PID_CO2.CS < 0 or self.PID_CO2.CS > self.PID_CO2.CSmax:
            print(f"경고: PID_CO2 제어 신호가 범위를 벗어났습니다: {self.PID_CO2.CS:.2f}")
        
        if self.thScreen.SC < 0 or self.thScreen.SC > 1:
            print(f"경고: 스크린 개도가 범위를 벗어났습니다: {self.thScreen.SC:.2f}")
