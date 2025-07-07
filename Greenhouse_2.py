"""
Greenhouse_2.py
온실 시뮬레이션 모델 (Modelica Greenhouse_1.mo의 Python 구현)
- Venlo-type 온실의 기후 시뮬레이션
- 토마토 작물 재배 (12월 10일 ~ 11월 22일)
- 날씨 데이터: TMY (Typical Meteorological Year) for Brussels
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple, Any
from port_connection_manager import PortConnectionManager, PipeConnectionManager, PortType
from Functions.WaterVapourPressure import WaterVapourPressure

# Constants
# Physical constants
GAS_CONSTANT = 8314.0  # Universal gas constant [J/(kmol·K)]
WATER_MOLAR_MASS = 18.0  # Water molar mass [kg/kmol]
LATENT_HEAT_VAPORIZATION = 2.5e6  # Latent heat of vaporization [J/kg]

# Greenhouse dimensions
surface = 1.4e4  # Greenhouse floor area [m²]

# File paths
WEATHER_DATA_PATH = "./10Dec-22Nov.txt"
SETPOINT_DATA_PATH = "./SP_10Dec-22Nov.txt"
SCREEN_USABLE_PATH = "./SC_usable_10Dec-22Nov.txt"

class Greenhouse_2:

    def __init__(self, time_unit_scaling: float = 1.0):
        """온실 시뮬레이션 모델 초기화"""
        self.time_unit_scaling = time_unit_scaling
        self.dt = 0.0  # 시간 간격 초기화
        
        # 포트 연결 관리자들 초기화
        self.port_manager = PortConnectionManager()
        self.pipe_manager = PipeConnectionManager()
        
        # 변경 감지를 위한 플래그
        self._last_screen_state = None
        self._last_heating_state = None
        self._last_time_idx = -1
        
        # 성능 모니터링
        self._connection_update_count = 0
        self._total_connection_time = 0.0
        
        # 누락된 속성 초기화
        self.W_el_illu_instant = 0.0  # 순간 조명 전력 [W/m²]
        
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
        
        print("Greenhouse_2 초기화 완료")
    
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
            
            # 6. 난방 파이프 온도 설정
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
            
            # 외부 RH 계산 (txt 파일의 2번째 열)
            # external_rh = row['RH_out'] / 100.0  # 95% → 0.95
            self.air.RH = 0.9
            self.air_Top.RH = 0.9  # 상부 공기 초기 상대습도를 90%로 설정
            
            # CO₂ 농도 초기화
            self.CO2_air.CO2 = 1940.0  # 하부공기
            self.CO2_top.CO2 = 1940.0  # 상부공기도 동일하게 초기화
            
        except Exception as e:
            print(f"초기 데이터 로드 실패: {e}")
            # 기본값 유지
    
    def _init_components(self) -> None:
        """컴포넌트 초기화 - 모듈화된 초기화 사용"""
        # 컴포넌트 초기화 모듈 사용
        from component_initializer import ComponentInitializer
        
        # 컴포넌트 초기화
        initializer = ComponentInitializer(surface=surface, u_wind=self.u_wind)
        components = initializer.initialize_all_components()
        
        # 컴포넌트들을 인스턴스 속성으로 설정
        for name, component in components.items():
            setattr(self, name, component)
        
        # 컴포넌트 간 연결 업데이트 (순환 참조 해결)
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
        self.Tair_setpoint = row['T_air_sp'] + 273.15
        
        # CO2 설정값 [mg/m³]
        self.CO2_SP_var = row['CO2_sp'] * 1.94

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
        
        # 3. 컴포넌트 간 연결 업데이트
        self._update_component_connections()
        
        # 4. 포트 연결 업데이트 (최적화된 버전 사용)
        self._update_port_connections_optimized(dt)
        
        # 5. 난방 시스템 업데이트 (in_Mdot 설정 후에 호출)
        self._update_heating_system(dt)  # 추가
        
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
        
        # # 11. 상태 검증 (첫 번째 스텝에서는 건너뛰기)
        # if time_idx > 0:
        #     try:
        #         self._verify_state()
        #     except ValueError as e:
        #         raise ValueError(f"상태 검증 실패: {str(e)}")
    
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

    def _update_port_connections_optimized(self, dt: float) -> None:
        """
        최적화된 포트 연결 업데이트 - 변경 감지 기반 선택적 업데이트
        
        Args:
            dt (float): 시간 간격 [s]
        """
        # 1. 항상 업데이트해야 하는 기본 연결들
        self.port_manager.update_connections_by_type(self, PortType.HEAT)
        self.port_manager.update_connections_by_type(self, PortType.MASS)
        
        # 2. 스크린 상태가 변경된 경우만 스크린 관련 연결 업데이트
        current_screen_state = self.thScreen.SC
        if self._last_screen_state != current_screen_state:
            self._update_screen_related_connections()
            self._last_screen_state = current_screen_state
        
        # 3. 난방 상태가 변경된 경우만 파이프 연결 업데이트
        current_heating_state = self.PID_Mdot.CS
        if abs(current_heating_state - (self._last_heating_state or 0)) > 0.01:
            self.pipe_manager.update_pipe_connections(self)
            self._last_heating_state = current_heating_state
        
        # 4. CO2 및 복사 연결 (필요시에만)
        self.port_manager.update_connections_by_type(self, PortType.CO2)
        self.port_manager.update_connections_by_type(self, PortType.RADIATION)
        
        # 5. 특수 연결들 (기존 로직 유지)
        self._update_special_connections(dt)
        
        # 6. CO2 관련 연결 업데이트
        self._update_co2_connections()
    
    def _update_screen_related_connections(self):
        """스크린 관련 연결만 선택적으로 업데이트"""
        screen_connections = [
            ("Q_cnv_AirScr", "heatPort_b", "thScreen", "T"),
            ("Q_cnv_ScrTop", "heatPort_a", "thScreen", "T"),
            ("Q_rad_CanScr", "port_b", "thScreen", "T"),
            ("Q_rad_FlrScr", "port_b", "thScreen", "T"),
            ("Q_rad_ScrCov", "port_a", "thScreen", "T"),
        ]
        
        for source_comp, source_port, target_comp, target_attr in screen_connections:
            source = getattr(self, source_comp)
            target = getattr(self, target_comp)
            getattr(source, source_port).T = getattr(target, target_attr)
    
    def _update_special_connections(self, dt: float):
        """특수한 연결들 (기존 로직 유지)"""
        # RH 센서 연결
        self.RH_air_sensor.heatPort.T = self.air.T
        self.RH_air_sensor.massPort.VP = self.air.massPort.VP
        
        # 토양 전도 포트 연결
        self.Q_cd_Soil.port_a.T = self.floor.T
        self.Q_cd_Soil.T_soil_sp = self.T_soil7
        
        # 외부 수증기압 포트
        self.Q_ven_AirOut.MassPort_b.VP = self.VPout
        self.Q_ven_TopOut.MassPort_b.VP = self.VPout
        
        # CO2out 변환 및 포트 설정
        self.CO2out.CO2 = self.CO2out_ppm_to_mgm3
        self.CO2out.calculate()
        self.MC_AirOut.port_b.CO2 = self.CO2out.CO2
        self.MC_TopOut.port_b.CO2 = self.CO2out.CO2
        
        # 태양광 열원 연결
        self.air.R_Air_Glob = [
            self.solar_model.R_SunAir_Glob,
            self.illu.R_IluAir_Glob
        ]
        self.cover.R_SunCov_Glob = self.solar_model.R_SunCov_Glob
        self.floor.R_Flr_Glob = [
            self.solar_model.R_SunFlr_Glob,
            self.illu.R_IluFlr_Glob
        ]
        self.canopy.R_Can_Glob = [
            self.solar_model.R_SunCan_Glob,
            self.illu.R_IluCan_Glob
        ]
        
        # 난방 파이프 연결
        self._update_heating_pipe_connections(dt)
    
    def _update_heating_pipe_connections(self, dt: float):
        """난방 파이프 연결 업데이트"""
        # 1. PID 제어 → 소스 유량
        self.sourceMdot_1ry.in_Mdot = self.PID_Mdot.CS
        
        # 2. 소스 → 하부 파이프
        self.pipe_low.pipe_in.p = self.sourceMdot_1ry.flangeB.p
        self.pipe_low.pipe_in.m_flow = self.sourceMdot_1ry.flangeB.m_flow
        self.pipe_low.pipe_in.h_outflow = self.sourceMdot_1ry.flangeB.h_outflow
        
        # 3. 하부 파이프 → 상부 파이프
        self.pipe_up.pipe_in.p = self.pipe_low.pipe_out.p
        self.pipe_up.pipe_in.m_flow = self.pipe_low.pipe_out.m_flow
        self.pipe_up.pipe_in.h_outflow = self.pipe_low.pipe_out.h_outflow
        
        # 4. 상부 파이프 → 싱크
        self.sinkP_2ry.flangeB.p = self.pipe_up.pipe_out.p
        self.sinkP_2ry.flangeB.m_flow = self.pipe_up.pipe_out.m_flow
        self.sinkP_2ry.flangeB.h_outflow = self.pipe_up.pipe_out.h_outflow
        
        # 5. 파이프 대류 열전달 포트 연결
        for pipe, q_cnv in ((self.pipe_low, self.Q_cnv_LowAir),
                            (self.pipe_up,  self.Q_cnv_UpAir)):
            # 파이프 외피 온도 → 대류 포트
            for i, port in enumerate(q_cnv.heatPorts_a.ports):
                port.T = pipe.T

            # flow1DimInc 각 셀에 유량(M_dot)·유체온도 셋업
            m_dot_per_cell = abs(self.sourceMdot_1ry.flangeB.m_flow) / pipe.N
            for cell in pipe.flow1DimInc.Cells:
                cell.M_dot = m_dot_per_cell
                cell.heatTransfer.M_dot = m_dot_per_cell
                cell.heatTransfer.T_fluid = [self.sourceMdot_1ry.T_0]
                cell.heatTransfer.calculate()

            # 공기측 포트 온도
            q_cnv.port_b.T = self.air.T
    
    def _update_co2_connections(self):
        """CO2 관련 연결 업데이트"""
        # 내부 CO2 (two-port) 설정
        self.MC_AirOut.port_a.CO2 = self.CO2_air.CO2
        self.MC_AirTop.port_a.CO2 = self.CO2_air.CO2
        self.MC_AirTop.port_b.CO2 = self.CO2_top.CO2
        self.MC_TopOut.port_a.CO2 = self.CO2_top.CO2

        # MC_ExtAir (one-port) 포트 설정
        self.MC_ExtAir.port.CO2 = self.CO2_air.CO2

        # 작물흡수(MC_AirCan) one-port
        self.MC_AirCan.port.CO2 = self.CO2_air.CO2

        # MC_ventilation2 컴포넌트들: 환기율을 미리 설정하고 step() 호출
        self.MC_AirOut.f_vent = self.Q_ven_AirOut.f_vent_total
        self.MC_AirOut.step()      # 환기로 인한 CO2 배출 (하부공기 → 외부)
        
        self.MC_AirTop.f_vent = self.Q_ven_AirTop.f_AirTop
        self.MC_AirTop.step()      # 스크린 통과로 인한 CO2 이동 (하부공기 → 상부공기)
        
        self.MC_TopOut.f_vent = self.Q_ven_TopOut.f_vent_total
        self.MC_TopOut.step()      # 환기로 인한 CO2 배출 (상부공기 → 외부)
        
        # MC_AirCan: 작물 CO2 흡수 (대수 방정식)
        self.MC_AirCan.step()
        
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
    
    def get_connection_performance_stats(self) -> Dict[str, Any]:
        """포트 연결 성능 통계 반환"""
        return {
            'total_updates': self._connection_update_count,
            'total_time': self._connection_update_count,
            'average_time': self._total_connection_time / max(self._connection_update_count, 1),
            'last_screen_state': self._last_screen_state,
            'last_heating_state': self._last_heating_state
        }
    
    def reset_performance_stats(self):
        """성능 통계 초기화"""
        self._connection_update_count = 0
        self._total_connection_time = 0.0
            
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
        self.pipe_low.step(dt=self.dt)  # 추가
        self.pipe_up.step(dt=self.dt)

        # 하부 파이프 셀에 유량 분배
        for cell in self.pipe_low.flow1DimInc.Cells:
            cell.M_dot = abs(self.pipe_low.pipe_in.m_flow) / self.pipe_low.N
            cell.heatTransfer.M_dot = cell.M_dot

        # 상부 파이프 셀에 유량 분배
        for cell in self.pipe_up.flow1DimInc.Cells:
            cell.M_dot = abs(self.pipe_up.pipe_in.m_flow) / self.pipe_up.N
            cell.heatTransfer.M_dot = cell.M_dot

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
        self.SC.Tout = self.Tout  # 외부 온도
        
        # RH 센서 계산 및 연결 (Modelica 원본과 일치)
        self.RH_air_sensor.update()
        self.SC.RH_air = self.RH_air_sensor.RH  # 이미 0~1 범위
        
        # sc_usable이 리스트인지 스칼라인지 확인하여 안전하게 처리
        if isinstance(row['SC'], list):
            self.SC.SC_usable = row['SC'][1]     # 스크린 사용 가능 시간 (1번째 열이 실제 값)
        else:
            self.SC.SC_usable = row['SC']         # 스크린 사용 가능 시간 (스칼라 값)
        
        # self.SC.R_Glob_can = self.solar_model.R_t_Glob  # 작물 수준 전천일사량
        # Modelica 원본과 일치: 원시 일사량 사용 (I_glob.y)
        self.SC.R_Glob_can = self.I_glob  # 원시 일사량 [W/m²]
        
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
        
        # 5. 동적 공기층 높이 업데이트 (Modelica 원본과 일치)
        self._update_dynamic_air_height(current_sc)
        
        # 6. View Factor 업데이트 (순환 참조 해결)
        self._update_view_factors()
        
        # 7. 전체 복사 열전달 계수 업데이트 (스크린 관련 포함)
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
        self.U_vents.T_air_sp = row['T_air_sp'] + 273.15  # 설정 온도 (K)
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
        
        # 3. 단위 면적당 에너지 계산 (W_el_illu_instant 업데이트)
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
            'crop': self._get_crop_states(),
            'I_glob': self.I_glob,
            'I_crop': self.solar_model.R_SunCan_Glob + self.illu.R_IluCan_Glob.value  # 태양광+보광 [W/m²]
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
                'U_vents': self.U_vents.y,  # 환기 개도율 [0-1]
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

    def _update_dynamic_air_height(self, screen_closure: float) -> None:
        """
        스크린 상태에 따른 동적 공기층 높이 업데이트
        
        Args:
            screen_closure (float): 스크린 폐쇄율 [0-1]
        """
        # Modelica 원본: h_Air = 3.8 + (1 - SC.y) * 0.4
        h_air_base = 3.8  # 기본 공기층 높이 [m]
        h_air_screen_effect = 0.4  # 스크린 효과로 인한 높이 변화 [m]
        
        new_h_air = h_air_base + (1 - screen_closure) * h_air_screen_effect
        
        # 공기 컴포넌트의 높이 업데이트
        self.air.h_Air = new_h_air
        
        # CO2 저장 용량도 함께 업데이트 (Modelica 원본과 일치)
        self.CO2_air.cap_CO2 = new_h_air
            
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
        
        # 8. 스크린 관련 컴포넌트 연결 업데이트
        self.Q_cnv_ScrTop.MV_AirScr = self.Q_cnv_AirScr.MV_flow
        
        # 9. View Factor 업데이트 (순환 참조 해결)
        self._update_view_factors()
        
        # 10. 복사 열전달 계수 업데이트
        self._update_radiation_coefficients()
