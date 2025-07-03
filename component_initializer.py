"""
컴포넌트 초기화 모듈
온실 시뮬레이션의 모든 컴포넌트를 초기화하는 클래스
"""

# Components
from Components.Greenhouse.Cover import Cover
from Components.Greenhouse.Air import Air
from Components.Greenhouse.Canopy import Canopy
from Components.Greenhouse.Floor import Floor
from Components.Greenhouse.Air_Top import Air_Top
from Components.Greenhouse.ThermalScreen import ThermalScreen
from Components.Greenhouse.Solar_model import Solar_model
from Components.Greenhouse.HeatingPipe import HeatingPipe
from Components.Greenhouse.Illumination import Illumination
from Components.CropYield.TomatoYieldModel import TomatoYieldModel

# Flows
from Flows.HeatTransfer.Radiation_T4 import Radiation_T4
from Flows.HeatTransfer.Radiation_N import Radiation_N
from Flows.HeatTransfer.CanopyFreeConvection import CanopyFreeConvection
from Flows.HeatTransfer.FreeConvection import FreeConvection
from Flows.HeatTransfer.OutsideAirConvection import OutsideAirConvection
from Flows.HeatTransfer.PipeFreeConvection_N import PipeFreeConvection_N
from Flows.HeatTransfer.SoilConduction import SoilConduction
from Flows.CO2MassTransfer.MC_AirCan import MC_AirCan
from Flows.CO2MassTransfer.CO2_Air import CO2_Air
from Flows.CO2MassTransfer.MC_ventilation2 import MC_ventilation2
from Flows.HeatAndVapourTransfer.Ventilation import Ventilation
from Flows.HeatAndVapourTransfer.AirThroughScreen import AirThroughScreen
from Flows.HeatAndVapourTransfer.Convection_Condensation import Convection_Condensation
from Flows.HeatAndVapourTransfer.Convection_Evaporation import Convection_Evaporation
from Flows.VapourMassTransfer.MV_CanopyTranspiration import MV_CanopyTranspiration
from Flows.FluidFlow.Reservoirs.SourceMdot import SourceMdot
from Modelica.Thermal.HeatTransfer.Sensors.TemperatureSensor import TemperatureSensor
from Flows.FluidFlow.Reservoirs.SinkP import SinkP
from Flows.Sensors.RHSensor import RHSensor
from Flows.Sources.CO2.PrescribedCO2Flow import PrescribedCO2Flow
from Flows.Sources.CO2.PrescribedConcentration import PrescribedConcentration

# Control Systems
from ControlSystems.PID import PID
from ControlSystems.Climate.Control_ThScreen import Control_ThScreen
from ControlSystems.Climate.Uvents_RH_T_Mdot import Uvents_RH_T_Mdot

# Initial conditions
INITIAL_CONDITIONS = {
    'air': {
        'T': 293.15,  # 20°C
        'RH': 0.7,    # 70%
        'h_Air_base': 3.8,  # 기본 공기층 높이 [m]
        'h_Air_screen_effect': 0.4  # 스크린 효과로 인한 높이 변화 [m]
    },
    'canopy': {
        'T': 293.15,  # 20°C
        'LAI': 1.06   # Leaf Area Index
    },
    'cover': {
        'T': 283.15,  # 10°C
        'epsilon': 0.84  # Emissivity
    },
    'floor': {
        'T': 288.15,  # 15°C
        'epsilon': 0.89  # Emissivity
    }
}

class ComponentInitializer:
    """온실 컴포넌트들을 초기화하는 클래스"""
    
    def __init__(self, surface: float, u_wind: float = 0.0):
        """
        초기화
        
        Args:
            surface (float): 온실 바닥 면적 [m²]
            u_wind (float): 초기 풍속 [m/s]
        """
        self.surface = surface
        self.u_wind = u_wind
    
    def calculate_h_air(self, screen_closure: float = 0.0) -> float:
        """
        스크린 상태에 따른 동적 공기층 높이 계산
        
        Args:
            screen_closure (float): 스크린 폐쇄율 [0-1]
                0: 완전히 열림, 1: 완전히 닫힘
        
        Returns:
            float: 계산된 공기층 높이 [m]
        """
        # Modelica 원본: h_Air = 3.8 + (1 - SC.y) * 0.4
        h_air_base = INITIAL_CONDITIONS['air']['h_Air_base']
        h_air_screen_effect = INITIAL_CONDITIONS['air']['h_Air_screen_effect']
        
        h_air = h_air_base + (1 - screen_closure) * h_air_screen_effect
        return h_air
    
    def initialize_all_components(self):
        """모든 컴포넌트를 초기화하고 딕셔너리로 반환"""
        components = {}
        
        # 1. cover 
        components['cover'] = Cover(
            rho=2600,  # 밀도 [kg/m³]
            c_p=840,   # 비열 [J/(kg·K)]
            A=self.surface,
            steadystate=False,
            h_cov=1e-3,  # 두께 [m]
            phi=0.43633231299858  # 경사각 [rad]
        )
        
        # 2. air - 초기에는 스크린이 완전히 열린 상태로 가정
        initial_h_air = self.calculate_h_air(screen_closure=0.0)
        components['air'] = Air(
            A=self.surface,
            steadystate=False,
            steadystateVP=False,
            h_Air=initial_h_air
        )

        # 3. canopy - 기본 LAI로 초기화, 나중에 TYM.LAI로 업데이트
        components['canopy'] = Canopy(
            A=self.surface,
            steadystate=False,
            LAI=INITIAL_CONDITIONS['canopy']['LAI']
        ) 

        # 4. Q_rad_CanCov
        components['Q_rad_CanCov'] = Radiation_T4(
            A=self.surface,
            epsilon_a=1.0,
            epsilon_b=INITIAL_CONDITIONS['cover']['epsilon'],
            FFa=components['canopy'].FF,    # 작물 View Factor
            FFb=1.0,     # 외피 View Factor
            FFab1=0.0,   # 임시값, 나중에 pipe_up.FF로 업데이트
            FFab2=0.0,   # 임시값, 나중에 thScreen.FF_ij로 업데이트
        )

        # 5. floor
        components['floor'] = Floor(
            rho=1,     # 밀도 [kg/m³]
            c_p=2e6,   # 비열 [J/(kg·K)]
            A=self.surface,
            V=0.01 * self.surface,  # 부피 [m³]
            steadystate=False
        )

        # 6. Q_rad_FlrCan
        components['Q_rad_FlrCan'] = Radiation_T4(
            A=self.surface,
            epsilon_a=INITIAL_CONDITIONS['floor']['epsilon'],  # 바닥 방사율
            epsilon_b=1.0,   # 작물 방사율
            FFa=1.0,         # 바닥 View Factor
            FFb=components['canopy'].FF,  # 작물 View Factor
            FFab1=0.0  # 임시값, 나중에 pipe_low.FF로 업데이트
        )

        # 7. Q_cnv_CanAir
        components['Q_cnv_CanAir'] = CanopyFreeConvection(
            A=self.surface,
            LAI=components['canopy'].LAI
        )

        # 8. Q_cnv_FlrAir
        components['Q_cnv_FlrAir'] = FreeConvection(
            phi=0,  # 바닥은 수평
            A=self.surface,
            floor=True
        )

        # 9. Q_rad_CovSky
        components['Q_rad_CovSky'] = Radiation_T4(
            A=self.surface,
            epsilon_a=INITIAL_CONDITIONS['cover']['epsilon'],
            epsilon_b=1.0            
        )

        # 10. Q_cnv_CovOut
        components['Q_cnv_CovOut'] = OutsideAirConvection(
            A=self.surface,
            u=self.u_wind,
            phi=0.43633231299858
        )

        # 11. illu - 기본 LAI로 초기화, 나중에 TYM.LAI로 업데이트
        components['illu'] = Illumination(
            A=self.surface,
            power_input=True,
            LAI=INITIAL_CONDITIONS['canopy']['LAI'],  # 기본값, 나중에 TYM.LAI로 업데이트
            P_el=500,  # 전기 소비량 [W]
            p_el=100   # 조명 밀도 [W/m²]
        )

        # 12. Q_rad_FlrCov
        components['Q_rad_FlrCov'] = Radiation_T4(
            A=self.surface,
            epsilon_a=INITIAL_CONDITIONS['floor']['epsilon'],  # 바닥 방사율
            epsilon_b=INITIAL_CONDITIONS['cover']['epsilon'],  # 외피 방사율
            FFa=1.0,         # 바닥 View Factor
            FFb=1.0,         # 외피 View Factor
            FFab1=0.0,       # 임시값, 나중에 pipe_low.FF로 업데이트
            FFab2=components['canopy'].FF,    # 작물 방해
            FFab3=0.0,       # 임시값, 나중에 pipe_up.FF로 업데이트
            FFab4=0.0        # 임시값, 나중에 thScreen.FF_ij로 업데이트
        )

        # 13. MV_CanAir - 기본값으로 초기화, 나중에 업데이트
        components['MV_CanAir'] = MV_CanopyTranspiration(
            A=self.surface,
            LAI=components['canopy'].LAI,
            CO2_ppm=1000,  # 기본값, 나중에 CO2_air.CO2_ppm으로 업데이트
            R_can=0.0,    # 기본값, 나중에 solar_model.R_t_Glob + illu.R_PAR + illu.R_NIR로 업데이트
            T_can=INITIAL_CONDITIONS['canopy']['T']
        )

        # 14. Q_cd_Soil
        components['Q_cd_Soil'] = SoilConduction(
            A=self.surface,
            N_c=2,  # 토양 층 수
            N_s=5,  # 토양 층 수
            lambda_c=1.7,  # 토양 전도도 [W/(m·K)]
            lambda_s=0.85,  # 토양 전도도 [W/(m·K)]
            steadystate=False
        )

        # 15. Q_rad_CanScr
        components['Q_rad_CanScr'] = Radiation_T4(
            A=self.surface,
            epsilon_a=1.0,
            epsilon_b=1.0,
            FFa=components['canopy'].FF,
            FFab1=0.0,  # 임시값, 나중에 pipe_up.FF로 업데이트
            FFb=0.0     # 임시값, 나중에 thScreen.FF_i로 업데이트
        )

        # 16. Q_rad_FlrScr
        components['Q_rad_FlrScr'] = Radiation_T4(
            A=self.surface,
            epsilon_a=INITIAL_CONDITIONS['floor']['epsilon'],  # 바닥 방사율
            epsilon_b=1.0,   # 스크린 방사율
            FFa=1.0,         # 바닥 View Factor
            FFb=0.0,         # 임시값, 나중에 thScreen.FF_i로 업데이트
            FFab1=components['canopy'].FF,    # 작물 방해
            FFab2=0.0,       # 임시값, 나중에 pipe_up.FF로 업데이트
            FFab3=0.0        # 임시값, 나중에 pipe_low.FF로 업데이트
        )

        # 17. thScreen - 기본값으로 초기화, 나중에 SC.y로 업데이트
        components['thScreen'] = ThermalScreen(
            A=self.surface,
            SC=0.0,  # 스크린을 완전히 열어서 하부공기 환기 허용
            steadystate=False
        )

        # 18. Q_rad_ScrCov
        components['Q_rad_ScrCov'] = Radiation_T4(
            A=self.surface,
            epsilon_a=1.0,   # 스크린 방사율
            epsilon_b=INITIAL_CONDITIONS['cover']['epsilon'],  # 외피 방사율
            FFa=0.0,         # 임시값, 나중에 thScreen.FF_i로 업데이트
            FFb=1.0
        )

        # 19. air_Top
        components['air_Top'] = Air_Top(
            steadystate=False,
            steadystateVP=True,
            h_Top=0.4,  # 높이 [m]
            A=self.surface
        )

        # 20. solar_model - 기본값으로 초기화, 나중에 업데이트
        components['solar_model'] = Solar_model(
            A=self.surface,
            LAI=INITIAL_CONDITIONS['canopy']['LAI'],  # 기본값, 나중에 TYM.LAI로 업데이트
            SC=0.0,    # 스크린을 열어서 환기 허용
            I_glob=0.0,  # 초기 일사량
        )

        # 21. pipe_low
        components['pipe_low'] = HeatingPipe(
            d=0.051,  # 직경 [m]
            freePipe=False,
            A=self.surface,
            N=5,      # 파이프 수
            N_p=625,  # 파이프 길이당 단위 수
            l=50      # 길이 [m]
        )

        # 22. Q_rad_LowFlr
        components['Q_rad_LowFlr'] = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=0.89,
            FFa=0.0,  # 임시값, 나중에 pipe_low.FF로 업데이트
            FFb=1.0,
            N=components['pipe_low'].N
        )
        
        # 23. Q_rad_LowCan
        components['Q_rad_LowCan'] = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=1.0,
            FFa=0.0,  # 임시값, 나중에 pipe_low.FF로 업데이트
            FFb=0.0,  # 임시값, 나중에 canopy.FF로 업데이트
            N=components['pipe_low'].N
        )

        # 24. Q_rad_LowCov
        components['Q_rad_LowCov'] = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=0.84,
            FFa=0.0,  # 임시값, 나중에 pipe_low.FF로 업데이트
            FFb=1.0,
            FFab1=0.0,  # 임시값, 나중에 canopy.FF로 업데이트
            FFab2=0.0,  # 임시값, 나중에 pipe_up.FF로 업데이트
            FFab3=0.0,  # 임시값, 나중에 thScreen.FF_ij로 업데이트
            N=components['pipe_low'].N
        )

        # 25. Q_cnv_LowAir
        components['Q_cnv_LowAir'] = PipeFreeConvection_N(
            N=components['pipe_low'].N,
            A=self.surface,
            d=components['pipe_low'].d,
            l=components['pipe_low'].l,
            N_p=components['pipe_low'].N_p,
            freePipe=False
        )

        # 26. Q_rad_LowScr
        components['Q_rad_LowScr'] = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=1.0,
            FFa=0.0,  # 임시값, 나중에 pipe_low.FF로 업데이트
            FFb=0.0,  # 임시값, 나중에 thScreen.FF_i로 업데이트
            FFab1=0.0,  # 임시값, 나중에 canopy.FF로 업데이트
            FFab2=0.0,  # 임시값, 나중에 pipe_up.FF로 업데이트
            N=components['pipe_low'].N
        )

        # 27. pipe_up
        components['pipe_up'] = HeatingPipe(
            d=0.025,  # 직경 [m]
            freePipe=True,
            A=self.surface,
            N=5,      # 파이프 수
            N_p=292,  # 파이프 길이당 단위 수
            l=44      # 길이 [m]
        )

        # 28. Q_rad_UpFlr
        components['Q_rad_UpFlr'] = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=0.89,
            FFb=1.0,
            FFa=0.0,  # 임시값, 나중에 pipe_up.FF로 업데이트
            FFab1=0.0,  # 임시값, 나중에 canopy.FF로 업데이트
            FFab2=0.0,  # 임시값, 나중에 pipe_low.FF로 업데이트
            N=components['pipe_up'].N
        )

        # 29. Q_rad_UpCan
        components['Q_rad_UpCan'] = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=1.0,
            FFa=0.0,  # 임시값, 나중에 pipe_up.FF로 업데이트
            FFb=0.0,  # 임시값, 나중에 canopy.FF로 업데이트
            N=components['pipe_up'].N
        )
        
        # 30. Q_rad_UpCov
        components['Q_rad_UpCov'] = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            epsilon_b=0.84,
            FFb=1.0,
            FFa=0.0,  # 임시값, 나중에 pipe_up.FF로 업데이트
            FFab1=0.0,  # 임시값, 나중에 thScreen.FF_ij로 업데이트
            N=components['pipe_up'].N
        )

        # 31. Q_cnv_UpAir
        components['Q_cnv_UpAir'] = PipeFreeConvection_N(
            N=components['pipe_up'].N,
            A=self.surface,
            d=components['pipe_up'].d,
            l=components['pipe_up'].l,  # 파이프 길이 추가
            N_p=components['pipe_up'].N_p,  # 병렬 파이프 수 추가
            freePipe=components['pipe_up'].freePipe  # 파이프 상태 추가
        )

        # 32. Q_rad_UpScr
        components['Q_rad_UpScr'] = Radiation_N(
            A=self.surface,
            epsilon_a=0.88,
            FFa=0.0,  # 임시값, 나중에 pipe_up.FF로 업데이트
            epsilon_b=1.0,
            FFb=0.0  # 임시값, 나중에 thScreen.FF_i로 업데이트
        )

        # 33. Q_cnv_AirScr
        components['Q_cnv_AirScr'] = Convection_Condensation(
            phi=0,
            A=self.surface,
            floor=False,
            thermalScreen=True,
            Air_Cov=False,
            SC=0.0  # 스크린을 열어서 환기 허용
        )

        # 34. Q_cnv_AirCov
        components['Q_cnv_AirCov'] = Convection_Condensation(
            phi=0.43633231299858,
            A=self.surface,
            floor=False,
            thermalScreen=True,
            Air_Cov=True,
            topAir=False,
            SC=0.0  # 스크린을 열어서 환기 허용
        )

        # 35. Q_cnv_TopCov
        components['Q_cnv_TopCov'] = Convection_Condensation(
            phi=0.43633231299858,
            A=self.surface,
            floor=False,
            thermalScreen=True,
            Air_Cov=True,
            topAir=True,
            SC=0.0  # 스크린을 열어서 환기 허용
        )

        # 36. Q_ven_AirOut
        components['Q_ven_AirOut'] = Ventilation(
            A=self.surface,
            thermalScreen=True,
            topAir=False,
            u=self.u_wind,  # Modelica: u_wind.y
            U_vents=0.0,    # 기본값, 나중에 U_vents.y로 업데이트
            SC=0.0          # 기본값, 나중에 SC.y로 업데이트
        )
        
        # 37. Q_ven_TopOut
        components['Q_ven_TopOut'] = Ventilation(
            A=self.surface,
            thermalScreen=True,
            topAir=True,
            forcedVentilation=False,
            u=self.u_wind,  # Modelica: u_wind.y
            U_vents=0.0,    # 기본값, 나중에 U_vents.y로 업데이트
            SC=0.0          # 기본값, 나중에 SC.y로 업데이트
        )

        # 38. Q_ven_AirTop
        components['Q_ven_AirTop'] = AirThroughScreen(
            A=self.surface,
            W=9.6,  # 스크린 너비 [m]
            K=0.2e-3,  # 스크린 투과도
            SC=0.0  # 기본값, 나중에 SC.y로 업데이트
        )

        # 39. Q_cnv_ScrTop
        components['Q_cnv_ScrTop'] = Convection_Evaporation(
            A=self.surface,
            SC=0.0,  # 기본값, 나중에 SC.y로 업데이트
            MV_AirScr=0.0  # 기본값, 나중에 Q_cnv_AirScr.MV_flow로 업데이트
        )

        # 40. PID_Mdot
        components['PID_Mdot'] = PID(
            PVmin=18 + 273.15,
            PVmax=22 + 273.15,
            PVstart=0.5,
            CSstart=0.5,
            steadyStateInit=False,
            CSmin=0,
            Kp=0.7,
            Ti=600,
            CSmax=86.75
        )

        # 41. TYM - 기본값으로 초기화, 나중에 업데이트
        components['TYM'] = TomatoYieldModel(
            T_canK=INITIAL_CONDITIONS['canopy']['T'],
            LAI_0=INITIAL_CONDITIONS['canopy']['LAI'],  
            C_Leaf_0=40e3,  # 초기 잎 질량 [mg/m²]
            C_Stem_0=30e3,  # 초기 줄기 질량 [mg/m²]
            CO2_air=1000,  # 기본값, 나중에 CO2_air.CO2_ppm으로 업데이트
            R_PAR_can=0,  # 기본값, 나중에 solar_model.R_PAR_Can_umol + illu.R_PAR_Can_umol로 업데이트
            LAI_MAX=3.5   # 최대 LAI
        )

        # 42. CO2_air
        components['CO2_air'] = CO2_Air(
            cap_CO2=components['air'].h_Air,  # 공기 구역 높이를 CO2 저장 용량으로 사용
            steadystate=True
        )

        # 43. CO2_top
        components['CO2_top'] = CO2_Air(
            cap_CO2=0.4,  # Modelica 원본과 정확히 일치
            steadystate=True
        )

        # 44. MC_AirTop
        components['MC_AirTop'] = MC_ventilation2(
            f_vent=0.0  # 기본값, 나중에 Q_ven_AirTop.f_AirTop로 업데이트
        )
        
        # 45. MC_AirOut
        components['MC_AirOut'] = MC_ventilation2(
            f_vent=0.0  # 기본값, 나중에 Q_ven_AirOut.f_vent_total로 업데이트
        )

        # 46. MC_TopOut
        components['MC_TopOut'] = MC_ventilation2(
            f_vent=0.0  # 기본값, 나중에 Q_ven_TopOut.f_vent_total로 업데이트
        )

        # 47. MC_AirCan
        components['MC_AirCan'] = MC_AirCan(
            MC_AirCan=0.0  # 기본값, 나중에 TYM.MC_AirCan_mgCO2m2s로 업데이트
        )

        # 48. MC_ExtAir
        components['MC_ExtAir'] = PrescribedCO2Flow(
            phi_ExtCO2=27
        )

        # 49. CO2out - 외부 CO2 농도 설정
        components['CO2out'] = PrescribedConcentration()

        # 50. PID_CO2
        components['PID_CO2'] = PID(
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

        # 51. sourceMdot_1ry
        components['sourceMdot_1ry'] = SourceMdot(
            T_0=363.15,  # 공급수 온도 [K]
            Mdot_0=0.528   # 초기 유량 [kg/s]
        )
        
        # 52. sinkP_2ry
        components['sinkP_2ry'] = SinkP(
            p0=1000000  # 압력 [Pa]
        )

        # 53. SC
        components['SC'] = Control_ThScreen(
            R_Glob_can=0, 
            R_Glob_can_min=35
        )

        # 54. U_vents
        components['U_vents'] = Uvents_RH_T_Mdot(
            T_air=components['air'].T,
            T_air_sp=293.15,  # 기본값
            Mdot=components['PID_Mdot'].CS,
            RH_air_input=components['air'].RH
        )

        # 55. 센서들
        components['Tair_sensor'] = TemperatureSensor()
        components['Tair_sensor'].port.T = components['air'].T  # 시뮬레이션 루프에서 동기화 필요
        components['RH_air_sensor'] = RHSensor()
        components['RH_out_sensor'] = RHSensor()
        
        return components 