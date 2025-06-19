"""
Greenhouse_1.py

온실 시뮬레이션 모델 (Modelica Greenhouse_1.mo의 Python 구현)
- Venlo-type 온실의 기후 시뮬레이션
- 토마토 작물 재배 (12월 10일 ~ 11월 22일)
- 날씨 데이터: TMY (Typical Meteorological Year) for Brussels
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass

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
from Flows.FluidFlow.Reservoirs.SinkP import SinkP
from Flows.Sensors.RHSensor import RHSensor

# Control Systems
from ControlSystems.PID import PID
from ControlSystems.Climate.Control_ThScreen import Control_ThScreen
from ControlSystems.Climate.Uvents_RH_T_Mdot import Uvents_RH_T_Mdot

# Constants
# Physical constants
GAS_CONSTANT = 8314.0  # Universal gas constant [J/(kmol·K)]
WATER_MOLAR_MASS = 18.0  # Water molar mass [kg/kmol]
LATENT_HEAT_VAPORIZATION = 2.5e6  # Latent heat of vaporization [J/kg]

# Greenhouse dimensions
SURFACE_AREA = 1.4e4  # Greenhouse floor area [m²]

# Temperature limits (in Kelvin)
MIN_TEMPERATURE = 273.15  # 0°C
MAX_TEMPERATURE = 373.15  # 100°C (난방 파이프 온도 허용)

# Initial conditions
INITIAL_CONDITIONS = {
    'air': {
        'T': 293.15,  # 20°C
        'RH': 0.7,    # 70%
        'h_Air': 3.8  # Air height [m]
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

# Control parameters
CONTROL_PARAMS = {
    'temperature': {
        'min': 18 + 273.15,  # 18°C
        'max': 22 + 273.15,  # 22°C
        'Kp': 0.7,
        'Ti': 600
    },
    'co2': {
        'min': 708.1,  # mg/m³
        'max': 1649.0,  # mg/m³
        'Kp': 0.4,
        'Ti': 0.5
    }
}

# Validation thresholds
VALIDATION_THRESHOLDS = {
    'heat_balance': 1000.0,  # Maximum allowed heat imbalance [W]
    'vapor_balance': 0.1,    # Maximum allowed vapor flow imbalance [kg/s]
    'temperature_range': (273.15, 323.15)  # Valid temperature range [K]
}

# File paths
WEATHER_DATA_PATH = "./10Dec-22Nov.txt"
SETPOINT_DATA_PATH = "./SP_10Dec-22Nov.txt"
SCREEN_USABLE_PATH = "./SC_usable_10Dec-22Nov.txt"

class CombiTimeTable:
    """
    Modelica.Blocks.Sources.CombiTimeTable의 Python 구현
    시간에 따른 데이터 테이블을 관리하고 보간을 수행하는 클래스
    """
    def __init__(self, tableOnFile: bool = True, tableName: str = "tab", 
                 columns: Optional[List[int]] = None, fileName: Optional[str] = None):
        """
        Args:
            tableOnFile (bool): 파일에서 데이터를 로드할지 여부
            tableName (str): 테이블 이름
            columns (List[int], optional): 사용할 열 인덱스 목록
            fileName (str, optional): 데이터 파일 경로
        """
        self.tableOnFile = tableOnFile
        self.tableName = tableName
        self.columns = columns or list(range(1, 11))  # 기본값: 1-10 열
        self.fileName = fileName
        self.data = None
        self.load_data()
        
    def load_data(self) -> None:
        """데이터 파일에서 테이블 데이터를 로드"""
        if self.tableOnFile and self.fileName:
            try:
                # 데이터 파일 로드 (탭으로 구분된 텍스트 파일)
                self.data = pd.read_csv(self.fileName, 
                                      delimiter="\t", 
                                      skiprows=2,  # 헤더 2줄 건너뛰기
                                      names=['time'] + [f'col_{i}' for i in self.columns])
            except Exception as e:
                raise RuntimeError(f"데이터 파일 로드 실패: {self.fileName}") from e
        else:
            self.data = pd.DataFrame(columns=['time'] + [f'col_{i}' for i in self.columns])
            
    def get_value(self, time: float, interpolate: bool = False) -> Union[float, List[float]]:
        """
        주어진 시간에 대한 데이터 값을 반환
        
        Args:
            time (float): 조회할 시간
            interpolate (bool): 선형 보간 사용 여부
            
        Returns:
            Union[float, List[float]]: 단일 열인 경우 float, 여러 열인 경우 List[float]
        """
        if self.data is None or len(self.data) == 0:
            raise RuntimeError("데이터가 로드되지 않았습니다")
            
        if time < self.data['time'].min() or time > self.data['time'].max():
            raise ValueError(f"시간 {time}이(가) 데이터 범위를 벗어났습니다")
            
        if interpolate:
            # 선형 보간 수행
            result = []
            for col in [f'col_{i}' for i in self.columns]:
                value = np.interp(time, self.data['time'], self.data[col])
                # nan 값 처리
                if np.isnan(value):
                    value = 0.0
                result.append(value)
        else:
            # 가장 가까운 시간의 값을 반환
            idx = (self.data['time'] - time).abs().idxmin()
            result = []
            for i in self.columns:
                value = self.data.loc[idx, f'col_{i}']
                # nan 값 처리
                if np.isnan(value):
                    value = 0.0
                result.append(value)
            
        return result[0] if len(result) == 1 else result

class TemperatureSensor:
    """
    온도 센서 클래스
    대상 객체의 특정 속성(기본값: 'T')을 모니터링
    """
    def __init__(self, target: object, attr: str = 'T'):
        """
        Args:
            target (object): 온도를 모니터링할 대상 객체
            attr (str): 모니터링할 속성 이름 (기본값: 'T')
        """
        self.target = target
        self.attr = attr
        
    @property
    def T(self) -> float:
        """
        현재 온도 값을 반환
        
        Returns:
            float: 현재 온도 [K]
        """
        return getattr(self.target, self.attr)

class Greenhouse_1:
    """
    Venlo-type 온실 시뮬레이션 모델
    
    주요 기능:
    - 온실 내부 기후 시뮬레이션 (온도, 습도, CO2 농도 등)
    - 열전달 및 질량 전달 계산
    - 제어 시스템 (난방, 환기, CO2 공급, 스크린 등)
    - 작물 생장 모델링
    """
    
    def __init__(self, time_unit_scaling: float = 1.0):
        """온실 시뮬레이션 모델 초기화"""
        self.time_unit_scaling = time_unit_scaling
        self.dt = 0.0  # 시간 간격 초기화
        
        # 날씨 데이터 및 설정값 초기화
        self.T_out = 293.15      # 외부 온도 [K]
        self.T_sky = 293.15      # 하늘 온도 [K]
        self.u_wind = 0.0        # 풍속 [m/s]
        self.I_glob = 0.0        # 일사량 [W/m²]
        self.VP_out = 0.0        # 외부 수증기압 [Pa]
        self.T_air_sp = 293.15   # 공기 온도 설정값 [K]
        self.T_soil7 = 276.15    # 토양 온도 [K]
        self.OnOff = 0.0         # 조명 ON/OFF 신호
        
        # 컴포넌트 초기화
        self._init_components()
        self._init_flows()
        self._init_control_systems()
        self._init_sensors()
        self._init_state_variables()
        
        # 데이터 로더 초기화
        self.weather_data = CombiTimeTable(
            fileName=WEATHER_DATA_PATH,
            columns=list(range(1, 11))  # 날씨 데이터: 시간, 온도, 압력, 풍속, 일사량 등
        )
        
        self.setpoint_data = CombiTimeTable(
            fileName=SETPOINT_DATA_PATH,
            columns=[1, 2, 3]  # 설정값: 시간, 온도, CO2
        )
        
        self.screen_usable_data = CombiTimeTable(
            fileName=SCREEN_USABLE_PATH,
            columns=[1, 2]  # 스크린 사용 가능 시간
        )
        
    def _init_components(self) -> None:
        """온실 구성 요소 초기화"""
        # 커버 (지붕)
        self.cover = Cover(
            rho=2600,  # 밀도 [kg/m³]
            c_p=840,   # 비열 [J/(kg·K)]
            A=SURFACE_AREA,
            steadystate=True,
            h_cov=1e-3,  # 두께 [m]
            phi=0.43633231299858  # 경사각 [rad]
        )
        
        # 공기 (주 구역)
        self.air = Air(
            A=SURFACE_AREA,
            steadystate=True,
            steadystateVP=True,
            h_Air=INITIAL_CONDITIONS['air']['h_Air']
        )
        
        # CO2 공기 모델
        self.CO2_air = CO2_Air(
            cap_CO2=self.air.h_Air,  # 공기 구역 높이를 CO2 저장 용량으로 사용
            CO2_start=400 * 1.94,    # 초기 CO2 농도 (400 ppm을 mg/m³로 변환)
            steadystate=True         # 초기 정상상태 가정
        )
        
        # 작물 캐노피
        self.canopy = Canopy(
            A=SURFACE_AREA,
            steadystate=True,
            LAI=INITIAL_CONDITIONS['canopy']['LAI']
        )
        
        # 바닥
        self.floor = Floor(
            rho=1,     # 밀도 [kg/m³]
            c_p=2e6,   # 비열 [J/(kg·K)]
            A=SURFACE_AREA,
            V=0.01 * SURFACE_AREA,  # 부피 [m³]
            steadystate=True
        )
        
        # 상부 공기 (스크린 위)
        self.air_Top = Air_Top(
            steadystate=True,
            steadystateVP=True,
            h_Top=0.4,  # 높이 [m]
            A=SURFACE_AREA
        )
        
        # 태양광 모델
        self.solar_model = Solar_model(
            A=SURFACE_AREA,
            LAI=self.canopy.LAI,
            SC=0.0,  # 초기 스크린 상태
            I_glob=0.0,  # 초기 일사량
        )
        
        # 난방 파이프 (하부)
        self.pipe_low = HeatingPipe(
            d=0.051,  # 직경 [m]
            freePipe=False,
            A=SURFACE_AREA,
            N=5,      # 파이프 수
            N_p=625,  # 파이프 길이당 단위 수
            l=50      # 길이 [m]
        )
        
        # 난방 파이프 (상부)
        self.pipe_up = HeatingPipe(
            d=0.025,  # 직경 [m]
            freePipe=True,
            A=SURFACE_AREA,
            N=5,      # 파이프 수
            N_p=292,  # 파이프 길이당 단위 수
            l=44      # 길이 [m]
        )
        
        # 보조 조명
        self.illu = Illumination(
            A=SURFACE_AREA,
            power_input=True,
            LAI=self.canopy.LAI,
            P_el=500,  # 전기 소비량 [W]
            p_el=100   # 조명 밀도 [W/m²]
        )
        
        # 스크린
        self.thScreen = ThermalScreen(
            A=SURFACE_AREA,
            SC=0.0,  # 초기 스크린 상태
            steadystate=False
        )
        
        # 토마토 생장 모델
        self.TYM = TomatoYieldModel(
            T_canK=self.canopy.T,
            LAI_0=self.canopy.LAI,  
            C_Leaf_0=40e3,  # 초기 잎 질량 [mg/m²]
            C_Stem_0=30e3,  # 초기 줄기 질량 [mg/m²]
            CO2_air=400,  # 초기 CO2 농도 [ppm]
            LAI_MAX=2.7   # 최대 LAI
        )
        
    def _init_flows(self) -> None:
        """유량 관련 컴포넌트 초기화"""
        # 1. 환기 시스템 초기화
        self.Q_ven_AirOut = Ventilation(
            A=SURFACE_AREA,
            thermalScreen=self.thScreen,
            topAir=False
        )
        
        self.Q_ven_TopOut = Ventilation(
            A=SURFACE_AREA,
            thermalScreen=self.thScreen,
            topAir=True
        )
        
        # 2. 대류 및 증발/응결 시스템 초기화 - 별도 컴포넌트로 분리
        # Air ↔ Screen 대류
        self.Q_cnv_AirScr = Convection_Evaporation(
            A=SURFACE_AREA,
            SC=self.thScreen.SC
        )
        
        # Top Air ↔ Cover 대류
        self.Q_cnv_TopCov = Convection_Condensation(
            phi=self.cover.phi,
            A=SURFACE_AREA,
            floor=False,
            thermalScreen=self.thScreen,
            Air_Cov=True,
            topAir=True,
            SC=self.thScreen.SC
        )
        
        # Screen ↔ Top Air 대류
        self.Q_cnv_ScrTop = Convection_Evaporation(
            A=SURFACE_AREA,
            SC=self.thScreen.SC
        )
        
        # Air ↔ Cover 대류
        self.Q_cnv_AirCov = Convection_Condensation(
            phi=self.cover.phi,
            A=SURFACE_AREA,
            floor=False,
            thermalScreen=self.thScreen,
            Air_Cov=True,
            topAir=False,
            SC=self.thScreen.SC
        )
        
        # Air ↔ Floor 대류
        self.Q_cnv_AirFlr = Convection_Condensation(
            phi=self.cover.phi,
            A=SURFACE_AREA,
            floor=True,
            thermalScreen=self.thScreen,
            Air_Cov=False,
            topAir=False,
            SC=self.thScreen.SC
        )
        
        # 3. 스크린을 통한 공기 흐름 초기화
        self.Q_ven_AirTop = AirThroughScreen(
            A=SURFACE_AREA,
            W=9.6,  # 스크린 너비 [m]
            K=0.2e-3,  # 스크린 투과도
            SC=self.thScreen.SC
        )
        
        # 4. 복사 열전달 초기화
        self.Q_rad_LowFlr = Radiation_N(
            N=5,  # 파이프 수
            A=SURFACE_AREA,
            epsilon_a=0.88,  # 파이프 방사율
            epsilon_b=0.89   # 바닥 방사율
        )
        # View Factor 설정 (원본 Modelica 모델과 동일)
        self.Q_rad_LowFlr.FFa = self.pipe_low.FF
        self.Q_rad_LowFlr.FFb = 1.0
        
        self.Q_rad_LowCan = Radiation_N(
            N=5,
            A=SURFACE_AREA,
            epsilon_a=0.88,  # 파이프 방사율
            epsilon_b=1.0    # 작물 방사율
        )
        # View Factor 설정
        self.Q_rad_LowCan.FFa = self.pipe_low.FF
        self.Q_rad_LowCan.FFb = self.canopy.FF
        
        self.Q_rad_LowCov = Radiation_N(
            N=5,
            A=SURFACE_AREA,
            epsilon_a=0.88,  # 파이프 방사율
            epsilon_b=0.84   # 외피 방사율
        )
        # View Factor 설정
        self.Q_rad_LowCov.FFa = self.pipe_low.FF
        self.Q_rad_LowCov.FFb = 1.0
        self.Q_rad_LowCov.FFab1 = self.canopy.FF
        self.Q_rad_LowCov.FFab2 = self.pipe_up.FF
        self.Q_rad_LowCov.FFab3 = self.thScreen.FF_ij
        
        self.Q_rad_LowScr = Radiation_N(
            N=5,
            A=SURFACE_AREA,
            epsilon_a=0.88,  # 파이프 방사율
            epsilon_b=1.0    # 스크린 방사율
        )
        # View Factor 설정
        self.Q_rad_LowScr.FFa = self.pipe_low.FF
        self.Q_rad_LowScr.FFb = self.thScreen.FF_i
        self.Q_rad_LowScr.FFab1 = self.canopy.FF
        self.Q_rad_LowScr.FFab2 = self.pipe_up.FF
        
        # 누락된 바닥→스크린 복사 추가
        self.Q_rad_FlrScr = Radiation_T4(
            A=SURFACE_AREA,
            epsilon_a=0.89,  # 바닥 방사율
            epsilon_b=1.0,   # 스크린 방사율
            FFa=1.0,         # 바닥 View Factor
            FFb=self.thScreen.FF_i,  # 스크린 View Factor
            FFab1=self.canopy.FF,    # 작물 방해
            FFab2=self.pipe_up.FF,   # 상부파이프 방해
            FFab3=self.pipe_low.FF   # 하부파이프 방해
        )
        
        self.Q_rad_UpFlr = Radiation_N(
            N=5,
            A=SURFACE_AREA,
            epsilon_a=0.88,  # 파이프 방사율
            epsilon_b=0.89   # 바닥 방사율
        )
        # View Factor 설정
        self.Q_rad_UpFlr.FFa = self.pipe_up.FF
        self.Q_rad_UpFlr.FFb = 1.0
        self.Q_rad_UpFlr.FFab1 = self.canopy.FF
        self.Q_rad_UpFlr.FFab2 = self.pipe_low.FF
        
        self.Q_rad_UpCan = Radiation_N(
            N=5,
            A=SURFACE_AREA,
            epsilon_a=0.88,  # 파이프 방사율
            epsilon_b=1.0    # 작물 방사율
        )
        # View Factor 설정
        self.Q_rad_UpCan.FFa = self.pipe_up.FF
        self.Q_rad_UpCan.FFb = self.canopy.FF
        
        self.Q_rad_UpCov = Radiation_N(
            N=5,
            A=SURFACE_AREA,
            epsilon_a=0.88,  # 파이프 방사율
            epsilon_b=0.84   # 외피 방사율
        )
        # View Factor 설정
        self.Q_rad_UpCov.FFa = self.pipe_up.FF
        self.Q_rad_UpCov.FFb = 1.0
        self.Q_rad_UpCov.FFab1 = self.thScreen.FF_ij
        
        self.Q_rad_UpScr = Radiation_N(
            N=5,
            A=SURFACE_AREA,
            epsilon_a=0.88,  # 파이프 방사율
            epsilon_b=1.0    # 스크린 방사율
        )
        # View Factor 설정
        self.Q_rad_UpScr.FFa = self.pipe_up.FF
        self.Q_rad_UpScr.FFb = self.thScreen.FF_i
        
        # 5. 대류 열전달 초기화
        self.Q_cnv_LowAir = PipeFreeConvection_N(
            N=5,
            A=SURFACE_AREA,
            d=self.pipe_low.d,
            l=self.pipe_low.l,  # 파이프 길이 추가
            N_p=self.pipe_low.N_p,  # 병렬 파이프 수 추가
            freePipe=self.pipe_low.freePipe  # 파이프 상태 추가
        )
        
        self.Q_cnv_UpAir = PipeFreeConvection_N(
            N=5,
            A=SURFACE_AREA,
            d=self.pipe_up.d,
            l=self.pipe_up.l,  # 파이프 길이 추가
            N_p=self.pipe_up.N_p,  # 병렬 파이프 수 추가
            freePipe=self.pipe_up.freePipe  # 파이프 상태 추가
        )
        
        # 6. 토양 전도 초기화
        self.Q_cd_Soil = SoilConduction(
            A=SURFACE_AREA,
            N_c=2,  # 토양 층 수
            N_s=5,  # 토양 층 수
            lambda_c=1.7,  # 토양 전도도 [W/(m·K)]
            lambda_s=0.85,  # 토양 전도도 [W/(m·K)]
            steadystate=False
        )
        
        # 7. 작물 증산 초기화
        self.MV_CanAir = MV_CanopyTranspiration(
            A=SURFACE_AREA,
            LAI=self.canopy.LAI,
            CO2_ppm=self.CO2_air.CO2_ppm,
            R_can=self.solar_model.R_t_Glob,
            T_can=self.canopy.T
        )
        
        self.MC_AirCan = MC_AirCan(
            MC_AirCan=self.TYM.MC_AirCan_mgCO2m2s
        )
        
        self.MC_AirTop = MC_ventilation2(
            f_vent=self.Q_ven_AirTop.f_AirTop
        )
        
        self.MC_AirOut = MC_ventilation2(
            f_vent=self.Q_ven_AirOut.f_vent_total
        )
        
        self.MC_TopOut = MC_ventilation2(
            f_vent=self.Q_ven_TopOut.f_vent_total
        )
        
        # 9. 외부 공기 소스/싱크 초기화
        self.sourceMdot_1ry = SourceMdot(
            T_0=353.15,  # 공급수 온도 [K]
            Mdot_0=0.0   # 초기 유량 [kg/s]
        )
        
        self.sinkP_2ry = SinkP(
            p0=1e6  # 압력 [Pa]
        )
        
        # 10. 작물 자유 대류 초기화
        self.Q_cnv_CanAir = CanopyFreeConvection(
            A=SURFACE_AREA,
            LAI=self.canopy.LAI
        )
        
        # 11. 외부 공기 대류 초기화
        self.Q_cnv_OutAir = OutsideAirConvection(
            A=SURFACE_AREA,
            u=self.u_wind,
            phi=self.cover.phi
        )
        
        # 12. 외부 공기 자유 대류 초기화
        self.Q_cnv_OutAirFree = FreeConvection(
            A=SURFACE_AREA,
            phi=self.cover.phi
        )
        
        # 13. Radiation_T4 컴포넌트들 초기화
        # 작물과 외피 사이의 복사
        self.Q_rad_CanCov = Radiation_T4(
            A=SURFACE_AREA,
            epsilon_a=1.0,
            epsilon_b=0.84
        )
        
        # 작물과 스크린 사이의 복사
        self.Q_rad_CanScr = Radiation_T4(
            A=SURFACE_AREA,
            epsilon_a=1.0,
            epsilon_b=1.0,
            FFa=self.canopy.FF,
            FFb=self.thScreen.FF_i,
            FFab1=self.pipe_up.FF
        )
        
        # 외피와 하늘 사이의 복사
        self.Q_rad_CovSky = Radiation_T4(
            A=SURFACE_AREA,
            epsilon_a=0.84,
            epsilon_b=1.0
        )
        
        # 스크린 → 외피 복사 추가 (누락됨)
        self.Q_rad_ScrCov = Radiation_T4(
            A=SURFACE_AREA,
            epsilon_a=1.0,   # 스크린 방사율
            epsilon_b=0.84,  # 외피 방사율
            FFa=self.thScreen.FF_i,
            FFb=1.0
        )
    
    def _init_control_systems(self) -> None:
        """제어 시스템 초기화"""
        # 온도 제어 (PID)
        self.PID_Mdot = PID(
            PVmin=CONTROL_PARAMS['temperature']['min'],
            PVmax=CONTROL_PARAMS['temperature']['max'],
            PVstart=0.5,
            CSstart=0.5,
            steadyStateInit=False,
            CSmin=0,
            Kp=CONTROL_PARAMS['temperature']['Kp'],
            Ti=CONTROL_PARAMS['temperature']['Ti'],
            CSmax=86.75
        )
        
        # CO2 제어 (PID)
        self.PID_CO2 = PID(
            PVstart=0.5,
            CSstart=0.5,
            steadyStateInit=False,
            PVmin=CONTROL_PARAMS['co2']['min'],
            PVmax=CONTROL_PARAMS['co2']['max'],
            CSmin=0,
            CSmax=1,
            Kp=CONTROL_PARAMS['co2']['Kp'],
            Ti=CONTROL_PARAMS['co2']['Ti']
        )
        
        # 스크린 제어
        self.SC = Control_ThScreen(
            R_Glob_can=0,  # 초기값, 실제 값은 시뮬레이션 중 업데이트
            R_Glob_can_min=35
        )
        
        # 환기 제어
        self.U_vents = Uvents_RH_T_Mdot()  # 매개변수 없이 초기화
        self.U_vents.T_air = self.air.T  # 초기화 후 속성 설정
        self.U_vents.T_air_sp = 293.15  # 초기 온도 설정값
        self.U_vents.Mdot = 0.528  # 초기 질량 유량
        
    def _init_sensors(self) -> None:
        """센서 초기화"""
        self.Tair_sensor = TemperatureSensor(self.air)
        self.RH_air_sensor = RHSensor()
        self.RH_out_sensor = RHSensor()
        
    def _init_state_variables(self) -> None:
        """상태 변수 초기화"""
        # 에너지 관련 변수
        self.q_low = 0.0  # 하부 난방 열유속 [W/m²]
        self.q_up = 0.0   # 상부 난방 열유속 [W/m²]
        self.q_tot = 0.0  # 총 난방 열유속 [W/m²]
        
        self.E_th_tot_kWhm2 = 0.0  # 단위 면적당 총 열에너지 [kWh/m²]
        self.E_th_tot = 0.0        # 총 열에너지 [kWh]
        
        # 전기 관련 변수
        self.W_el_illu = 0.0       # 조명 전력 [kWh/m²]
        self.E_el_tot_kWhm2 = 0.0  # 단위 면적당 총 전기 에너지 [kWh/m²]
        self.E_el_tot = 0.0        # 총 전기 에너지 [kWh]
        
        # 작물 관련 변수
        self.DM_Har = 0.0  # 수확된 건물중 [mg/m²]
        
        # 디버깅 변수
        self._first_step = False
    
    def _set_environmental_conditions(self, weather: List[float]) -> None:
        """
        외부 환경 조건을 설정합니다.
        
        Args:
            weather (List[float]): 날씨 데이터 [시간, 온도, 습도, 압력, 일사량, 풍속, 하늘온도, ...]
        """
        # 외부 온도 [K]
        self.T_out = weather[1] + 273.15
        
        # 하늘 온도 [K]
        self.T_sky = weather[6] + 273.15
        
        # 풍속 [m/s]
        self.u_wind = weather[5]
        
        # 일사량 [W/m²]
        self.I_glob = weather[4]
        
        # 외부 수증기압 [Pa] (상대습도와 온도로부터 계산)
        self.VP_out = weather[2] * 100  # 상대습도(%)를 수증기압(Pa)으로 변환
        
        # 조명 ON/OFF 신호
        self.OnOff = weather[9]
        
        # 태양광 모델 업데이트
        self.solar_model.I_glob = self.I_glob
        
        # 외부 CO2 농도 [mg/m³]
        self.CO2_out = 340 * 1.94  # 340 ppm을 mg/m³로 변환

    def _update_setpoints(self, setpoint: List[float]) -> None:
        """
        설정값을 업데이트합니다.
        
        Args:
            setpoint (List[float]): 설정값 데이터 [시간, 온도, CO2, ...]
        """
        # 공기 온도 설정값 [K]
        self.T_air_sp = setpoint[1] + 273.15
        
        # CO2 설정값 [mg/m³]
        self.CO2_sp = setpoint[2] * 1.94  # ppm을 mg/m³로 변환

    def step(self, dt: float, time_idx: int) -> None:
        """시뮬레이션 스텝 실행"""
        self.dt = dt  # 시간 간격 업데이트
        
        # 현재 시간의 기상 데이터와 설정값 가져오기
        weather = self.weather_data.get_value(time_idx * dt)
        setpoint = self.setpoint_data.get_value(time_idx * dt)
        sc_usable = self.screen_usable_data.get_value(time_idx * dt)
        
        # 외부 환경 조건 및 설정값 업데이트
        self._set_environmental_conditions(weather)
        self._update_setpoints(setpoint)
        
        # 스크린 온도 디버깅 - 스텝 시작 시
        if time_idx == 0:
            print(f"스텝 시작 시 스크린 온도: {self.thScreen.T - 273.15:.1f}°C")
        
        # 하위 스텝 반복
        for _ in range(max(1, int(dt / 60))):
            # 1. 구성 요소 업데이트
            self._update_components(dt, weather, setpoint)
            
            # 2. 포트 연결 업데이트
            self._update_port_connections_ports_only(dt)
            
            # 3. 열전달 계산
            self._update_heat_transfer(dt)
            
            # 4. 제어 시스템 업데이트
            self._update_control_systems(dt, weather, setpoint, sc_usable)
            
            # 5. 구성 요소 상태 업데이트
            # 5.1 공기 상태 업데이트
            self.air.step(dt)
            self.air_Top.step(dt)
            
            # 5.2 외피 상태 업데이트
            self.cover.step(dt)
            
            # 5.3 작물 상태 업데이트
            self.canopy.step(dt)
            
            # 5.4 바닥 상태 업데이트
            self.floor.step(dt)
            
            # 5.5 보온 스크린 상태 업데이트 - 디버깅 추가
            old_screen_temp = self.thScreen.T
            self.thScreen.step(dt)
            
            # 스크린 열용량 디버깅 (온도 변화 직후)
            screen_mass = self.thScreen.rho * self.thScreen.h * self.thScreen.A
            screen_heat_capacity = screen_mass * self.thScreen.c_p
            temp_change = self.thScreen.T - old_screen_temp
            
            print(f"스크린 열용량 디버깅:")
            print(f"  스크린 질량: {screen_mass:.6f} kg")
            print(f"  스크린 열용량: {screen_heat_capacity:.2f} J/K")
            print(f"  온도 변화: {temp_change:.2f} K")
            print(f"  열유속: {self.thScreen.Q_flow:.2f} W")
            print(f"  예상 온도 변화: {self.thScreen.Q_flow * dt / screen_heat_capacity:.2f} K")
            
            if abs(self.thScreen.T - old_screen_temp) > 10:  # 10K 이상 변화
                print(f"스크린 온도 급격한 변화: {old_screen_temp - 273.15:.1f}°C → {self.thScreen.T - 273.15:.1f}°C")
                print(f"스크린 열유속: {self.thScreen.Q_flow:.2f} W")
            
            # 5.6 CO2 상태 업데이트
            self.CO2_air.step(dt)
            
            # 5.7 난방 파이프 상태 업데이트
            self.pipe_low.step(dt)
            self.pipe_up.step(dt)
            
            # 5.8 조명 상태 업데이트
            self.illu.step(dt)
            
            # 5.9 태양광 모델 업데이트
            self.solar_model.step(dt)
            
            # 6. 에너지 흐름 계산
            self._calculate_energy_flows(dt)
            
            # 7. 상태 검증
            try:
                self._verify_state()
            except ValueError as e:
                raise ValueError(f"상태 검증 실패: {str(e)}")
    
    def _update_components(self, dt: float, weather: List[float], setpoint: List[float]) -> None:
        """컴포넌트 상태를 업데이트합니다."""
        # 1. 환경 조건 설정
        self._set_environmental_conditions(weather)
        
        # 2. 설정점 업데이트
        self._update_setpoints(setpoint)
        
        # 3. 컴포넌트 스텝 실행
        self.air.step(dt)
        self.air_Top.step(dt)  
        self.cover.step(dt)
        self.floor.step(dt)
        self.canopy.step(dt)  # FF 계산이 포함됨
        self.thScreen.step(dt)  # FF_i, FF_ij 업데이트
        self.pipe_low.step(dt)
        self.pipe_up.step(dt)
        
        # 4. View Factor 기반 복사 열전달 계수 업데이트
        self._update_radiation_coefficients()
        
        # 5. 상태 검증
        self._validate_component_states()
    
    def _validate_component_states(self) -> None:
        """
        구성 요소들의 상태가 유효한 범위 내에 있는지 검증합니다.
        경고 메시지를 출력하지만 예외는 발생시키지 않습니다.
        """
        # 온도 검증
        for component, name in [
            (self.air, "공기"),
            (self.air_Top, "상부 공기"),
            (self.canopy, "작물"),
            (self.cover, "외피"),
            (self.floor, "바닥"),
            (self.thScreen, "보온 스크린")
        ]:
            if component.T < MIN_TEMPERATURE or component.T > MAX_TEMPERATURE:
                print(f"경고: {name} 온도가 범위를 벗어났습니다: {component.T - 273.15:.1f}°C")
        
        # 수증기압 검증
        for component, name in [
            (self.air.massPort, "공기"),
            (self.air_Top.massPort, "상부 공기"),
            (self.cover.massPort, "외피"),
            (self.thScreen.massPort, "보온 스크린"),
            (self.canopy.massPort, "작물")
        ]:
            if component.VP < 0:
                print(f"경고: {name} 수증기압이 음수입니다: {component.VP:.1f} Pa")
        
        # CO2 농도 검증
        if self.CO2_air.CO2 < 0:
            print(f"경고: CO2 농도가 음수입니다: {self.CO2_air.CO2:.1f} mg/m³")
        
        # 스크린 개도 검증
        if self.thScreen.SC < 0 or self.thScreen.SC > 1:
            print(f"경고: 스크린 개도가 범위를 벗어났습니다: {self.thScreen.SC:.2f}")

    def _update_port_connections_ports_only(self, dt: float) -> None:
        """
        모든 포트 연결을 업데이트합니다.
        
        Args:
            dt (float): 시간 간격 [s]
        """
        # 1. 열 포트 연결 업데이트
        self._update_heat_ports()
        
        # 2. 질량 포트 연결 업데이트
        self._update_mass_ports()
        
        # 3. 복사 포트 연결 업데이트
        self._update_radiation_ports()
    
    def _update_heat_ports(self) -> None:
        """열 포트 연결을 업데이트합니다."""
        # Air ↔ Screen 대류
        self.Q_cnv_AirScr.heatPort_a.T = self.air.T
        self.Q_cnv_AirScr.heatPort_b.T = self.thScreen.T
        
        # Top Air ↔ Cover 대류
        self.Q_cnv_TopCov.heatPort_a.T = self.air_Top.T
        self.Q_cnv_TopCov.heatPort_b.T = self.cover.T
        
        # Screen ↔ Top Air 대류
        self.Q_cnv_ScrTop.heatPort_a.T = self.thScreen.T
        self.Q_cnv_ScrTop.heatPort_b.T = self.air_Top.T
        
        # Air ↔ Cover 대류
        self.Q_cnv_AirCov.heatPort_a.T = self.air.T
        self.Q_cnv_AirCov.heatPort_b.T = self.cover.T
        
        # Air ↔ Floor 대류
        self.Q_cnv_AirFlr.heatPort_a.T = self.air.T
        self.Q_cnv_AirFlr.heatPort_b.T = self.floor.T
        
        # 외부 공기와 외피 사이의 대류
        self.Q_cnv_OutAir.port_a.T = self.cover.T
        self.Q_cnv_OutAir.port_b.T = self.T_out
    
    def _update_mass_ports(self) -> None:
        """질량 포트 연결을 업데이트합니다."""
        # Air ↔ Screen 대류
        self.Q_cnv_AirScr.massPort_a.VP = self.air.massPort.VP
        self.Q_cnv_AirScr.massPort_b.VP = self.thScreen.massPort.VP
        
        # Top Air ↔ Cover 대류
        self.Q_cnv_TopCov.massPort_a.VP = self.air_Top.massPort.VP
        self.Q_cnv_TopCov.massPort_b.VP = self.cover.massPort.VP
        
        # Screen ↔ Top Air 대류
        self.Q_cnv_ScrTop.massPort_a.VP = self.thScreen.massPort.VP
        self.Q_cnv_ScrTop.massPort_b.VP = self.air_Top.massPort.VP
        
        # Air ↔ Cover 대류
        self.Q_cnv_AirCov.massPort_a.VP = self.air.massPort.VP
        self.Q_cnv_AirCov.massPort_b.VP = self.cover.massPort.VP
        
        # 작물과 공기 사이의 질량 포트 (증산)
        self.MV_CanAir.port_a.VP = self.canopy.massPort.VP
        self.MV_CanAir.port_b.VP = self.air.massPort.VP
        
        # 환기 관련 질량 포트
        self.Q_ven_AirOut.MassPort_a.VP = self.air.massPort.VP
        self.Q_ven_AirOut.MassPort_b.VP = self.VP_out
        
        self.Q_ven_TopOut.MassPort_a.VP = self.air_Top.massPort.VP
        self.Q_ven_TopOut.MassPort_b.VP = self.VP_out
        
        self.Q_ven_AirTop.MassPort_a.VP = self.air.massPort.VP
        self.Q_ven_AirTop.MassPort_b.VP = self.air_Top.massPort.VP
    
    def _update_radiation_ports(self) -> None:
        """복사 포트 연결을 업데이트합니다."""
        # 작물과 외피 사이의 복사
        self.Q_rad_CanCov.port_a.T = self.canopy.T
        self.Q_rad_CanCov.port_b.T = self.cover.T
        
        # 작물과 스크린 사이의 복사
        self.Q_rad_CanScr.port_a.T = self.canopy.T
        self.Q_rad_CanScr.port_b.T = self.thScreen.T
        
        # 외피와 하늘 사이의 복사
        self.Q_rad_CovSky.port_a.T = self.cover.T
        self.Q_rad_CovSky.port_b.T = self.T_sky

        # 바닥 → 스크린 복사 올바른 연결
        self.Q_rad_FlrScr.port_a.T = self.floor.T      # 바닥 온도
        self.Q_rad_FlrScr.port_b.T = self.thScreen.T   # 스크린 온도

        self.Q_rad_FlrScr.FFa = 1.0  # 바닥 전체 표면
        self.Q_rad_FlrScr.FFb = self.thScreen.FF_i  # 스크린 하부면
        
        # 난방 파이프 관련 복사 포트
        self._update_pipe_radiation_ports()
    
    def _update_pipe_radiation_ports(self) -> None:
        """난방 파이프 관련 복사 열전달을 계산합니다."""
        # 하부 파이프 복사
        for port in self.Q_rad_LowFlr.heatPorts_a:
            port.T = self.pipe_low.T
            
        for port in self.Q_rad_LowCan.heatPorts_a:
            port.T = self.pipe_low.T
            
        for port in self.Q_rad_LowCov.heatPorts_a:
            port.T = self.pipe_low.T
            
        for port in self.Q_rad_LowScr.heatPorts_a:
            port.T = self.pipe_low.T
        
        # 상부 파이프 복사
        for port in self.Q_rad_UpFlr.heatPorts_a:
            port.T = self.pipe_up.T
            
        for port in self.Q_rad_UpCan.heatPorts_a:
            port.T = self.pipe_up.T
            
        for port in self.Q_rad_UpCov.heatPorts_a:
            port.T = self.pipe_up.T
            
        for port in self.Q_rad_UpScr.heatPorts_a:
            port.T = self.pipe_up.T
            
        # 복사 포트 b 연결 (스크린, 바닥, 작물, 외피)
        self.Q_rad_LowScr.port_b.T = self.thScreen.T
        self.Q_rad_LowFlr.port_b.T = self.floor.T
        self.Q_rad_LowCan.port_b.T = self.canopy.T
        self.Q_rad_LowCov.port_b.T = self.cover.T
        
        self.Q_rad_UpScr.port_b.T = self.thScreen.T
        self.Q_rad_UpFlr.port_b.T = self.floor.T
        self.Q_rad_UpCan.port_b.T = self.canopy.T
        self.Q_rad_UpCov.port_b.T = self.cover.T
            
    def _update_heat_transfer(self, dt: float) -> None:
        """
        모든 열전달 과정을 계산합니다.
        
        Args:
            dt (float): 시간 간격 [s]
        """
        # 1. 대류 열전달 계산
        self._calculate_convection()
        
        # 2. 복사 열전달 계산
        self._calculate_radiation()
        
        # 3. 전도 열전달 계산
        self._calculate_conduction()
        
        # 4. 잠열 계산
        self._calculate_latent_heat()
        
        # 5. 구성 요소별 열 균형 계산
        self._calculate_component_heat_balance()
    
    def _calculate_convection(self) -> None:
        """대류 열전달을 계산합니다."""
        # Air ↔ Screen 대류
        self.Q_cnv_AirScr.step()
        
        # Top Air ↔ Cover 대류
        self.Q_cnv_TopCov.step()
        
        # Screen ↔ Top Air 대류
        self.Q_cnv_ScrTop.step()
        
        # Air ↔ Cover 대류
        self.Q_cnv_AirCov.step()
        
        # Air ↔ Floor 대류
        self.Q_cnv_AirFlr.step()
        
        # 외부 공기와 외피 사이의 대류
        self.Q_cnv_OutAir.step()
        
        # 외부 공기 자유 대류
        self.Q_cnv_OutAirFree.step()
        
        # 작물과 공기 사이의 자유 대류
        self.Q_cnv_CanAir.step()
        
        # 난방 파이프와 공기 사이의 대류
        self.Q_cnv_LowAir.step()
        self.Q_cnv_UpAir.step()
    
    def _calculate_radiation(self) -> None:
        """복사 열전달을 계산합니다."""
        # 작물과 외피 사이의 복사
        self.Q_rad_CanCov.step()
        
        # 작물과 스크린 사이의 복사
        self.Q_rad_CanScr.step()
        
        # 외피와 하늘 사이의 복사
        self.Q_rad_CovSky.step()
        
        # 난방 파이프 관련 복사
        self._calculate_pipe_radiation()
    
    def _calculate_pipe_radiation(self) -> None:
        """난방 파이프 관련 복사 열전달을 계산합니다."""
        # 하부 파이프 복사
        self.Q_rad_LowFlr.step()
        self.Q_rad_LowCan.step()
        self.Q_rad_LowCov.step()
        self.Q_rad_LowScr.step()
        
        # 상부 파이프 복사
        self.Q_rad_UpFlr.step()
        self.Q_rad_UpCan.step()
        self.Q_rad_UpCov.step()
        self.Q_rad_UpScr.step()
        
        # 바닥→스크린 복사 (누락된 부분)
        self.Q_rad_FlrScr.step()
    
    def _calculate_conduction(self) -> None:
        """전도 열전달을 계산합니다."""
        # 바닥과 토양 사이의 전도
        self.Q_cd_Soil.step(dt=self.dt)  # dt 인자 추가
    
    def _calculate_latent_heat(self) -> None:
        """잠열을 계산합니다."""
        # 작물 증산에 의한 잠열
        MV_flow_transpiration = self.MV_CanAir.step()
        latent_heat_transpiration = MV_flow_transpiration * LATENT_HEAT_VAPORIZATION
        
        # 작물 열 균형에 잠열 추가
        self.canopy.Q_flow -= latent_heat_transpiration
    
    def _calculate_component_heat_balance(self) -> None:
        """각 구성 요소의 열 균형을 계산합니다."""
        # 공기 열 균형
        self.air.Q_flow = (
            self.Q_cnv_AirScr.Q_flow +
            self.Q_cnv_AirCov.Q_flow +
            self.Q_cnv_AirFlr.Q_flow +
            self.Q_cnv_LowAir.Q_flow +
            self.Q_cnv_UpAir.Q_flow +
            self.Q_cnv_CanAir.Q_flow +
            self.Q_ven_AirOut.Q_flow +
            self.Q_ven_AirTop.Q_flow
        )
        
        # 상부 공기 열 균형
        self.air_Top.Q_flow = (
            self.Q_cnv_TopCov.Q_flow +
            self.Q_cnv_ScrTop.Q_flow +
            self.Q_ven_TopOut.Q_flow -
            self.Q_ven_AirTop.Q_flow
        )
        
        # 외피 열 균형
        self.cover.Q_flow = (
            self.Q_cnv_AirCov.Q_flow +
            self.Q_cnv_TopCov.Q_flow +
            self.Q_cnv_OutAir.Q_flow +
            self.Q_cnv_OutAirFree.Q_flow +
            self.Q_rad_CovSky.Q_flow
        )
        
        # 작물 열 균형
        self.canopy.Q_flow = (
            self.Q_cnv_CanAir.Q_flow +
            self.Q_rad_CanCov.Q_flow +
            self.Q_rad_CanScr.Q_flow +
            self.Q_rad_LowCan.Q_flow +
            self.Q_rad_UpCan.Q_flow
        )
        
        # 바닥 열 균형
        self.floor.Q_flow = (
            self.Q_cnv_AirFlr.Q_flow +
            self.Q_cd_Soil.Q_flow +
            self.Q_rad_LowFlr.Q_flow +
            self.Q_rad_UpFlr.Q_flow -
            self.Q_rad_FlrScr.Q_flow  # 바닥→스크린 복사 (바닥에서 나가는 열)
        )
        
        # 보온 스크린 열 균형 - 디버깅 추가
        screen_heat_flows = {
            # 유입 (+): 하부 구성요소에서 스크린으로
            'Q_rad_CanScr': +self.Q_rad_CanScr.Q_flow,    # 작물 → 스크린
            'Q_rad_LowScr': +self.Q_rad_LowScr.Q_flow,    # 하부파이프 → 스크린  
            'Q_rad_UpScr': +self.Q_rad_UpScr.Q_flow,      # 상부파이프 → 스크린
            'Q_rad_FlrScr': +self.Q_rad_FlrScr.Q_flow,    # 바닥 → 스크린
            'Q_cnv_AirScr': +self.Q_cnv_AirScr.Q_flow,    # 공기 → 스크린 대류
            
            # 유출 (-): 스크린에서 상부로  
            'Q_cnv_ScrTop': -self.Q_cnv_ScrTop.Q_flow,    # 스크린 → 상부공기
            'Q_rad_ScrCov': -self.Q_rad_ScrCov.Q_flow     # 스크린 → 외피 (추가 필요)
        }
        
        self.thScreen.Q_flow = sum(screen_heat_flows.values())
        
        # 스크린 온도가 비정상적일 때 디버깅 출력
        if abs(self.thScreen.Q_flow) > 10000:  # 10kW 이상
            print(f"스크린 과도한 열유속 감지: {self.thScreen.Q_flow:.2f} W")
            for name, value in screen_heat_flows.items():
                print(f"  {name}: {value:.2f} W")
    
    def _update_control_systems(self, dt: float, weather: List[float], setpoint: List[float], sc_usable: List[float]) -> None:
        """
        모든 제어 시스템을 업데이트합니다.
        
        Args:
            dt (float): 시간 간격 [s]
            weather (List[float]): 기상 데이터 [온도, 습도, 풍속, 일사량 등]
            setpoint (List[float]): 설정값 데이터 [온도, CO2 등]
            sc_usable (List[float]): 보온 스크린 사용 가능 시간 데이터
        """
        # 1. 보온 스크린 제어 업데이트
        self._update_thermal_screen_control(weather, setpoint, sc_usable)
        
        # 2. 환기 제어 업데이트
        self._update_ventilation_control(setpoint)
        
        # 3. 난방 제어 업데이트
        self._update_heating_control(setpoint)
        
        # 4. CO2 제어 업데이트
        self._update_co2_control(setpoint)
        
        # 5. 조명 제어 업데이트
        self._update_illumination_control(weather)
    
    def _update_thermal_screen_control(self, weather: List[float], setpoint: List[float], sc_usable: List[float]) -> None:
        """보온 스크린 제어를 업데이트합니다."""
        # 보온 스크린 제어 입력값 업데이트
        self.SC.T_air_sp = setpoint[1] + 273.15  # 온도 설정값 (K)
        self.SC.T_out = weather[1] + 273.15      # 외부 온도 (K)
        self.SC.RH_air = self.air.RH             # 실내 상대습도
        self.SC.SC_usable = sc_usable[1]         # 스크린 사용 가능 시간
        self.SC.R_Glob_can = self.solar_model.R_t_Glob  # 작물 수준 전천일사량
        
        # 보온 스크린 제어 업데이트
        self.SC.step(dt=self.dt)
        
        # 보온 스크린 상태 업데이트
        self.thScreen.SC = self.SC.SC
    
    def _update_ventilation_control(self, setpoint: List[float]) -> None:
        """환기 제어 시스템 업데이트"""
        # 환기 제어 입력값 업데이트
        self.U_vents.T_air = self.air.T  # 현재 온실 내부 온도
        self.U_vents.T_air_sp = setpoint[1] + 273.15  # 설정 온도 (K)
        self.U_vents.RH_air = self.air.RH  # 현재 상대습도
        self.U_vents.Mdot = self.PID_Mdot.CS  # PID 제어기로부터 계산된 질량 유량
        
        # 환기 제어 계산 및 적용
        self.U_vents.step(dt=self.dt)
        self.Q_ven_AirOut.U_vents = self.U_vents.y  # ven_AirOut을 Q_ven_AirOut으로 수정
        self.Q_ven_TopOut.U_vents = self.U_vents.y  # ven_TopOut을 Q_ven_TopOut으로 수정
    
    def _update_heating_control(self, setpoint: List[float]) -> None:
        """난방 제어를 업데이트합니다."""
        # 난방 PID 제어 입력값 업데이트
        self.PID_Mdot.PV = self.air.T                  # 현재 온도
        self.PID_Mdot.SP = setpoint[1] + 273.15        # 온도 설정값 [K]
        
        # 난방 PID 제어 업데이트
        self.PID_Mdot.step(dt=self.dt)
        
        # 난방수 유량 업데이트
        self.sourceMdot_1ry.Mdot = self.PID_Mdot.CS
    
    def _update_co2_control(self, setpoint: List[float]) -> None:
        """CO2 제어를 업데이트합니다."""
        # CO2 PID 제어 업데이트
        self.PID_CO2.PV = self.CO2_air.CO2  # 현재 CO2 농도 [mg/m³]
        self.PID_CO2.SP = setpoint[2] * 1.94  # CO2 설정값 [mg/m³]
        self.PID_CO2.step(dt=self.dt)
        
        # CO2 주입량 업데이트
        self.MC_AirCan.U_MCext = self.PID_CO2.CS
    
    def _update_illumination_control(self, weather: List[float]) -> None:
        """조명 제어를 업데이트합니다."""
        # 조명 스위치 상태 업데이트 (nan 값 처리)
        ilu_value = weather[9] if len(weather) > 9 else 0.0
        if np.isnan(ilu_value):
            ilu_value = 0.0  # nan인 경우 기본값 0 사용
        self.illu.switch = ilu_value  # 조명 ON/OFF 상태 [0-1]

    def _calculate_energy_flows(self, dt: float) -> None:
        """
        온실의 에너지 흐름을 계산하고 누적합니다.
        
        Args:
            dt (float): 시간 간격 [s]
        """
        # 1. 난방 에너지 계산
        self._calculate_heating_energy(dt)
        
        # 2. 전기 에너지 계산
        self._calculate_electrical_energy(dt)
        
        # 3. 단위 면적당 에너지 계산
        self._calculate_energy_per_area()
    
    def _calculate_heating_energy(self, dt: float) -> None:
        """난방 에너지를 계산하고 누적합니다."""
        # 하부 파이프 열량
        q_low = -self.pipe_low.flow1DimInc.Q_tot / SURFACE_AREA
        
        # 상부 파이프 열량
        q_up = -self.pipe_up.flow1DimInc.Q_tot / SURFACE_AREA
        
        # 총 열량
        q_tot = q_low + q_up
        
        # 양의 열량만 누적 (냉방 에너지는 제외)
        if q_tot > 0:
            # kWh/m²로 변환 (J → kWh)
            self.E_th_tot_kWhm2 += q_tot * dt / (1000 * 3600)
            
            # 총 난방 에너지 계산 (kWh)
            self.E_th_tot = self.E_th_tot_kWhm2 * SURFACE_AREA
    
    def _calculate_electrical_energy(self, dt: float) -> None:
        """전기 에너지를 계산하고 누적합니다."""
        # 조명 전력 (W/m²)
        W_el_illu_instant = self.illu.W_el / SURFACE_AREA
        
        # 전기 에너지 누적 (kWh/m²)
        self.W_el_illu += W_el_illu_instant * dt / (1000 * 3600)
        
        # 총 전기 에너지 계산 (kWh/m², kWh)
        self.E_el_tot_kWhm2 = self.W_el_illu
        self.E_el_tot = self.E_el_tot_kWhm2 * SURFACE_AREA
    
    def _calculate_energy_per_area(self) -> None:
        """단위 면적당 에너지 사용량을 계산합니다."""
        # 난방 에너지 (kWh/m²)
        self.q_low = -self.pipe_low.flow1DimInc.Q_tot / SURFACE_AREA
        self.q_up = -self.pipe_up.flow1DimInc.Q_tot / SURFACE_AREA
        self.q_tot = self.q_low + self.q_up
        
        # 전기 에너지 (kWh/m²)
        self.W_el_illu_instant = self.illu.W_el / SURFACE_AREA

    def _get_state(self) -> Dict[str, Any]:
        """
        온실의 현재 상태를 수집하여 반환합니다.
        
        Returns:
            Dict[str, Any]: 온실의 현재 상태 정보를 담은 딕셔너리
                - temperatures: 온도 관련 상태
                - humidity: 습도 관련 상태
                - energy: 에너지 관련 상태
                - control: 제어 관련 상태
                - crop: 작물 관련 상태
        """
        return {
            'temperatures': self._get_temperature_states(),
            'humidity': self._get_humidity_states(),
            'energy': self._get_energy_states(),
            'control': self._get_control_states(),
            'crop': self._get_crop_states()
        }
    
    def _get_temperature_states(self) -> Dict[str, float]:
        """온도 관련 상태를 수집합니다."""
        return {
            'air': self.air.T - 273.15,           # 실내 공기 온도 [°C]
            'air_top': self.air_Top.T - 273.15,   # 상부 공기 온도 [°C]
            'cover': self.cover.T - 273.15,       # 외피 온도 [°C]
            'canopy': self.canopy.T - 273.15,     # 작물 온도 [°C]
            'floor': self.floor.T - 273.15,       # 바닥 온도 [°C]
            'screen': self.thScreen.T - 273.15,   # 보온 스크린 온도 [°C]
            'pipe_low': self.pipe_low.T - 273.15, # 하부 파이프 온도 [°C]
            'pipe_up': self.pipe_up.T - 273.15,   # 상부 파이프 온도 [°C]
            'soil': self.T_soil7 - 273.15         # 토양 온도 [°C] (외부 입력값 사용)
        }
    
    def _get_humidity_states(self) -> Dict[str, float]:
        """습도 관련 상태를 수집합니다."""
        return {
            'air_rh': self.air.RH,                # 실내 상대습도 [%]
            'air_top_rh': self.air_Top.RH,        # 상부 공기 상대습도 [%]
            'air_vp': self.air.massPort.VP,       # 실내 수증기압 [Pa]
            'air_top_vp': self.air_Top.massPort.VP,  # 상부 공기 수증기압 [Pa]
            'cover_vp': self.cover.massPort.VP,   # 외피 수증기압 [Pa]
            'screen_vp': self.thScreen.massPort.VP,  # 보온 스크린 수증기압 [Pa]
            'canopy_vp': self.canopy.massPort.VP  # 작물 수증기압 [Pa]
        }
    
    def _get_energy_states(self) -> Dict[str, float]:
        """에너지 관련 상태를 수집합니다."""
        return {
            'heating': {
                'q_low': self.q_low,              # 하부 파이프 열량 [W/m²]
                'q_up': self.q_up,                # 상부 파이프 열량 [W/m²]
                'q_tot': self.q_tot,              # 총 열량 [W/m²]
                'E_th_tot_kWhm2': self.E_th_tot_kWhm2,  # 누적 난방 에너지 [kWh/m²]
                'E_th_tot': self.E_th_tot        # 총 누적 난방 에너지 [kWh]
            },
            'electrical': {
                'W_el_illu': self.W_el_illu,      # 누적 조명 에너지 [kWh/m²]
                'W_el_illu_instant': self.W_el_illu_instant,  # 순간 조명 전력 [W/m²]
                'E_el_tot_kWhm2': self.E_el_tot_kWhm2,  # 누적 전기 에너지 [kWh/m²]
                'E_el_tot': self.E_el_tot        # 총 누적 전기 에너지 [kWh]
            }
        }
    
    def _get_control_states(self) -> Dict[str, float]:
        """제어 관련 상태를 수집합니다."""
        return {
            'screen': {
                'SC': self.thScreen.SC,           # 보온 스크린 폐쇄율 [0-1]
                'SC_usable': self.SC.SC_usable    # 스크린 사용 가능 여부 [0-1]
            },
            'ventilation': {
                'U_vents': self.U_vents.U_vents,  # 환기 개도율 [0-1]
                'f_vent': self.Q_ven_AirOut.f_vent_total  # 환기량 [m³/s]
            },
            'heating': {
                'Mdot': self.PID_Mdot.CS,         # 난방수 유량 [kg/s]
                'T_supply': self.sourceMdot_1ry.T_0 - 273.15  # 공급수 온도 [°C]
            },
            'co2': {
                'CO2_air': self.CO2_air.CO2,      # 실내 CO2 농도 [mg/m³]
                'CO2_injection': self.MC_AirCan.U_MCext  # CO2 주입량 [mg/s]
            },
            'illumination': {
                'switch': self.illu.switch,       # 조명 ON/OFF 상태 [0-1]
                'P_el': self.illu.P_el            # 조명 전력 [W]
            }
        }
    
    def _get_crop_states(self) -> Dict[str, float]:
        """작물 관련 상태를 수집합니다."""
        return {
            'LAI': self.TYM.LAI,                  # 엽면적지수 [m²/m²]
            'DM_Har': self.TYM.DM_Har,            # 수확 건물중 [mg/m²]
            'C_Leaf': self.TYM.C_Leaf,            # 잎 건물중 [mg/m²]
            'C_Stem': self.TYM.C_Stem,            # 줄기 건물중 [mg/m²]
            'R_PAR_can': self.TYM.R_PAR_can,      # 작물 수준 광합성 유효 복사 [μmol/m²/s]
            'MC_AirCan': self.TYM.MC_AirCan_mgCO2m2s  # 작물 CO2 흡수량 [mg/m²/s]
        }

    def _verify_state(self) -> None:
        """
        온실의 현재 상태가 유효한지 검증합니다.
        
        검증 항목:
        1. 온도 범위 검증
        2. 습도 범위 검증
        3. 에너지 균형 검증
        4. 수증기 균형 검증
        5. CO2 농도 검증
        6. 제어 시스템 상태 검증
        
        Raises:
            ValueError: 상태 검증에 실패한 경우
        """
        try:
            print("온도 범위 검증 중...")
            self._verify_temperature_ranges()
            print("습도 범위 검증 중...")
            self._verify_humidity_ranges()
            print("에너지 균형 검증 중...")
            self._verify_energy_balance()
            print("수증기 균형 검증 중...")
            self._verify_vapor_balance()
            print("CO2 농도 검증 중...")
            self._verify_co2_concentration()
            print("제어 시스템 상태 검증 중...")
            self._verify_control_systems()
            print("모든 검증 통과!")
        except ValueError as e:
            print(f"검증 실패: {str(e)}")
            raise ValueError(f"상태 검증 실패: {str(e)}")
    
    def _verify_temperature_ranges(self) -> None:
        """온도 범위가 유효한지 검증합니다."""
        state = self._get_state()
        temps = state['temperatures']
        
        # 일반 온도 범위 검증 (난방 파이프 제외)
        for name, temp in temps.items():
            if name in ['pipe_low', 'pipe_up']:
                # 난방 파이프는 더 높은 온도 허용 (0°C ~ 100°C)
                if not (0 <= temp <= 100):
                    raise ValueError(f"{name} 온도({temp:.1f}°C)가 허용 범위를 벗어났습니다")
            else:
                # 일반 구성 요소는 기본 온도 범위 (0°C ~ 50°C)
                if not (0 <= temp <= 50):
                    raise ValueError(f"{name} 온도({temp:.1f}°C)가 허용 범위를 벗어났습니다")
        
        # 온도 차이 검증
        if abs(temps['air'] - temps['air_top']) > 10.0:  # 상하부 공기 온도차
            raise ValueError(f"상하부 공기 온도차({abs(temps['air'] - temps['air_top']):.1f}°C)가 너무 큽니다")
    
    def _verify_humidity_ranges(self) -> None:
        """습도 범위가 유효한지 검증합니다."""
        state = self._get_state()
        humidity = state['humidity']
        
        # 상대습도 범위 검증
        if not (0.0 <= humidity['air_rh'] <= 100.0):
            raise ValueError(f"실내 상대습도({humidity['air_rh']:.1f}%)가 허용 범위를 벗어났습니다")
        if not (0.0 <= humidity['air_top_rh'] <= 100.0):
            raise ValueError(f"상부 공기 상대습도({humidity['air_top_rh']:.1f}%)가 허용 범위를 벗어났습니다")
        
        # 수증기압 검증
        for name, vp in humidity.items():
            if 'vp' in name and vp < 0:
                raise ValueError(f"{name} 수증기압({vp:.1f} Pa)이 음수입니다")
    
    def _verify_energy_balance(self) -> None:
        """에너지 균형이 유효한지 검증합니다."""
        state = self._get_state()
        energy = state['energy']
        
        # 열량 검증
        if energy['heating']['q_tot'] < -1000:  # 최대 냉각량
            raise ValueError(f"총 열량({energy['heating']['q_tot']:.1f} W/m²)이 너무 낮습니다")
        if energy['heating']['q_tot'] > 1000:   # 최대 가열량
            raise ValueError(f"총 열량({energy['heating']['q_tot']:.1f} W/m²)이 너무 높습니다")
        
        # 누적 에너지 검증
        if energy['heating']['E_th_tot_kWhm2'] < 0:
            raise ValueError(f"누적 난방 에너지({energy['heating']['E_th_tot_kWhm2']:.1f} kWh/m²)가 음수입니다")
        if energy['electrical']['E_el_tot_kWhm2'] < 0:
            raise ValueError(f"누적 전기 에너지({energy['electrical']['E_el_tot_kWhm2']:.1f} kWh/m²)가 음수입니다")
    
    def _verify_vapor_balance(self) -> None:
        """수증기 균형이 유효한지 검증합니다."""
        state = self._get_state()
        control = state['control']
        
        # 환기량과 수증기압 관계 검증
        if control['ventilation']['f_vent'] > 0:
            air_vp = state['humidity']['air_vp']
            air_top_vp = state['humidity']['air_top_vp']
            if air_vp < air_top_vp:
                raise ValueError("환기 시 실내 수증기압이 상부 공기 수증기압보다 낮습니다")
    
    def _verify_co2_concentration(self) -> None:
        """CO2 농도가 유효한지 검증합니다."""
        state = self._get_state()
        control = state['control']
        
        # CO2 농도 범위 검증
        co2_air = control['co2']['CO2_air']
        if not (300 <= co2_air <= 2000):  # 일반적인 CO2 농도 범위 [mg/m³]
            raise ValueError(f"실내 CO2 농도({co2_air:.1f} mg/m³)가 허용 범위를 벗어났습니다")
        
        # CO2 주입량 검증
        if control['co2']['CO2_injection'] < 0:
            raise ValueError(f"CO2 주입량({control['co2']['CO2_injection']:.1f} mg/s)이 음수입니다")
    
    def _verify_control_systems(self) -> None:
        """제어 시스템 상태가 유효한지 검증합니다."""
        state = self._get_state()
        control = state['control']
        
        # 보온 스크린 상태 검증
        if not (0.0 <= control['screen']['SC'] <= 1.0):
            raise ValueError(f"보온 스크린 폐쇄율({control['screen']['SC']:.2f})이 허용 범위를 벗어났습니다")
        
        # 환기 개도율 검증
        if not (0.0 <= control['ventilation']['U_vents'] <= 1.0):
            raise ValueError(f"환기 개도율({control['ventilation']['U_vents']:.2f})이 허용 범위를 벗어났습니다")
        
        # 난방수 유량 검증
        if control['heating']['Mdot'] < 0:
            raise ValueError(f"난방수 유량({control['heating']['Mdot']:.2f} kg/s)이 음수입니다")
        
        # 조명 상태 검증
        if not (0.0 <= control['illumination']['switch'] <= 1.0):
            raise ValueError(f"조명 상태({control['illumination']['switch']:.2f})가 허용 범위를 벗어났습니다")

    def _update_radiation_coefficients(self) -> None:
        """View Factor 기반 복사 열전달 계수를 업데이트합니다."""
        # 하부 파이프 복사 열전달 계수 업데이트
        self.Q_rad_LowFlr.FFa = self.pipe_low.FF
        self.Q_rad_LowFlr._update_REC_ab()
        
        self.Q_rad_LowCan.FFa = self.pipe_low.FF
        self.Q_rad_LowCan.FFb = self.canopy.FF
        self.Q_rad_LowCan._update_REC_ab()
        
        self.Q_rad_LowCov.FFa = self.pipe_low.FF
        self.Q_rad_LowCov._update_REC_ab()
        
        self.Q_rad_LowScr.FFa = self.pipe_low.FF
        self.Q_rad_LowScr.FFb = self.thScreen.FF_i
        self.Q_rad_LowScr._update_REC_ab()
        
        # 상부 파이프 복사 열전달 계수 업데이트
        self.Q_rad_UpFlr.FFa = self.pipe_up.FF
        self.Q_rad_UpFlr._update_REC_ab()
        
        self.Q_rad_UpCan.FFa = self.pipe_up.FF
        self.Q_rad_UpCan.FFb = self.canopy.FF
        self.Q_rad_UpCan._update_REC_ab()
        
        self.Q_rad_UpCov.FFa = self.pipe_up.FF
        self.Q_rad_UpCov._update_REC_ab()
        
        self.Q_rad_UpScr.FFa = self.pipe_up.FF
        self.Q_rad_UpScr.FFb = self.thScreen.FF_i
        self.Q_rad_UpScr._update_REC_ab()
