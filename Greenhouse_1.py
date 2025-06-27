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
from Modelica.Thermal.HeatTransfer.Sensors.TemperatureSensor import TemperatureSensor
from Flows.FluidFlow.Reservoirs.SinkP import SinkP
from Flows.Sensors.RHSensor import RHSensor
from Flows.Sources.CO2.PrescribedCO2Flow import PrescribedCO2Flow
from Flows.Sources.CO2.PrescribedConcentration import PrescribedConcentration
from Functions.WaterVapourPressure import WaterVapourPressure

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
surface = 1.4e4  # Greenhouse floor area [m²]

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

class Greenhouse_1:

    def __init__(self, time_unit_scaling: float = 1.0):
        """온실 시뮬레이션 모델 초기화"""
        self.time_unit_scaling = time_unit_scaling
        self.dt = 0.0  # 시간 간격 초기화
        
        # 통합 입력 데이터프레임 생성
        self.input_df = self._load_and_merge_inputs()
        
        # 날씨 데이터 및 설정값 초기화 (Modelica 원본과 일치)
        self.Tout = 293.15      # 외부 온도 [K] (Modelica: Tout)
        self.Tsky = 293.15      # 하늘 온도 [K] (Modelica: Tsky)
        self.u_wind = 0.0       # 풍속 [m/s] (Modelica: u_wind)
        self.I_glob = 0.0       # 일사량 [W/m²] (Modelica: I_glob)
        self.VPout = 0.0        # 외부 수증기압 [Pa] (Modelica: VPout)
        self.Tair_setpoint = 293.15   # 공기 온도 설정값 [K] (Modelica: Tair_setpoint)
        self.T_soil7 = 276.15   # 토양 온도 [K] (Modelica: Tsoil7)
        self.OnOff = 0.0        # 조명 ON/OFF 신호 (Modelica: OnOff)
        
        # CO2 관련 변수 (Modelica 원본과 일치)
        self.CO2out_ppm_to_mgm3 = 340 * 1.94  # 외부 CO2 농도 [mg/m³] (Modelica: 340 ppm)
        self.CO2_SP_var = 0.0   # CO2 설정값 [mg/m³] (Modelica: CO2_SP_var)
        
        # 컴포넌트 초기화
        self._init_components()
        self._init_state_variables()
        
        # 초기 스크린 상태 동기화 (모든 관련 컴포넌트에 SC=0.0 적용)
        self._synchronize_screen_components()
        
        # 초기 데이터 로드 (첫 번째 스텝의 데이터로 초기화)
        self._load_initial_data()
        
        print("Greenhouse_1 초기화 완료")
    
    def _load_and_merge_inputs(self):
        # 파일 읽기 (헤더 포함, skiprows 없이)
        weather = pd.read_csv(WEATHER_DATA_PATH, sep='\t')
        setpoint = pd.read_csv(SETPOINT_DATA_PATH, sep='\t')
        sc_usable = pd.read_csv(SCREEN_USABLE_PATH, sep='\t')
        # 컬럼명 통일 (필요시)
        weather = weather.rename(columns={weather.columns[0]: 'time'})
        setpoint = setpoint.rename(columns={setpoint.columns[0]: 'time'})
        sc_usable = sc_usable.rename(columns={sc_usable.columns[0]: 'time'})
        # time 기준 merge (outer join)
        df = pd.merge(weather, setpoint, on='time', how='outer')
        df = pd.merge(df, sc_usable, on='time', how='outer')
        # 시간순 정렬
        df = df.sort_values('time').reset_index(drop=True)
        # 결측치 선형 보간
        df = df.interpolate(method='linear', limit_direction='both')
        return df

    def _get_input_row(self, current_time):
        # current_time: 초 단위
        # 가장 가까운 time 행을 반환
        idx = (self.input_df['time'] - current_time).abs().idxmin()
        return self.input_df.iloc[idx]

    def _load_initial_data(self) -> None:
        """초기 데이터를 로드하여 환경 조건을 설정합니다."""
        try:
            # 시간 0초의 입력값으로 초기화
            row = self._get_input_row(0)
            self._set_environmental_conditions(row)
            self._update_setpoints(row)
            
            # 외부 환경 조건 기반으로 현실적인 초기 온도 설정
            external_temp = self.Tout  # 외부 온도 [K]
            
            # 1. 공기 온도: 외부 온도보다 약간 높게 (난방 효과)
            self.air.T = external_temp + 5.0  # 외부 + 5°C
            self.air_Top.T = external_temp + 4.5  # 상부공기는 하부공기보다 약간 낮게 (0.5°C 차이)
            
            # 2. 작물 온도: 공기 온도와 비슷하지만 약간 낮게 (증산 냉각 효과)
            self.canopy.T = self.air.T - 1.0  # 공기보다 1°C 낮게
            
            # 3. 외피 온도: 외부 온도와 비슷하지만 약간 높게 (태양복사 흡수)
            self.cover.T = external_temp + 2.0  # 외부 + 2°C
            
            # 4. 바닥 온도: 공기 온도보다 약간 낮게 (지하 열전달)
            self.floor.T = self.air.T - 2.0  # 공기보다 2°C 낮게
            
            # 5. 보온 스크린 온도: 공기와 외피 사이의 중간값
            self.thScreen.T = (self.air.T + self.cover.T) / 2
            
            # 6. 난방 파이프 온도 설정 (Modelica 원본과 일치)
            # Modelica: Tstart_inlet=353.15 (80°C), Tstart_outlet=323.15 (50°C)
            self.pipe_low.flow1DimInc.Tstart_inlet = 353.15  # 80°C
            self.pipe_low.flow1DimInc.Tstart_outlet = 323.15  # 50°C
            self.pipe_up.flow1DimInc.Tstart_inlet = 353.15   # 80°C
            self.pipe_up.flow1DimInc.Tstart_outlet = 323.15  # 50°C
            
            # 모든 컴포넌트의 초기 수증기압을 외부 수증기압과 동일하게 설정
            initial_vp = self.VPout  # 외부 수증기압 [Pa]
            
            # 공기 수증기압 설정
            self.air.massPort.VP = initial_vp
            self.air_Top.massPort.VP = initial_vp
            
            # 작물 수증기압 설정
            self.canopy.massPort.VP = initial_vp
            
            # 외피 수증기압 설정
            self.cover.massPort.VP = initial_vp
            
            # 보온 스크린 수증기압 설정
            self.thScreen.massPort.VP = initial_vp
            
            # **중요**: 공기 RH를 외부 RH와 동일하게 설정 (100% 고정 방지)
            # 외부 RH 계산 (txt 파일의 2번째 열)
            external_rh = row['RH_out'] / 100.0  # 95% → 0.95
            self.air.RH = external_rh
            self.air_Top.RH = external_rh
            
            # **중요**: CO₂ 농도 초기화 (Modelica 원본과 정확히 일치)
            # Modelica: CO2_start=1940 mg/m³ (약 1000 ppm)
            self.CO2_air.CO2 = 1940.0  # 하부공기
            self.CO2_top.CO2 = 1940.0  # 상부공기도 동일하게 초기화 (Modelica 원본과 일치)
            
        except Exception as e:
            print(f"초기 데이터 로드 실패: {e}")
            # 기본값 유지
    
    def _init_components(self) -> None:
        # 1. cover 
        self.cover = Cover(
            rho=2600,  # 밀도 [kg/m³]
            c_p=840,   # 비열 [J/(kg·K)]
            A=surface,
            steadystate=False,
            h_cov=1e-3,  # 두께 [m]
            phi=0.43633231299858  # 경사각 [rad]
        )
        
        # 2. air
        self.air = Air(
            A=surface,
            steadystate=False,
            steadystateVP=False,
            h_Air=INITIAL_CONDITIONS['air']['h_Air']
        )

        # 3. canopy (Modelica 원본 순서) - 기본 LAI로 초기화, 나중에 TYM.LAI로 업데이트
        self.canopy = Canopy(
            A=surface,
            steadystate=False,
            LAI=1.06  # 기본값, 나중에 TYM.LAI로 업데이트
        ) 

        # 4. Q_rad_CanCov (Modelica 원본 순서)
        self.Q_rad_CanCov = Radiation_T4(
            A=surface,
            epsilon_a=1.0,
            epsilon_b=0.84,
            FFa=self.canopy.FF,    # 작물 View Factor
            FFb=1.0,     # 외피 View Factor
            FFab1=0.0,   # 임시값, 나중에 pipe_up.FF로 업데이트
            FFab2=0.0,   # 임시값, 나중에 thScreen.FF_ij로 업데이트
        )

        # 5. floor (Modelica 원본 순서)
        self.floor = Floor(
            rho=1,     # 밀도 [kg/m³]
            c_p=2e6,   # 비열 [J/(kg·K)]
            A=surface,
            V=0.01 * surface,  # 부피 [m³]
            steadystate=False
        )

        # 6. Q_rad_FlrCan (Modelica 원본 순서)
        self.Q_rad_FlrCan = Radiation_T4(
            A=surface,
            epsilon_a=0.89,  # 바닥 방사율
            epsilon_b=1.0,   # 작물 방사율
            FFa=1.0,         # 바닥 View Factor
            FFb=self.canopy.FF,  # 작물 View Factor
            FFab1=0.0  # 임시값, 나중에 pipe_low.FF로 업데이트
        )

        # 7. Q_cnv_CanAir (Modelica 원본 순서)
        self.Q_cnv_CanAir = CanopyFreeConvection(
            A=surface,
            LAI=self.canopy.LAI
        )

        # 8. Q_cnv_FlrAir (Modelica 원본 순서)
        self.Q_cnv_FlrAir = FreeConvection(
            phi=0,  # 바닥은 수평
            A=surface,
            floor=True
        )

        # 9. Q_rad_CovSky (Modelica 원본 순서)
        self.Q_rad_CovSky = Radiation_T4(
            A=surface,
            epsilon_a=0.84,
            epsilon_b=1.0            
        )

        # 10. Q_cnv_CovOut (Modelica 원본 순서)
        self.Q_cnv_CovOut = OutsideAirConvection(
            A=surface,
            u=self.u_wind,
            phi=0.43633231299858
        )

        # 11. illu (Modelica 원본 순서) - 기본 LAI로 초기화, 나중에 TYM.LAI로 업데이트
        self.illu = Illumination(
            A=surface,
            power_input=True,
            LAI=1.06,  # 기본값, 나중에 TYM.LAI로 업데이트
            P_el=500,  # 전기 소비량 [W]
            p_el=100   # 조명 밀도 [W/m²]
        )

        # 12. Q_rad_FlrCov (Modelica 원본 순서)
        self.Q_rad_FlrCov = Radiation_T4(
            A=surface,
            epsilon_a=0.89,  # 바닥 방사율
            epsilon_b=0.84,  # 외피 방사율
            FFa=1.0,         # 바닥 View Factor
            FFb=1.0,         # 외피 View Factor
            FFab1=0.0,       # 임시값, 나중에 pipe_low.FF로 업데이트
            FFab2=self.canopy.FF,    # 작물 방해
            FFab3=0.0,       # 임시값, 나중에 pipe_up.FF로 업데이트
            FFab4=0.0        # 임시값, 나중에 thScreen.FF_ij로 업데이트
        )

        # 13. MV_CanAir (Modelica 원본 순서) - 기본값으로 초기화, 나중에 업데이트
        self.MV_CanAir = MV_CanopyTranspiration(
            A=surface,
            LAI=self.canopy.LAI,
            CO2_ppm=1000,  # 기본값, 나중에 CO2_air.CO2_ppm으로 업데이트 (Modelica: CO2_air.CO2_ppm)
            R_can=0.0,    # 기본값, 나중에 solar_model.R_t_Glob + illu.R_PAR + illu.R_NIR로 업데이트
            T_can=self.canopy.T
        )

        # 14. Q_cd_Soil (Modelica 원본 순서)
        self.Q_cd_Soil = SoilConduction(
            A=surface,
            N_c=2,  # 토양 층 수
            N_s=5,  # 토양 층 수
            lambda_c=1.7,  # 토양 전도도 [W/(m·K)]
            lambda_s=0.85,  # 토양 전도도 [W/(m·K)]
            steadystate=False
        )

        # 15. Q_rad_CanScr (Modelica 원본 순서)
        self.Q_rad_CanScr = Radiation_T4(
            A=surface,
            epsilon_a=1.0,
            epsilon_b=1.0,
            FFa=self.canopy.FF,
            FFab1=0.0,  # 임시값, 나중에 pipe_up.FF로 업데이트
            FFb=0.0     # 임시값, 나중에 thScreen.FF_i로 업데이트
        )

        # 16. Q_rad_FlrScr (Modelica 원본 순서)
        self.Q_rad_FlrScr = Radiation_T4(
            A=surface,
            epsilon_a=0.89,  # 바닥 방사율
            epsilon_b=1.0,   # 스크린 방사율
            FFa=1.0,         # 바닥 View Factor
            FFb=0.0,         # 임시값, 나중에 thScreen.FF_i로 업데이트
            FFab1=self.canopy.FF,    # 작물 방해
            FFab2=0.0,       # 임시값, 나중에 pipe_up.FF로 업데이트
            FFab3=0.0        # 임시값, 나중에 pipe_low.FF로 업데이트
        )

        # 17. thScreen (Modelica 원본 순서) - 기본값으로 초기화, 나중에 SC.y로 업데이트
        self.thScreen = ThermalScreen(
            A=surface,
            SC=0.0,  # 스크린을 완전히 열어서 하부공기 환기 허용
            steadystate=False
        )

        # 18. Q_rad_ScrCov (Modelica 원본 순서)
        self.Q_rad_ScrCov = Radiation_T4(
            A=surface,
            epsilon_a=1.0,   # 스크린 방사율
            epsilon_b=0.84,  # 외피 방사율
            FFa=0.0,         # 임시값, 나중에 thScreen.FF_i로 업데이트
            FFb=1.0
        )

        # 19. air_Top (Modelica 원본 순서)
        self.air_Top = Air_Top(
            steadystate=False,
            steadystateVP=True,
            h_Top=0.4,  # 높이 [m]
            A=surface
        )

        # 20. solar_model (Modelica 원본 순서) - 기본값으로 초기화, 나중에 업데이트
        self.solar_model = Solar_model(
            A=surface,
            LAI=1.06,  # 기본값, 나중에 TYM.LAI로 업데이트
            SC=0.0,    # 스크린을 열어서 환기 허용
            I_glob=0.0,  # 초기 일사량
        )

        # 21. pipe_low (Modelica 원본 순서)
        self.pipe_low = HeatingPipe(
            d=0.051,  # 직경 [m]
            freePipe=False,
            A=surface,
            N=5,      # 파이프 수
            N_p=625,  # 파이프 길이당 단위 수
            l=50      # 길이 [m]
        )

        # 22. Q_rad_LowFlr (Modelica 원본 순서)
        self.Q_rad_LowFlr = Radiation_N(
            A=surface,
            epsilon_a=0.88,
            epsilon_b=0.89,
            FFa=0.0,  # 임시값, 나중에 pipe_low.FF로 업데이트
            FFb=1.0,
            N=self.pipe_low.N
        )
        
        # 23. Q_rad_LowCan (Modelica 원본 순서)
        self.Q_rad_LowCan = Radiation_N(
            A=surface,
            epsilon_a=0.88,
            epsilon_b=1.0,
            FFa=0.0,  # 임시값, 나중에 pipe_low.FF로 업데이트
            FFb=0.0,  # 임시값, 나중에 canopy.FF로 업데이트
            N=self.pipe_low.N
        )

        # 24. Q_rad_LowCov (Modelica 원본 순서)
        self.Q_rad_LowCov = Radiation_N(
            A=surface,
            epsilon_a=0.88,
            epsilon_b=0.84,
            FFa=0.0,  # 임시값, 나중에 pipe_low.FF로 업데이트
            FFb=1.0,
            FFab1=0.0,  # 임시값, 나중에 canopy.FF로 업데이트
            FFab2=0.0,  # 임시값, 나중에 pipe_up.FF로 업데이트
            FFab3=0.0,  # 임시값, 나중에 thScreen.FF_ij로 업데이트
            N=self.pipe_low.N
        )

        # 25. Q_cnv_LowAir (Modelica 원본 순서)
        self.Q_cnv_LowAir = PipeFreeConvection_N(
            N=self.pipe_low.N,
            A=surface,
            d=self.pipe_low.d,
            l=self.pipe_low.l,
            N_p=self.pipe_low.N_p,
            freePipe=False
        )

        # 26. Q_rad_LowScr (Modelica 원본 순서)
        self.Q_rad_LowScr = Radiation_N(
            A=surface,
            epsilon_a=0.88,
            epsilon_b=1.0,
            FFa=0.0,  # 임시값, 나중에 pipe_low.FF로 업데이트
            FFb=0.0,  # 임시값, 나중에 thScreen.FF_i로 업데이트
            FFab1=0.0,  # 임시값, 나중에 canopy.FF로 업데이트
            FFab2=0.0,  # 임시값, 나중에 pipe_up.FF로 업데이트
            N=self.pipe_low.N
        )

        # 27. pipe_up (Modelica 원본 순서)
        self.pipe_up = HeatingPipe(
            d=0.025,  # 직경 [m]
            freePipe=True,
            A=surface,
            N=5,      # 파이프 수
            N_p=292,  # 파이프 길이당 단위 수
            l=44      # 길이 [m]
        )

        # 28. Q_rad_UpFlr (Modelica 원본 순서)
        self.Q_rad_UpFlr = Radiation_N(
            A=surface,
            epsilon_a=0.88,
            epsilon_b=0.89,
            FFb=1.0,
            FFa=0.0,  # 임시값, 나중에 pipe_up.FF로 업데이트
            FFab1=0.0,  # 임시값, 나중에 canopy.FF로 업데이트
            FFab2=0.0,  # 임시값, 나중에 pipe_low.FF로 업데이트
            N=self.pipe_up.N
        )

        # 29. Q_rad_UpCan (Modelica 원본 순서)
        self.Q_rad_UpCan = Radiation_N(
            A=surface,
            epsilon_a=0.88,
            epsilon_b=1.0,
            FFa=0.0,  # 임시값, 나중에 pipe_up.FF로 업데이트
            FFb=0.0,  # 임시값, 나중에 canopy.FF로 업데이트
            N=self.pipe_up.N
        )
        
        # 30. Q_rad_UpCov (Modelica 원본 순서)
        self.Q_rad_UpCov = Radiation_N(
            A=surface,
            epsilon_a=0.88,
            epsilon_b=0.84,
            FFb=1.0,
            FFa=0.0,  # 임시값, 나중에 pipe_up.FF로 업데이트
            FFab1=0.0,  # 임시값, 나중에 thScreen.FF_ij로 업데이트
            N=self.pipe_up.N
        )

        # 31. Q_cnv_UpAir (Modelica 원본 순서)
        self.Q_cnv_UpAir = PipeFreeConvection_N(
            N=self.pipe_up.N,
            A=surface,
            d=self.pipe_up.d,
            l=self.pipe_up.l,  # 파이프 길이 추가
            N_p=self.pipe_up.N_p,  # 병렬 파이프 수 추가
            freePipe=self.pipe_up.freePipe  # 파이프 상태 추가
        )

        # 32. Q_rad_UpScr (Modelica 원본 순서)
        self.Q_rad_UpScr = Radiation_N(
            A=surface,
            epsilon_a=0.88,
            FFa=0.0,  # 임시값, 나중에 pipe_up.FF로 업데이트
            epsilon_b=1.0,
            FFb=0.0  # 임시값, 나중에 thScreen.FF_i로 업데이트
        )

        # 33. Q_cnv_AirScr (Modelica 원본 순서)
        self.Q_cnv_AirScr = Convection_Condensation(
            phi=0,
            A=surface,
            floor=False,
            thermalScreen=True,
            Air_Cov=False,
            SC=0.0  # 스크린을 열어서 환기 허용
        )

        # 34. Q_cnv_AirCov (Modelica 원본 순서)
        self.Q_cnv_AirCov = Convection_Condensation(
            phi=0.43633231299858,
            A=surface,
            floor=False,
            thermalScreen=True,
            Air_Cov=True,
            topAir=False,
            SC=0.0  # 스크린을 열어서 환기 허용
        )

        # 35. Q_cnv_TopCov (Modelica 원본 순서)
        self.Q_cnv_TopCov = Convection_Condensation(
            phi=0.43633231299858,
            A=surface,
            floor=False,
            thermalScreen=True,
            Air_Cov=True,
            topAir=True,
            SC=0.0  # 스크린을 열어서 환기 허용
        )

        # 36. Q_ven_AirOut (Modelica 원본 순서)
        self.Q_ven_AirOut = Ventilation(
            A=surface,
            thermalScreen=True,
            topAir=False,
            u=self.u_wind,  # Modelica: u_wind.y
            U_vents=0.0,    # 기본값, 나중에 U_vents.y로 업데이트
            SC=0.0          # 기본값, 나중에 SC.y로 업데이트
        )
        
        # 37. Q_ven_TopOut (Modelica 원본 순서)
        self.Q_ven_TopOut = Ventilation(
            A=surface,
            thermalScreen=True,
            topAir=True,
            forcedVentilation=False,
            u=self.u_wind,  # Modelica: u_wind.y
            U_vents=0.0,    # 기본값, 나중에 U_vents.y로 업데이트
            SC=0.0          # 기본값, 나중에 SC.y로 업데이트
        )

        # 38. Q_ven_AirTop (Modelica 원본 순서)
        self.Q_ven_AirTop = AirThroughScreen(
            A=surface,
            W=9.6,  # 스크린 너비 [m]
            K=0.2e-3,  # 스크린 투과도
            SC=0.0  # 기본값, 나중에 SC.y로 업데이트
        )

        # 39. Q_cnv_ScrTop (Modelica 원본 순서)
        self.Q_cnv_ScrTop = Convection_Evaporation(
            A=surface,
            SC=0.0,  # 기본값, 나중에 SC.y로 업데이트
            MV_AirScr=0.0  # 기본값, 나중에 Q_cnv_AirScr.MV_flow로 업데이트
        )

        # 40. PID_Mdot (Modelica 원본 순서)
        self.PID_Mdot = PID(
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

        # 41. TYM (Modelica 원본 순서) - 기본값으로 초기화, 나중에 업데이트
        self.TYM = TomatoYieldModel(
            T_canK=self.canopy.T,
            LAI_0=1.06,  
            C_Leaf_0=40e3,  # 초기 잎 질량 [mg/m²]
            C_Stem_0=30e3,  # 초기 줄기 질량 [mg/m²]
            CO2_air=1000,  # 기본값, 나중에 CO2_air.CO2_ppm으로 업데이트 (Modelica: CO2_air.CO2_ppm)
            R_PAR_can=0,  # 기본값, 나중에 solar_model.R_PAR_Can_umol + illu.R_PAR_Can_umol로 업데이트
            LAI_MAX=3.5   # 최대 LAI
        )

        # 42. CO2_air (Modelica 원본 순서)
        self.CO2_air = CO2_Air(
            cap_CO2=self.air.h_Air,  # 공기 구역 높이를 CO2 저장 용량으로 사용
            steadystate=True
        )

        # 43. CO2_top (Modelica 원본 순서)
        self.CO2_top = CO2_Air(
            cap_CO2=0.4,  # Modelica 원본과 정확히 일치
            steadystate=True
        )

        # 44. MC_AirTop (Modelica 원본 순서)
        self.MC_AirTop = MC_ventilation2(
            f_vent=0.0  # 기본값, 나중에 Q_ven_AirTop.f_AirTop로 업데이트
        )
        
        # 45. MC_AirOut (Modelica 원본 순서)
        self.MC_AirOut = MC_ventilation2(
            f_vent=0.0  # 기본값, 나중에 Q_ven_AirOut.f_vent_total로 업데이트
        )

        # 46. MC_TopOut (Modelica 원본 순서)
        self.MC_TopOut = MC_ventilation2(
            f_vent=0.0  # 기본값, 나중에 Q_ven_TopOut.f_vent_total로 업데이트
        )

        # 47. MC_AirCan (Modelica 원본 순서)
        self.MC_AirCan = MC_AirCan(
            MC_AirCan=0.0  # 기본값, 나중에 TYM.MC_AirCan_mgCO2m2s로 업데이트
        )

        # 48. MC_ExtAir (Modelica 원본 순서)
        self.MC_ExtAir = PrescribedCO2Flow(
            phi_ExtCO2=27
        )

        # 49. CO2out (Modelica 원본 순서) - 외부 CO2 농도 설정
        self.CO2out = PrescribedConcentration()

        # 50. PID_CO2 (Modelica 원본 순서)
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

        # 51. sourceMdot_1ry (Modelica 원본 순서)
        self.sourceMdot_1ry = SourceMdot(
            T_0=363.15,  # 공급수 온도 [K]
            Mdot_0=0.528   # 초기 유량 [kg/s]
        )
        
        # 52. sinkP_2ry (Modelica 원본 순서)
        self.sinkP_2ry = SinkP(
            p0=1000000  # 압력 [Pa]
        )

        # 53. SC (Modelica 원본 순서)
        self.SC = Control_ThScreen(
            R_Glob_can=0, 
            R_Glob_can_min=35
        )

        # 54. U_vents (Modelica 원본 순서)
        self.U_vents = Uvents_RH_T_Mdot(
            T_air=self.air.T,
            T_air_sp=self.Tair_setpoint,
            Mdot=self.PID_Mdot.CS,
            RH_air_input=self.air.RH
        )

        # 55. 센서들 (Modelica 원본 순서)
        self.Tair_sensor = TemperatureSensor()
        self.Tair_sensor.port.T = self.air.T  # 시뮬레이션 루프에서 동기화 필요
        self.RH_air_sensor = RHSensor()
        self.RH_out_sensor = RHSensor()

        # 56. 컴포넌트 간 연결 업데이트 (순환 참조 해결)
        self._update_component_connections()
    
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
    
    def _set_environmental_conditions(self, row) -> None:
        """
        외부 환경 조건을 설정합니다.
        
        Args:
            row: 입력 데이터프레임의 한 행(Series)
        """
        
        # 외부 온도 (Modelica: TMY_and_control.y[1]) - 섭씨를 켈빈으로 변환
        self.Tout = row['T_out'] + 273.15 
             
        # 하늘 온도 (Modelica: TMY_and_control.y[6]) - 섭씨를 켈빈으로 변환
        self.Tsky = row['T_sky'] + 273.15  
        
        # 풍속 [m/s]
        self.u_wind = row['u_wind']  # col_5가 풍속
        
        # 일사량 [W/m²]
        self.I_glob = row['I_glob']  # col_4가 일사량
        
        # 외부 수증기압 [Pa]
        # 섭씨 온도와 습도를 사용하여 수증기압 계산
        self.VPout = WaterVapourPressure().calculate(row['T_out'], row['RH_out'])  # 섭씨 온도, 습도
        
        # 조명 ON/OFF 신호 (Modelica: TMY_and_control.y[9])
        self.OnOff = row['ilu_sp'] if 'ilu_sp' in row else 0  # col_9가 조명
        
        # 태양광 모델 업데이트
        self.solar_model.I_glob = self.I_glob
        
        # 외부 CO2 농도 [mg/m³]
        # self.CO2out_ppm_to_mgm3 = 430 * 1.94  # 외부 CO2 농도 [mg/m³] 
        # self.CO2_SP_var = 0.0   # CO2 설정값 [mg/m³] (Modelica: CO2_SP_var)
        
    def _update_setpoints(self, row) -> None:
        """
        설정값을 업데이트합니다.
        
        Args:
            row: 입력 데이터프레임의 한 행(Series)
        """
        # 공기 온도 설정값 [K]
        self.Tair_setpoint = row['T_sp'] + 273.15 if 'T_sp' in row else 293.15
        
        # CO2 설정값 [mg/m³] (Modelica: CO2_SP_var = SP_new.y[3]*1.94)
        self.CO2_SP_var = row['CO2_sp'] * 1.94 if 'CO2_sp' in row else 1000 * 1.94  # ppm을 mg/m³로 변환

    def step(self, dt: float, time_idx: int) -> None:
        """시뮬레이션 스텝 실행"""
        self.dt = dt  # 시간 간격 업데이트
        
        # 실제 시간 계산 (초 단위)
        current_time = time_idx * dt  # [초]
        self._current_time = current_time  # 디버깅 출력에서 사용
        
        # 현재 시간의 기상 데이터와 설정값 가져오기 (선형 보간 사용)
        row = self._get_input_row(current_time)
        
        # 1. 외부 환경 조건 및 설정값 업데이트
        self._set_environmental_conditions(row)
        self._update_setpoints(row)
        
        # 2. 제어 시스템 업데이트 (스크린 동기화 포함)
        self._update_control_systems(dt, row)
        
        # 3. 난방 시스템 업데이트 (소스/싱크)
        self._update_heating_system(dt)
        
        # 4. 컴포넌트 간 연결 업데이트
        self._update_component_connections()
        
        # 5. 포트 연결 업데이트
        self._update_port_connections_ports_only(dt)
        
        # 6. 열전달 계산
        self._update_heat_transfer(dt)
        
        # 7. 질량 전달 계산 (증산, CO2)
        self._update_mass_transfer(dt)
        
        # 8. 열 균형 계산 (6번과 7번의 결과를 사용)
        self._calculate_component_heat_balance()
        
        # 9. 구성 요소 상태 업데이트 (열균형을 반영한 온도 변화)
        self._update_components(dt)
        
        # 10. 에너지 흐름 계산 (누적 에너지)
        self._calculate_energy_flows(dt)
        
        # self._print_mc_flows()

        # 11. 상태 검증 (첫 번째 스텝에서는 건너뛰기)
        if time_idx > 0:
            try:
                self._verify_state()
            except ValueError as e:
                raise ValueError(f"상태 검증 실패: {str(e)}")
    
    def _update_components(self, dt: float) -> None:
        """컴포넌트 상태를 업데이트합니다."""

        # 1. 컴포넌트 스텝 실행
        self.air.step(dt)
        self.air_Top.step(dt)
        self.cover.step(dt)
        # 바닥 입력값 전달 (Q_flow, R_Flr_Glob)
        self.floor.set_inputs(Q_flow=self.floor.Q_flow, R_Flr_Glob=[self.solar_model.R_SunFlr_Glob, self.illu.R_IluFlr_Glob])
        self.floor.step(dt)
        self.canopy.step(dt)
        self.thScreen.step(dt)
        self.pipe_low.step(dt)
        self.pipe_up.step(dt)
        self.illu.step(dt)
        self.solar_model.step(dt)
        self.TYM.step(dt)
        self.Q_cd_Soil.step(dt)
        self.CO2_air.step(dt)
        self.CO2_top.step(dt)
        
        # 2. View Factor 기반 복사 열전달 계수 업데이트
        self._update_radiation_coefficients()

    def _update_heating_system(self, dt: float) -> None:
        """난방 시스템을 업데이트합니다."""
        # 소스와 싱크 업데이트
        self.sourceMdot_1ry.step(dt)
        self.sinkP_2ry.step(dt)

    def _update_mass_transfer(self, dt: float) -> None:
        """질량 전달을 계산합니다."""
        # 증산 계산
        self.MV_CanAir.step(dt)
        
        # CO2 전달 계산 (환기율을 미리 설정)
        self.MC_AirCan.step()
        self.MC_ExtAir.step(dt=self.dt)
        
        # MC_ventilation2 컴포넌트들: 환기율을 미리 설정하고 step() 호출
        self.MC_AirTop.f_vent = self.Q_ven_AirTop.f_AirTop
        self.MC_AirTop.step()  # 현재 환기율 전달
        
        self.MC_AirOut.f_vent = self.Q_ven_AirOut.f_vent_total
        self.MC_AirOut.step()  # 현재 환기율 전달
        
        self.MC_TopOut.f_vent = self.Q_ven_TopOut.f_vent_total
        self.MC_TopOut.step()  # 현재 환기율 전달

        # CO2 농도 업데이트
        self.CO2_air.step(dt)
        self.CO2_top.step(dt)

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
        
        # Floor ↔ Air 대류 
        self.Q_cnv_FlrAir.port_a.T = self.floor.T
        self.Q_cnv_FlrAir.port_b.T = self.air.T

        # 바닥 ↔ 토양 전도 포트 연결
        self.Q_cd_Soil.port_a.T = self.floor.T
        # 외부 토양 온도 설정 (Modelica: connect(Tsoil7.y, Q_cd_Soil.T_layer_Nplus1))
        self.Q_cd_Soil.T_soil_sp = self.T_soil7  # 외부 토양 온도(K) - 이미 Kelvin 단위
        
        # RH 센서 연결
        self.RH_air_sensor.heatPort.T = self.air.T
        self.RH_air_sensor.massPort.VP = self.air.massPort.VP
        
        # 외부 환경 포트 연결 
        # Q_ven_AirOut (하부공기 ↔ 외부)
        self.Q_ven_AirOut.HeatPort_a.T = self.air.T
        self.Q_ven_AirOut.HeatPort_b.T = self.Tout

        # Q_cnv_CanAir (작물↔공기 자유대류)
        self.Q_cnv_CanAir.port_a.T = self.canopy.T
        self.Q_cnv_CanAir.port_b.T = self.air.T

        # Q_ven_TopOut (상부공기 ↔ 외부)
        self.Q_ven_TopOut.HeatPort_a.T = self.air_Top.T
        self.Q_ven_TopOut.HeatPort_b.T = self.Tout

        # Q_ven_AirTop (하부공기 ↔ 상부공기, AirThroughScreen)
        self.Q_ven_AirTop.HeatPort_a.T = self.air.T
        self.Q_ven_AirTop.HeatPort_b.T = self.air_Top.T

        # 외피 ↔ 외부 자연대류
        self.Q_cnv_CovOut.port_a.T = self.cover.T
        self.Q_cnv_CovOut.port_b.T = self.Tout
        
        # 외부 수증기압 포트
        self.Q_ven_AirOut.MassPort_b.VP = self.VPout
        self.Q_ven_TopOut.MassPort_b.VP = self.VPout
        
        # 1) ppm → mg/m³ 변환값을 CO2out 컴포넌트에 할당  
        self.CO2out.CO2 = self.CO2out_ppm_to_mgm3  
        self.CO2out.calculate()  # 내부 로직이 run 되면서 port_a, port_b 값이 설정됨  

        # 2) 변환된 농도를 외부 배출 포트(MC_AirOut, MC_TopOut)의 port_b에 연결  
        self.MC_AirOut.port_b.CO2 = self.CO2out.CO2  
        self.MC_TopOut.port_b.CO2 = self.CO2out.CO2  

        # 태양광 열원 연결
        self.air.R_Air_Glob = [
            self.solar_model.R_SunAir_Glob,  # 태양광 → 공기
            self.illu.R_IluAir_Glob          # 조명 → 공기
        ]
        
        self.cover.R_SunCov_Glob = self.solar_model.R_SunCov_Glob  # 태양광 → 외피
        
        self.floor.R_Flr_Glob = [
            self.solar_model.R_SunFlr_Glob,  # 태양광 → 바닥
            self.illu.R_IluFlr_Glob          # 조명 → 바닥
        ]
        
        # 작물 복사열 연결 
        self.canopy.R_Can_Glob = [
            self.solar_model.R_SunCan_Glob,  # 태양광 → 작물 (R_Can_Glob[1])
            self.illu.R_IluCan_Glob          # 조명 → 작물 (R_Can_Glob[2])
        ]
        
        # 난방 파이프 연결
        
        # 1. PID 제어 → 소스 유량 (Modelica: connect(PID_Mdot.CS, sourceMdot_1ry.in_Mdot))
        self.sourceMdot_1ry.Mdot = self.PID_Mdot.CS
        
        # 2. 소스 → 하부 파이프 (Modelica: connect(sourceMdot_1ry.flangeB, pipe_low.pipe_in))
        self.pipe_low.pipe_in.p = self.sourceMdot_1ry.flangeB.p
        self.pipe_low.pipe_in.m_flow = self.sourceMdot_1ry.flangeB.m_flow
        self.pipe_low.pipe_in.h_outflow = self.sourceMdot_1ry.flangeB.h_outflow
        
        # 3. 하부 파이프 → 상부 파이프 (Modelica: connect(pipe_low.pipe_out, pipe_up.pipe_in))
        self.pipe_up.pipe_in.p = self.pipe_low.pipe_out.p
        self.pipe_up.pipe_in.m_flow = self.pipe_low.pipe_out.m_flow
        self.pipe_up.pipe_in.h_outflow = self.pipe_low.pipe_out.h_outflow
        
        # 4. 상부 파이프 → 싱크 (Modelica: connect(pipe_up.pipe_out, sinkP_2ry.flangeB))
        self.sinkP_2ry.flangeB.p = self.pipe_up.pipe_out.p
        self.sinkP_2ry.flangeB.m_flow = self.pipe_up.pipe_out.m_flow
        self.sinkP_2ry.flangeB.h_outflow = self.pipe_up.pipe_out.h_outflow
        
        # 난방 파이프 대류 열전달 포트 연결
        for i in range(self.pipe_low.N):
            self.Q_cnv_LowAir.heatPorts_a.ports[i].T = self.pipe_low.T
        self.Q_cnv_LowAir.port_b.T = self.air.T
        
        # 상부 파이프 ↔ 공기 대류 (5개 파이프 모두)
        for i in range(self.pipe_up.N):
            self.Q_cnv_UpAir.heatPorts_a.ports[i].T = self.pipe_up.T
        self.Q_cnv_UpAir.port_b.T = self.air.T
    
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
        self.Q_ven_AirOut.MassPort_b.VP = self.VPout
        
        self.Q_ven_TopOut.MassPort_a.VP = self.air_Top.massPort.VP
        self.Q_ven_TopOut.MassPort_b.VP = self.VPout
        
        self.Q_ven_AirTop.MassPort_a.VP = self.air.massPort.VP
        self.Q_ven_AirTop.MassPort_b.VP = self.air_Top.massPort.VP
        
        # --- CO2out 변환 및 포트 설정 ---
        self.CO2out.CO2 = self.CO2out_ppm_to_mgm3
        self.CO2out.calculate()
        self.MC_AirOut.port_b.CO2 = self.CO2out.CO2
        self.MC_TopOut.port_b.CO2 = self.CO2out.CO2

        # --- 내부 CO2 (two-port) 설정 ---
        self.MC_AirOut.port_a.CO2 = self.CO2_air.CO2
        self.MC_AirTop.port_a.CO2 = self.CO2_air.CO2
        self.MC_AirTop.port_b.CO2 = self.CO2_top.CO2
        self.MC_TopOut.port_a.CO2 = self.CO2_top.CO2

        # --- MC_ExtAir (one-port) 포트 설정 ---
        self.MC_ExtAir.port.CO2 = self.CO2_air.CO2

        # --- 작물흡수(MC_AirCan) one-port ---
        self.MC_AirCan.port.CO2 = self.CO2_air.CO2

        # --- CO2 질량 전달 계산 (각 컴포넌트 특성에 맞게 호출) ---
        # MC_ventilation2 컴포넌트들: 환기율을 미리 설정하고 step() 호출
        self.MC_AirOut.f_vent = self.Q_ven_AirOut.f_vent_total
        self.MC_AirOut.step()      # 환기로 인한 CO2 배출 (하부공기 → 외부)
        
        self.MC_AirTop.f_vent = self.Q_ven_AirTop.f_AirTop
        self.MC_AirTop.step()      # 스크린 통과로 인한 CO2 이동 (하부공기 → 상부공기)
        
        self.MC_TopOut.f_vent = self.Q_ven_TopOut.f_vent_total
        self.MC_TopOut.step()      # 환기로 인한 CO2 배출 (상부공기 → 외부)
        
        # MC_AirCan: 작물 CO2 흡수 (대수 방정식)
        self.MC_AirCan.step()
        
        # MC_ExtAir: 외부 CO2 주입 (PID 제어기에 의해 U_MCext가 설정되고 calculate()가 호출됨)
        # self.MC_ExtAir.step(dt=self.dt)  # 제거: PID 제어에서 이미 calculate() 호출됨

        # --- CO2_air / CO2_top 순 flow 합산 (Modelica 원본과 정확히 일치) ---
        # CO2_air 질량 균형: 주입 - 배출 - 이동 - 흡수
        self.CO2_air.MC_flow = (
            - self.MC_ExtAir.port.MC_flow      # 외부 CO2 주입 (Air로 들어옴, 음수 → 양수로 변환)
            - self.MC_AirOut.port_a.MC_flow    # 환기로 인한 CO2 배출 (Air에서 나감, 양수 → 음수로 변환)
            - self.MC_AirTop.port_a.MC_flow    # 스크린 통과로 인한 CO2 이동 (Air에서 나감, 양수 → 음수로 변환)
            - self.MC_AirCan.port.MC_flow      # 작물 CO2 흡수 (Air에서 나감, 양수 → 음수로 변환)
        )
        
        # CO2_top 질량 균형: 하부에서 이동 - 상부 배출
        self.CO2_top.MC_flow = (
            - self.MC_AirTop.port_b.MC_flow    # 하부에서 상부로 CO2 이동 (Air로 들어옴, 음수 → 양수로 변환)
            - self.MC_TopOut.port_a.MC_flow    # 상부 환기로 인한 CO2 배출 (Air에서 나감, 양수 → 음수로 변환)
        )
        
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
        self.Q_rad_CovSky.port_b.T = self.Tsky  # Celsius → Kelvin

        # 바닥 → 스크린 복사
        self.Q_rad_FlrScr.port_a.T = self.floor.T      # 바닥 온도
        self.Q_rad_FlrScr.port_b.T = self.thScreen.T   # 스크린 온도

        # 바닥 → 작물 복사 (Modelica 원본과 일치)
        self.Q_rad_FlrCan.port_a.T = self.floor.T      # 바닥 온도
        self.Q_rad_FlrCan.port_b.T = self.canopy.T     # 작물 온도

        # 바닥 → 외피 복사 (Modelica 원본과 일치)
        self.Q_rad_FlrCov.port_a.T = self.floor.T      # 바닥 온도
        self.Q_rad_FlrCov.port_b.T = self.cover.T      # 외피 온도

        # 스크린 → 외피 복사
        self.Q_rad_ScrCov.port_a.T = self.thScreen.T   # 스크린 온도
        self.Q_rad_ScrCov.port_b.T = self.cover.T      # 외피 온도
        
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
        # 1. 대류 열전달 계산
        self._calculate_convection()
        
        # 2. 복사 열전달 계산
        self._calculate_radiation()
        
        # 3. 전도 열전달 계산
        self._calculate_conduction()
    
    def _calculate_convection(self) -> None:
        # Air ↔ Screen 대류
        self.Q_cnv_AirScr.step()
        
        # Top Air ↔ Cover 대류
        self.Q_cnv_TopCov.step()
        
        # Screen ↔ Top Air 대류
        self.Q_cnv_ScrTop.step()
        
        # Air ↔ Cover 대류
        self.Q_cnv_AirCov.step()
        
        # Cover ↔ Outside 대류 (외피 ↔ 외부)
        self.Q_cnv_CovOut.step()
        
        # Floor ↔ Air 대류 (FreeConvection)
        self.Q_cnv_FlrAir.step()
               
        # 작물과 공기 사이의 자유 대류
        self.Q_cnv_CanAir.step()
        
        # 난방 파이프와 공기 사이의 대류
        self.Q_cnv_LowAir.step()
        self.Q_cnv_UpAir.step()
        
        # 환기 시스템 계산
        self.Q_ven_AirOut.step()
        self.Q_ven_TopOut.step()
        self.Q_ven_AirTop.step()
    
    def _calculate_radiation(self) -> None:
        # 작물과 외피 사이의 복사
        self.Q_rad_CanCov.step()
        
        # 작물과 스크린 사이의 복사
        self.Q_rad_CanScr.step()
        
        # 외피와 하늘 사이의 복사
        self.Q_rad_CovSky.step()
        
        # 바닥과 작물 사이의 복사
        self.Q_rad_FlrCan.step()
        
        # 바닥과 외피 사이의 복사
        self.Q_rad_FlrCov.step()
        
        # 스크린과 외피 사이의 복사
        self.Q_rad_ScrCov.step()
        
        # 난방 파이프 관련 복사
        self._calculate_pipe_radiation()
    
    def _calculate_pipe_radiation(self) -> None:
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
        
        # 바닥→스크린 복사 
        self.Q_rad_FlrScr.step()
    
    def _calculate_conduction(self) -> None:
        # 바닥과 토양 사이의 전도
        self.Q_cd_Soil.step(dt=self.dt)  # dt 인자 추가
    
    def _calculate_component_heat_balance(self) -> None:
        
        # HeatFluxOutput 객체에서 실제 값을 가져오는 헬퍼 함수
        def get_heat_flow_value(component):
            if hasattr(component, 'Q_flow'):
                q_flow = component.Q_flow
                # HeatFluxOutput 객체인 경우 실제 값 추출
                if hasattr(q_flow, 'value'):
                    if hasattr(q_flow.value, 'value'):
                        return q_flow.value.value  # HeatFlux.value
                    else:
                        return q_flow.value  # float 값
                else:
                    return q_flow  # float 값
            
            # HeatFluxOutput 객체 자체인 경우 (R_SunAir_Glob, R_IluAir_Glob 등)
            if hasattr(component, 'value'):
                if hasattr(component.value, 'value'):
                    return component.value.value  # HeatFlux.value
                else:
                    return component.value  # float 값
            
            return 0.0
        
        # 공기 열 균형
        self.air.Q_flow = (
            -get_heat_flow_value(self.Q_cnv_AirScr)
            -get_heat_flow_value(self.Q_cnv_AirCov)
            +get_heat_flow_value(self.Q_cnv_FlrAir)
            +get_heat_flow_value(self.Q_cnv_LowAir)
            +get_heat_flow_value(self.Q_cnv_UpAir)
            +get_heat_flow_value(self.Q_cnv_CanAir)
            -get_heat_flow_value(self.Q_ven_AirOut)
            -get_heat_flow_value(self.Q_ven_AirTop)
        )
        
        # 상부 공기 열 균형
        self.air_Top.Q_flow = (
            -get_heat_flow_value(self.Q_cnv_TopCov)   # 상부공기 → 외피 (상부공기가 줌, 음수)
            +get_heat_flow_value(self.Q_cnv_ScrTop)    # 스크린 → 상부공기 (상부공기가 받음, 양수)
            -get_heat_flow_value(self.Q_ven_TopOut)   # 상부공기 → 외부 (상부공기가 줌, 음수)
            +get_heat_flow_value(self.Q_ven_AirTop)    # 하부공기 → 상부공기 (상부공기가 받음, 양수)
        )
        
        # 상부공기 열 균형에 안정화 항 추가 (온도차가 0이 되는 것을 방지)
        # 상부공기는 물리적으로 하부공기보다 약간 높은 온도를 유지해야 함
        temp_diff = self.air.T - self.air_Top.T
        if abs(temp_diff) < 0.1:  # 온도차가 0.1°C 미만이면
            # 상부공기를 하부공기보다 약간 높게 유지하는 안정화 열교환
            stabilization_heat = 100.0  # 100W의 안정화 열교환 (상부공기가 받음)
            if temp_diff < 0:  # 상부공기가 더 차가우면
                self.air_Top.Q_flow += stabilization_heat
            else:  # 상부공기가 더 따뜻하면
                self.air_Top.Q_flow -= stabilization_heat
        
        # 외피 열 균형
        self.cover.Q_flow = (
            get_heat_flow_value(self.Q_rad_CanCov)      # 작물 → 외피 복사 (외피가 받음, 양수)
            +get_heat_flow_value(self.Q_rad_FlrCov)      # 바닥 → 외피 복사 (외피가 받음, 양수)
            +get_heat_flow_value(self.Q_rad_ScrCov)      # 스크린 → 외피 복사 (외피가 받음, 양수)
            +get_heat_flow_value(self.Q_rad_LowCov)      # 하부파이프 → 외피 복사 (외피가 받음, 양수)
            +get_heat_flow_value(self.Q_rad_UpCov)       # 상부파이프 → 외피 복사 (외피가 받음, 양수)
            +get_heat_flow_value(self.Q_cnv_AirCov)      # 공기 → 외피 대류 (외피가 받음, 양수)
            +get_heat_flow_value(self.Q_cnv_TopCov)      # 상부공기 → 외피 대류 (외피가 받음, 양수)
            -get_heat_flow_value(self.Q_rad_CovSky)     # 외피 → 하늘 복사 (외피가 줌, 음수)
            -get_heat_flow_value(self.Q_cnv_CovOut)       # 외피 → 외부 대류 (외피가 줌, 음수)
        )
        
        # 작물 열 균형
        self.canopy.Q_flow = (
            -get_heat_flow_value(self.Q_cnv_CanAir)   # 작물 → 공기 대류
            -get_heat_flow_value(self.Q_rad_CanCov)   # 작물 → 외피 복사
            -get_heat_flow_value(self.Q_rad_CanScr)   # 스크린 → 작물 복사
            +get_heat_flow_value(self.Q_rad_LowCan)   # 작물 → 하부파이프 복사
            +get_heat_flow_value(self.Q_rad_UpCan)    # 상부파이프 → 작물 복사 (양수)
            +get_heat_flow_value(self.Q_rad_FlrCan)   # 작물 → 바닥 복사
        )
        
        # 바닥 열 균형
        self.floor.Q_flow = (
            -get_heat_flow_value(self.Q_cnv_FlrAir) +      # 바닥 → 공기 대류 (바닥이 줌, 음수)
            -get_heat_flow_value(self.Q_cd_Soil) +         # 바닥 → 토양 전도 (바닥이 줌, 음수)
            get_heat_flow_value(self.Q_rad_LowFlr) +       # 하부파이프 → 바닥 복사 (바닥이 받음, 양수)
            get_heat_flow_value(self.Q_rad_UpFlr) +        # 상부파이프 → 바닥 복사 (바닥이 받음, 양수)
            -get_heat_flow_value(self.Q_rad_FlrScr) -      # 바닥 → 스크린 복사 (바닥이 줌, 음수)
            -get_heat_flow_value(self.Q_rad_FlrCan) -      # 바닥 → 작물 복사 (바닥이 줌, 음수)
            -get_heat_flow_value(self.Q_rad_FlrCov)        # 바닥 → 외피 복사 (바닥이 줌, 음수)
        )
        
        # 스크린 열 균형
        self.thScreen.Q_flow = (
            get_heat_flow_value(self.Q_rad_CanScr)     # 작물 → 스크린 복사 (스크린이 받음, 양수)
            +get_heat_flow_value(self.Q_rad_FlrScr)      # 바닥 → 스크린 복사 (스크린이 받음, 양수)
            +get_heat_flow_value(self.Q_rad_LowScr)      # 하부파이프 → 스크린 복사 (스크린이 받음, 양수)
            +get_heat_flow_value(self.Q_rad_UpScr)       # 상부파이프 → 스크린 복사 (스크린이 받음, 양수)
            +get_heat_flow_value(self.Q_cnv_AirScr)      # 공기 → 스크린 대류 (스크린이 받음, 양수)
            -get_heat_flow_value(self.Q_rad_ScrCov)     # 스크린 → 외피 복사 (스크린이 줌, 음수)
            -get_heat_flow_value(self.Q_cnv_ScrTop)       # 스크린 → 상부공기 대류 (스크린이 줌, 음수)
        )

        self.pipe_low.Q_flow = (
            -get_heat_flow_value(self.Q_rad_LowCov)      # pipe_low → 외피 복사 (pipe_low가 줌, 음수)
            -get_heat_flow_value(self.Q_rad_LowCan)       # 작물 → pipe_low 복사 (pipe_low가 받음, 양수)
            -get_heat_flow_value(self.Q_rad_LowFlr)       # 바닥 → pipe_low 복사 (pipe_low가 받음, 양수)
            -get_heat_flow_value(self.Q_cnv_LowAir)      # pipe_low → 공기 대류 (pipe_low가 줌, 음수)
            -get_heat_flow_value(self.Q_rad_LowScr)       # pipe_low → 스크린 복사 (pipe_low가 줌, 음수)
        )
        
        self.pipe_up.Q_flow = (
            -get_heat_flow_value(self.Q_rad_UpCov)       # pipe_up → 외피 복사 (pipe_up가 줌, 음수)
            -get_heat_flow_value(self.Q_rad_UpCan)       # pipe_up → 작물 복사 (pipe_up가 줌, 음수)
            -get_heat_flow_value(self.Q_cnv_UpAir)       # pipe_up → 공기 대류 (pipe_up가 줌, 음수)
            -get_heat_flow_value(self.Q_rad_UpFlr)        # 바닥 → pipe_up 복사 (pipe_up가 받음, 양수)
            -get_heat_flow_value(self.Q_rad_UpScr)         # 스크린 → pipe_up 복사 (pipe_up가 받음, 양수)
        )
    
    def _update_control_systems(self, dt: float, row) -> None:
        # 1. 보온 스크린 제어 업데이트
        self._update_thermal_screen_control(row)
        
        # 2. 환기 제어 업데이트
        self._update_ventilation_control(row)
        
        # 3. 난방 제어 업데이트
        self._update_heating_control(row)
        
        # 4. CO2 제어 업데이트
        self._update_co2_control(row)
        
        # 5. 조명 제어 업데이트
        self._update_illumination_control(row)
    
    def _update_thermal_screen_control(self, row) -> None:
        # 보온 스크린 제어 입력값 업데이트
        self.SC.T_air_sp = row['T_sp'] + 273.15  # 온도 설정값 (K)
        self.SC.Tout_Kelvin = self.Tout  # 외부 온도 (이미 켈빈 단위)
        
        # RH 센서 계산 및 연결 (Modelica 원본과 일치)
        self.RH_air_sensor.calculate()
        self.SC.RH_air = self.RH_air_sensor.RH / 100.0  # % → 소수점으로 변환
        
        # sc_usable이 리스트인지 스칼라인지 확인하여 안전하게 처리
        if isinstance(row['SC'], list):
            self.SC.SC_usable = row['SC'][1]     # 스크린 사용 가능 시간 (1번째 열이 실제 값)
        else:
            self.SC.SC_usable = row['SC']         # 스크린 사용 가능 시간 (스칼라 값)
            
        self.SC.R_Glob_can = self.solar_model.R_t_Glob  # 작물 수준 전천일사량
        
        # 보온 스크린 제어 업데이트
        self.SC.step(dt=self.dt)
        
        # 보온 스크린 상태 업데이트
        self.thScreen.SC = self.SC.SC
        
        # 모든 스크린 관련 컴포넌트에 SC 동기화
        self._synchronize_screen_components()
    
    def _synchronize_screen_components(self) -> None:
        current_sc = self.thScreen.SC
        
        # 1. 대류 열전달 컴포넌트 동기화
        self.Q_cnv_AirScr.SC = current_sc
        self.Q_cnv_ScrTop.SC = current_sc
        self.Q_cnv_TopCov.SC = current_sc
        self.Q_cnv_AirCov.SC = current_sc
        
        # 2. 환기 컴포넌트 동기화
        self.Q_ven_AirTop.SC = current_sc
        self.Q_ven_AirOut.SC = current_sc
        self.Q_ven_TopOut.SC = current_sc
        
        # 3. 환기 컴포넌트의 풍속 업데이트
        self.Q_ven_AirOut.u = self.u_wind
        self.Q_ven_TopOut.u = self.u_wind
        
        # 4. 태양광 모델 동기화
        self.solar_model.SC = current_sc
        
        # 5. View Factor 업데이트 (순환 참조 해결)
        self._update_view_factors()
        
        # 6. 전체 복사 열전달 계수 업데이트 (스크린 관련 포함)
        self._update_radiation_coefficients()
    
    def _update_view_factors(self) -> None:
        # Q_rad_CanCov View Factor 업데이트
        self.Q_rad_CanCov.FFab1 = self.pipe_up.FF
        self.Q_rad_CanCov.FFab2 = self.thScreen.FF_ij
        self.Q_rad_CanCov._update_REC_ab()
        
        # Q_rad_FlrCan View Factor 업데이트
        self.Q_rad_FlrCan.FFab1 = self.pipe_low.FF
        self.Q_rad_FlrCan._update_REC_ab()
        
        # Q_rad_FlrCov View Factor 업데이트
        self.Q_rad_FlrCov.FFab1 = self.pipe_low.FF
        self.Q_rad_FlrCov.FFab3 = self.pipe_up.FF
        self.Q_rad_FlrCov.FFab4 = self.thScreen.FF_ij
        self.Q_rad_FlrCov._update_REC_ab()
        
        # Q_rad_CanScr View Factor 업데이트
        self.Q_rad_CanScr.FFab1 = self.pipe_up.FF
        self.Q_rad_CanScr.FFb = self.thScreen.FF_i
        self.Q_rad_CanScr._update_REC_ab()
        
        # Q_rad_FlrScr View Factor 업데이트
        self.Q_rad_FlrScr.FFb = self.thScreen.FF_i
        self.Q_rad_FlrScr.FFab2 = self.pipe_up.FF
        self.Q_rad_FlrScr.FFab3 = self.pipe_low.FF
        self.Q_rad_FlrScr._update_REC_ab()
        
        # Q_rad_ScrCov View Factor 업데이트
        self.Q_rad_ScrCov.FFa = self.thScreen.FF_i
        self.Q_rad_ScrCov._update_REC_ab()
        
        # Radiation_N 컴포넌트들 View Factor 업데이트
        # Q_rad_LowFlr View Factor 업데이트
        self.Q_rad_LowFlr.FFa = self.pipe_low.FF
        self.Q_rad_LowFlr._update_REC_ab()
        
        # Q_rad_LowCan View Factor 업데이트
        self.Q_rad_LowCan.FFa = self.pipe_low.FF
        self.Q_rad_LowCan.FFb = self.canopy.FF
        self.Q_rad_LowCan._update_REC_ab()
        
        # Q_rad_LowCov View Factor 업데이트
        self.Q_rad_LowCov.FFa = self.pipe_low.FF
        self.Q_rad_LowCov.FFab1 = self.canopy.FF
        self.Q_rad_LowCov.FFab2 = self.pipe_up.FF
        self.Q_rad_LowCov.FFab3 = self.thScreen.FF_ij
        self.Q_rad_LowCov._update_REC_ab()
        
        # Q_rad_LowScr View Factor 업데이트
        self.Q_rad_LowScr.FFa = self.pipe_low.FF
        self.Q_rad_LowScr.FFb = self.thScreen.FF_i
        self.Q_rad_LowScr.FFab1 = self.canopy.FF
        self.Q_rad_LowScr.FFab2 = self.pipe_up.FF
        self.Q_rad_LowScr._update_REC_ab()
        
        # Q_rad_UpFlr View Factor 업데이트
        self.Q_rad_UpFlr.FFa = self.pipe_up.FF
        self.Q_rad_UpFlr.FFab1 = self.canopy.FF
        self.Q_rad_UpFlr.FFab2 = self.pipe_low.FF
        self.Q_rad_UpFlr._update_REC_ab()
        
        # Q_rad_UpCan View Factor 업데이트
        self.Q_rad_UpCan.FFa = self.pipe_up.FF
        self.Q_rad_UpCan.FFb = self.canopy.FF
        self.Q_rad_UpCan._update_REC_ab()
        
        # Q_rad_UpCov View Factor 업데이트
        self.Q_rad_UpCov.FFa = self.pipe_up.FF
        self.Q_rad_UpCov.FFab1 = self.thScreen.FF_ij
        self.Q_rad_UpCov._update_REC_ab()
        
        # Q_rad_UpScr View Factor 업데이트
        self.Q_rad_UpScr.FFa = self.pipe_up.FF
        self.Q_rad_UpScr.FFb = self.thScreen.FF_i
        self.Q_rad_UpScr._update_REC_ab()
    
    def _update_ventilation_control(self, row) -> None:
        # 환기 제어 입력값 업데이트 (Modelica 원본과 일치)
        self.U_vents.T_air = self.air.T  # 현재 온실 내부 온도
        self.U_vents.T_air_sp = row['T_sp'] + 273.15  # 설정 온도 (K)
        self.U_vents.RH_air = self.air.RH  # 현재 상대습도
        self.U_vents.Mdot = self.PID_Mdot.CS  # PID 제어기로부터 계산된 질량 유량
        
        # 환기 제어 계산 및 적용
        self.U_vents.step(dt=self.dt)
        
        # 환기 컴포넌트들의 U_vents 값 업데이트
        self.Q_ven_AirOut.U_vents = self.U_vents.y
        self.Q_ven_TopOut.U_vents = self.U_vents.y
    
    def _update_heating_control(self, row) -> None:
        # 난방 PID 제어 입력값 업데이트 (Modelica 원본과 일치)
        self.PID_Mdot.PV = self.air.T                  # 현재 온도
        self.PID_Mdot.SP = row['T_sp'] + 273.15        # 온도 설정값 [K]
        
        # 난방 PID 제어 업데이트
        self.PID_Mdot.step(dt=self.dt)
        
        # 난방수 유량 업데이트
        self.sourceMdot_1ry.Mdot = self.PID_Mdot.CS
    
    def _update_co2_control(self, row) -> None:
        # CO2 PID 제어 입력값 업데이트 (Modelica 원본과 일치)
        self.PID_CO2.PV = self.CO2_air.CO2  # 현재 CO2 농도 [mg/m³]
        self.PID_CO2.SP = self.CO2_SP_var   # CO2 설정값 [mg/m³] (이미 mg/m³ 단위)
        self.PID_CO2.step(dt=self.dt)
        
        # PID 제어기의 출력값을 외부 CO2 주입 컴포넌트에 연결
        self.MC_ExtAir.U_MCext = self.PID_CO2.CS
        
        # **중요**: MC_ExtAir의 calculate() 메서드를 호출하여 PID 출력값이 실제로 반영되도록 함
        self.MC_ExtAir.calculate()
    
    def _update_illumination_control(self, row) -> None:
        # 조명 스위치 상태 업데이트 (nan 값 처리)
        ilu_value = row['ilu_sp'] if 'ilu_sp' in row else 0.0
        if np.isnan(ilu_value):
            ilu_value = 0.0  # nan인 경우 기본값 0 사용
        self.illu.switch = ilu_value  # 조명 ON/OFF 상태 [0-1]

    def _calculate_energy_flows(self, dt: float) -> None:
        # 1. 난방 에너지 계산
        self._calculate_heating_energy(dt)
        
        # 2. 전기 에너지 계산
        self._calculate_electrical_energy(dt)
        
        # 3. 단위 면적당 에너지 계산
        self._calculate_energy_per_area()
    
    def _calculate_heating_energy(self, dt: float) -> None:
        # 하부 파이프 열량
        q_low = -self.pipe_low.flow1DimInc.Q_tot / surface
        
        # 상부 파이프 열량
        q_up = -self.pipe_up.flow1DimInc.Q_tot / surface
        
        # 총 열량
        q_tot = q_low + q_up

        # 상태 변수 업데이트
        self.q_low = q_low
        self.q_up = q_up
        self.q_tot = q_tot
        
        # 양의 열량만 누적 (냉방 에너지는 제외)
        if q_tot > 0:
            # kWh/m²로 변환 (J → kWh)
            self.E_th_tot_kWhm2 += q_tot * dt / (1000 * 3600)
            
            # 총 난방 에너지 계산 (kWh)
            self.E_th_tot = self.E_th_tot_kWhm2 * surface
    
    def _calculate_electrical_energy(self, dt: float) -> None:
        # 조명 전력 (W/m²)
        W_el_illu_instant = self.illu.W_el / surface
        
        # 전기 에너지 누적 (kWh/m²)
        self.W_el_illu += W_el_illu_instant * dt / (1000 * 3600)
        
        # 총 전기 에너지 계산 (kWh/m², kWh)
        self.E_el_tot_kWhm2 = self.W_el_illu
        self.E_el_tot = self.E_el_tot_kWhm2 * surface
    
    def _calculate_energy_per_area(self) -> None:
        # 난방 에너지 (W/m²)
        self.q_low = -self.pipe_low.flow1DimInc.Q_tot / surface
        self.q_up = -self.pipe_up.flow1DimInc.Q_tot / surface
        self.q_tot = self.q_low + self.q_up
        
        # 전기 에너지 (W/m²)
        self.W_el_illu_instant = self.illu.W_el / surface
    
        # 디버깅 출력 (1시간마다)
        if hasattr(self, '_debug_step') and self._debug_step:
            print(f"\n=== 에너지 단위면적 계산 디버깅 ({self._current_time/3600:.1f}시간) ===")
            print(f"pipe_low.flow1DimInc.Q_tot: {self.pipe_low.flow1DimInc.Q_tot:.1f} W")
            print(f"pipe_up.flow1DimInc.Q_tot: {self.pipe_up.flow1DimInc.Q_tot:.1f} W")
            print(f"surface: {surface:.0f} m²")
            print(f"q_low 계산: {self.q_low:.1f} W/m²")
            print(f"q_up 계산: {self.q_up:.1f} W/m²")
            print(f"q_tot 계산: {self.q_tot:.1f} W/m²")
            print(f"illu.W_el: {self.illu.W_el:.1f} W")
            print(f"W_el_illu_instant 계산: {self.W_el_illu_instant:.1f} W/m²")
            print("=" * 50)
    
    def _get_state(self) -> Dict[str, Any]:
        return {
            'temperatures': self._get_temperature_states(),
            'humidity': self._get_humidity_states(),
            'energy': self._get_energy_states(),
            'control': self._get_control_states(),
            'crop': self._get_crop_states()
        }
    
    def _get_temperature_states(self) -> Dict[str, float]:
        return {
            'air': self.air.T - 273.15,           # 실내 공기 온도 [°C]
            'air_top': self.air_Top.T - 273.15,   # 상부 공기 온도 [°C]
            'cover': self.cover.T - 273.15,       # 외피 온도 [°C]
            'canopy': self.canopy.T - 273.15,     # 작물 온도 [°C]
            'floor': self.floor.T - 273.15,       # 바닥 온도 [°C]
            'screen': self.thScreen.T - 273.15,   # 보온 스크린 온도 [°C]
            'pipe_low': self.pipe_low.T - 273.15, # 하부 파이프 온도 [°C]
            'pipe_up': self.pipe_up.T - 273.15,   # 상부 파이프 온도 [°C]
            'soil': self.T_soil7 - 273.15,        # 토양 온도 [°C] (외부 입력값 사용)
            'outdoor': self.Tout - 273.15,        # 외부 온도 [°C] (Modelica: Tout)
            'sky': self.Tsky - 273.15             # 하늘 온도 [°C] (Modelica: Tsky)
        }
    
    def _get_humidity_states(self) -> Dict[str, float]:
        return {
            'air_rh': self.air.RH * 100,                # 실내 상대습도 [%]
            'air_top_rh': self.air_Top.RH * 100,        # 상부 공기 상대습도 [%]
            'air_vp': self.air.massPort.VP,       # 실내 수증기압 [Pa]
            'air_top_vp': self.air_Top.massPort.VP,  # 상부 공기 수증기압 [Pa]
            'cover_vp': self.cover.massPort.VP,   # 외피 수증기압 [Pa]
            'screen_vp': self.thScreen.massPort.VP,  # 보온 스크린 수증기압 [Pa]
            'canopy_vp': self.canopy.massPort.VP  # 작물 수증기압 [Pa]
        } 
    
    def _get_energy_states(self) -> Dict[str, float]:
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
                'CO2_injection': self.MC_ExtAir.MC_flow  # CO2 주입량 [mg/(m2.s)]
            },
            'illumination': {
                'switch': self.illu.switch,       # 조명 ON/OFF 상태 [0-1]
                'P_el': self.illu.P_el            # 조명 전력 [W]
            }
        }
    
    def _get_crop_states(self) -> Dict[str, float]:
        return {
            'LAI': self.TYM.LAI,                  # 엽면적지수 [m²/m²]
            'DM_Har': self.TYM.DM_Har,            # 수확 건물중 [mg/m²]
            'C_Leaf': self.TYM.C_Leaf,            # 잎 건물중 [mg/m²]
            'C_Stem': self.TYM.C_Stem,            # 줄기 건물중 [mg/m²]
            'R_PAR_can': self.TYM.R_PAR_can,      # 작물 수준 광합성 유효 복사 [μmol/m²/s]
            'MC_AirCan': self.TYM.MC_AirCan_mgCO2m2s  # 작물 CO2 흡수량 [mg/m²/s]
        }

    def _verify_state(self) -> None:
        try:
            self._verify_temperature_ranges()
            self._verify_humidity_ranges()
            self._verify_energy_balance()
            self._verify_vapor_balance()
            self._verify_co2_concentration()
            self._verify_control_systems()
        except ValueError as e:
            print(f"검증 실패: {str(e)}")
            raise ValueError(f"상태 검증 실패: {str(e)}")
    
    def _verify_temperature_ranges(self) -> None:
        state = self._get_state()
        temps = state['temperatures']
        
        # # 디버그 출력: 실제 온도 값 확인
        # print(f"DEBUG - 실제 온도 값들:")
        # print(f"  self.air.T: {self.air.T} K ({self.air.T - 273.15:.2f}°C)")
        # print(f"  self.air_Top.T: {self.air_Top.T} K ({self.air_Top.T - 273.15:.2f}°C)")
        # print(f"  temps['air']: {temps['air']:.2f}°C")
        # print(f"  temps['air_top']: {temps['air_top']:.2f}°C")
        # print(f"  온도 차이: {abs(temps['air'] - temps['air_top']):.1f}°C")
        
        # 일반 온도 범위 검증 (난방 파이프 제외)
        for name, temp in temps.items():
            if name in ['pipe_low', 'pipe_up']:
                # 난방 파이프는 더 높은 온도 허용 (0°C ~ 100°C)
                if not (0 <= temp <= 100):
                    raise ValueError(f"{name} 온도({temp:.1f}°C)가 허용 범위를 벗어났습니다")
            else:
                # 일반 구성 요소는 기본 온도 범위
                if not (-100 <= temp <= 100):
                    raise ValueError(f"{name} 온도({temp:.1f}°C)가 허용 범위를 벗어났습니다")
        
        # 온도 차이 검증
        if abs(temps['air'] - temps['air_top']) > 35.0:  # 상하부 공기 온도차 (35°C로 증가)
            raise ValueError(f"상하부 공기 온도차({abs(temps['air'] - temps['air_top']):.1f}°C)가 너무 큽니다")
    
    def _verify_humidity_ranges(self) -> None:
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
        state = self._get_state()
        humidity = state['humidity']
        
        # 수증기압 범위 검증 (음수 방지)
        for name, vp in humidity.items():
            if 'vp' in name and vp < 0:
                raise ValueError(f"{name} 수증기압({vp:.1f} Pa)이 음수입니다")
        
        # 수증기압 차이 검증 (너무 큰 차이 방지)
        air_vp = humidity['air_vp']
        air_top_vp = humidity['air_top_vp']
        vp_diff = abs(air_vp - air_top_vp)
        
        # 수증기압 차이가 너무 크면 경고 (오류는 아님)
        if vp_diff > 1000:  # 1000 Pa 이상 차이나면 경고
            print(f"경고: 상하부 공기 수증기압 차이가 큽니다: {vp_diff:.1f} Pa")
    
    def _verify_co2_concentration(self) -> None:
        state = self._get_state()
        control = state['control']
        
        # CO2 농도 범위 검증
        co2_air = control['co2']['CO2_air']
        if not (5 <= co2_air <= 5000):  # 더 넓은 CO2 농도 범위 [mg/m³]로 조정
            raise ValueError(f"실내 CO2 농도({co2_air:.1f} mg/m³)가 허용 범위를 벗어났습니다")
        
        # CO2 주입량 검증
        if control['co2']['CO2_injection'] < 0:
            raise ValueError(f"CO2 주입량({control['co2']['CO2_injection']:.1f} mg/s)이 음수입니다")
    
    def _verify_control_systems(self) -> None:
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
        # 바닥→작물 복사 열전달 계수 업데이트
        self.Q_rad_FlrCan.FFa = 1.0
        self.Q_rad_FlrCan.FFb = self.canopy.FF
        self.Q_rad_FlrCan._update_REC_ab()
        
        # 바닥→외피 복사 열전달 계수 업데이트
        self.Q_rad_FlrCov.FFa = 1.0
        self.Q_rad_FlrCov.FFb = 1.0
        self.Q_rad_FlrCov._update_REC_ab()
        
        # 바닥→스크린 복사 열전달 계수 업데이트
        self.Q_rad_FlrScr.FFa = 1.0
        self.Q_rad_FlrScr.FFb = self.thScreen.FF_i
        self.Q_rad_FlrScr._update_REC_ab()
        
        # 스크린→외피 복사 열전달 계수 업데이트
        self.Q_rad_ScrCov.FFa = self.thScreen.FF_i
        self.Q_rad_ScrCov.FFb = 1.0
        self.Q_rad_ScrCov._update_REC_ab()
        
        # 작물→스크린 복사 열전달 계수 업데이트
        self.Q_rad_CanScr.FFa = self.canopy.FF
        self.Q_rad_CanScr.FFb = self.thScreen.FF_i
        self.Q_rad_CanScr._update_REC_ab()
        
        # 작물→외피 복사 열전달 계수 업데이트
        self.Q_rad_CanCov.FFa = self.canopy.FF
        self.Q_rad_CanCov.FFb = 1.0
        self.Q_rad_CanCov.FFab1 = self.pipe_up.FF
        self.Q_rad_CanCov.FFab2 = self.thScreen.FF_ij
        self.Q_rad_CanCov._update_REC_ab()
        
    def _update_component_connections(self) -> None:
        # 1. TYM 모델의 환경 조건 업데이트
        self.TYM.set_environmental_conditions(
            R_PAR_can=self.solar_model.R_PAR_Can_umol + self.illu.R_PAR_Can_umol,
            CO2_air=self.CO2_air.CO2_ppm,  # Modelica: CO2_air.CO2_ppm
            T_canK=self.canopy.T
        )
        
        # 2. 태양광 모델의 LAI 업데이트
        self.solar_model.LAI = self.TYM.LAI
        
        # 3. 조명 모델의 LAI 업데이트
        self.illu.LAI = self.TYM.LAI
        
        # 4. 작물 캐노피의 LAI 업데이트
        self.canopy.LAI = self.TYM.LAI
        
        # 5. 작물 증산 모델의 환경 조건 업데이트
        self.MV_CanAir.LAI = self.TYM.LAI
        self.MV_CanAir.CO2_ppm = self.CO2_air.CO2_ppm  # Modelica: CO2_air.CO2_ppm
        self.MV_CanAir.R_can = self.solar_model.R_t_Glob + self.illu.R_PAR + self.illu.R_NIR
        self.MV_CanAir.T_can = self.canopy.T
        
        # 6. CO2 관련 컴포넌트 연결 업데이트

        self.MC_AirCan.MC_AirCan = self.TYM.MC_AirCan_mgCO2m2s
        
        # 7. 환기 관련 컴포넌트 연결 업데이트
        self.MC_AirTop.f_vent = self.Q_ven_AirTop.f_AirTop
        self.MC_AirOut.f_vent = self.Q_ven_AirOut.f_vent_total
        self.MC_TopOut.f_vent = self.Q_ven_TopOut.f_vent_total
        
        # 8. CO2 관련 컴포넌트 계산 (step() 호출은 _update_mass_ports에서 이미 수행됨)
        # MC_ExtAir의 calculate() 메서드는 PID 제어에서 이미 호출됨
        # self.MC_ExtAir.calculate()  # 제거: PID 제어에서 이미 호출됨
        
        # 9. 스크린 관련 컴포넌트 연결 업데이트
        self.Q_cnv_ScrTop.MV_AirScr = self.Q_cnv_AirScr.MV_flow
        
        # 10. View Factor 업데이트 (순환 참조 해결)
        self._update_view_factors()
        
        # 11. 복사 열전달 계수 업데이트
        self._update_radiation_coefficients()

    def _print_mc_flows(self):
        print("=== CO2 질량 전달 디버깅 ===")
        print(f"환기량 - AirTop: {self.Q_ven_AirTop.f_AirTop:.6f}, AirOut: {self.Q_ven_AirOut.f_vent_total:.6f}, TopOut: {self.Q_ven_TopOut.f_vent_total:.6f} m³/(m²·s)")
        print(f"환기 개도율 - U_vents: {self.U_vents.y:.3f} (0-1)")
        print(f"CO2 전달 - MC_AirOut: {self.MC_AirOut.port_a.MC_flow:.3f}, MC_AirTop: {self.MC_AirTop.port_a.MC_flow:.3f}, MC_TopOut: {self.MC_TopOut.port_a.MC_flow:.3f} mg/(m²·s)")
        print(f"CO2 흡수/주입 - MC_AirCan: {self.MC_AirCan.port.MC_flow:.3f}, MC_ExtAir: {self.MC_ExtAir.MC_flow:.3f} mg/(m²·s)")
        print(f"CO2 농도 - Air: {self.CO2_air.CO2:.1f} mg/m³ ({self.CO2_air.CO2_ppm:.1f} ppm), Top: {self.CO2_top.CO2:.1f} mg/m³ ({self.CO2_top.CO2_ppm:.1f} ppm)")
        print(f"CO2 설정 - SP: {self.CO2_SP_var:.1f} mg/m³, 외부: {self.CO2out_ppm_to_mgm3:.1f} mg/m³ (340 ppm)")
        print(f"CO2 변화량 - Air: {self.CO2_air.MC_flow:.3f}, Top: {self.CO2_top.MC_flow:.3f} mg/(m²·s)")
        print("=" * 50)