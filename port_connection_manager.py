"""
포트 연결 관리 모듈
온실 시뮬레이션의 포트 연결을 자동화하는 관리자 클래스들
"""

from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class PortType(Enum):
    """포트 타입 열거형"""
    HEAT = "heat"
    MASS = "mass" 
    RADIATION = "radiation"
    FLUID = "fluid"
    CO2 = "co2"

@dataclass
class PortConnection:
    """포트 연결 정보를 담는 데이터 클래스"""
    source_component: str
    source_port: str
    target_component: str
    target_attribute: str
    port_type: PortType
    bidirectional: bool = False
    description: str = ""

class PortConnectionManager:
    """포트 연결을 자동화하는 관리자 클래스"""
    
    def __init__(self):
        self.connections = self._initialize_connections()
        
    def _initialize_connections(self) -> List[PortConnection]:
        """모든 포트 연결 정보를 정의"""
        return [
            # 열 포트 연결
            PortConnection("Q_cnv_AirScr", "heatPort_a", "air", "T", PortType.HEAT, description="Air to Screen convection heat port A"),
            PortConnection("Q_cnv_AirScr", "heatPort_b", "thScreen", "T", PortType.HEAT, description="Air to Screen convection heat port B"),
            PortConnection("Q_cnv_TopCov", "heatPort_a", "air_Top", "T", PortType.HEAT, description="Top Air to Cover convection heat port A"),
            PortConnection("Q_cnv_TopCov", "heatPort_b", "cover", "T", PortType.HEAT, description="Top Air to Cover convection heat port B"),
            PortConnection("Q_cnv_ScrTop", "heatPort_a", "thScreen", "T", PortType.HEAT, description="Screen to Top Air convection heat port A"),
            PortConnection("Q_cnv_ScrTop", "heatPort_b", "air_Top", "T", PortType.HEAT, description="Screen to Top Air convection heat port B"),
            PortConnection("Q_cnv_AirCov", "heatPort_a", "air", "T", PortType.HEAT, description="Air to Cover convection heat port A"),
            PortConnection("Q_cnv_AirCov", "heatPort_b", "cover", "T", PortType.HEAT, description="Air to Cover convection heat port B"),
            PortConnection("Q_cnv_FlrAir", "port_a", "floor", "T", PortType.HEAT, description="Floor to Air convection port A"),
            PortConnection("Q_cnv_FlrAir", "port_b", "air", "T", PortType.HEAT, description="Floor to Air convection port B"),
            PortConnection("Q_cnv_CanAir", "port_a", "canopy", "T", PortType.HEAT, description="Canopy to Air free convection port A"),
            PortConnection("Q_cnv_CanAir", "port_b", "air", "T", PortType.HEAT, description="Canopy to Air free convection port B"),
            PortConnection("Q_cnv_CovOut", "port_a", "cover", "T", PortType.HEAT, description="Cover to Outside convection port A"),
            PortConnection("Q_cnv_CovOut", "port_b", "Tout", "", PortType.HEAT, description="Cover to Outside convection port B"),
            
            # 토양 전도 포트 연결
            PortConnection("Q_cd_Soil", "port_a", "floor", "T", PortType.HEAT, description="Floor to Soil conduction port A"),
            
            # RH 센서 포트 연결
            PortConnection("RH_air_sensor", "heatPort", "air", "T", PortType.HEAT, description="RH sensor heat port"),
            PortConnection("RH_air_sensor", "massPort", "air", "massPort.VP", PortType.MASS, description="RH sensor mass port"),
            
            # 환기 열 포트 연결
            PortConnection("Q_ven_AirOut", "HeatPort_a", "air", "T", PortType.HEAT, description="Air ventilation heat port A"),
            PortConnection("Q_ven_AirOut", "HeatPort_b", "Tout", "", PortType.HEAT, description="Air ventilation heat port B"),
            PortConnection("Q_ven_TopOut", "HeatPort_a", "air_Top", "T", PortType.HEAT, description="Top Air ventilation heat port A"),
            PortConnection("Q_ven_TopOut", "HeatPort_b", "Tout", "", PortType.HEAT, description="Top Air ventilation heat port B"),
            PortConnection("Q_ven_AirTop", "HeatPort_a", "air", "T", PortType.HEAT, description="Air to Top Air heat port A"),
            PortConnection("Q_ven_AirTop", "HeatPort_b", "air_Top", "T", PortType.HEAT, description="Air to Top Air heat port B"),
            
            # 질량 포트 연결 (수증기압)
            PortConnection("Q_cnv_AirScr", "massPort_a", "air", "massPort.VP", PortType.MASS, description="Air to Screen mass port A"),
            PortConnection("Q_cnv_AirScr", "massPort_b", "thScreen", "massPort.VP", PortType.MASS, description="Air to Screen mass port B"),
            PortConnection("Q_cnv_TopCov", "massPort_a", "air_Top", "massPort.VP", PortType.MASS, description="Top Air to Cover mass port A"),
            PortConnection("Q_cnv_TopCov", "massPort_b", "cover", "massPort.VP", PortType.MASS, description="Top Air to Cover mass port B"),
            PortConnection("Q_cnv_ScrTop", "massPort_a", "thScreen", "massPort.VP", PortType.MASS, description="Screen to Top Air mass port A"),
            PortConnection("Q_cnv_ScrTop", "massPort_b", "air_Top", "massPort.VP", PortType.MASS, description="Screen to Top Air mass port B"),
            PortConnection("Q_cnv_AirCov", "massPort_a", "air", "massPort.VP", PortType.MASS, description="Air to Cover mass port A"),
            PortConnection("Q_cnv_AirCov", "massPort_b", "cover", "massPort.VP", PortType.MASS, description="Air to Cover mass port B"),
            PortConnection("MV_CanAir", "port_a", "canopy", "massPort.VP", PortType.MASS, description="Canopy transpiration port A"),
            PortConnection("MV_CanAir", "port_b", "air", "massPort.VP", PortType.MASS, description="Canopy transpiration port B"),
            
            # 환기 질량 포트 연결
            PortConnection("Q_ven_AirOut", "MassPort_a", "air", "massPort.VP", PortType.MASS, description="Air ventilation mass port A"),
            PortConnection("Q_ven_AirOut", "MassPort_b", "VPout", "", PortType.MASS, description="Air ventilation mass port B"),
            PortConnection("Q_ven_TopOut", "MassPort_a", "air_Top", "massPort.VP", PortType.MASS, description="Top Air ventilation mass port A"),
            PortConnection("Q_ven_TopOut", "MassPort_b", "VPout", "", PortType.MASS, description="Top Air ventilation mass port B"),
            PortConnection("Q_ven_AirTop", "MassPort_a", "air", "massPort.VP", PortType.MASS, description="Air to Top Air mass port A"),
            PortConnection("Q_ven_AirTop", "MassPort_b", "air_Top", "massPort.VP", PortType.MASS, description="Air to Top Air mass port B"),
            
            # 복사 포트 연결
            PortConnection("Q_rad_CanCov", "port_a", "canopy", "T", PortType.RADIATION, description="Canopy to Cover radiation port A"),
            PortConnection("Q_rad_CanCov", "port_b", "cover", "T", PortType.RADIATION, description="Canopy to Cover radiation port B"),
            PortConnection("Q_rad_CanScr", "port_a", "canopy", "T", PortType.RADIATION, description="Canopy to Screen radiation port A"),
            PortConnection("Q_rad_CanScr", "port_b", "thScreen", "T", PortType.RADIATION, description="Canopy to Screen radiation port B"),
            PortConnection("Q_rad_CovSky", "port_a", "cover", "T", PortType.RADIATION, description="Cover to Sky radiation port A"),
            PortConnection("Q_rad_CovSky", "port_b", "Tsky", "", PortType.RADIATION, description="Cover to Sky radiation port B"),
            PortConnection("Q_rad_FlrCan", "port_a", "floor", "T", PortType.RADIATION, description="Floor to Canopy radiation port A"),
            PortConnection("Q_rad_FlrCan", "port_b", "canopy", "T", PortType.RADIATION, description="Floor to Canopy radiation port B"),
            PortConnection("Q_rad_FlrCov", "port_a", "floor", "T", PortType.RADIATION, description="Floor to Cover radiation port A"),
            PortConnection("Q_rad_FlrCov", "port_b", "cover", "T", PortType.RADIATION, description="Floor to Cover radiation port B"),
            PortConnection("Q_rad_FlrScr", "port_a", "floor", "T", PortType.RADIATION, description="Floor to Screen radiation port A"),
            PortConnection("Q_rad_FlrScr", "port_b", "thScreen", "T", PortType.RADIATION, description="Floor to Screen radiation port B"),
            PortConnection("Q_rad_ScrCov", "port_a", "thScreen", "T", PortType.RADIATION, description="Screen to Cover radiation port A"),
            PortConnection("Q_rad_ScrCov", "port_b", "cover", "T", PortType.RADIATION, description="Screen to Cover radiation port B"),
            
            # CO2 포트 연결
            PortConnection("MC_AirOut", "port_a", "CO2_air", "CO2", PortType.CO2, description="Air CO2 to outside port A"),
            PortConnection("MC_AirOut", "port_b", "CO2out", "CO2", PortType.CO2, description="Air CO2 to outside port B"),
            PortConnection("MC_AirTop", "port_a", "CO2_air", "CO2", PortType.CO2, description="Air CO2 to top port A"),
            PortConnection("MC_AirTop", "port_b", "CO2_top", "CO2", PortType.CO2, description="Air CO2 to top port B"),
            PortConnection("MC_TopOut", "port_a", "CO2_top", "CO2", PortType.CO2, description="Top CO2 to outside port A"),
            PortConnection("MC_TopOut", "port_b", "CO2out", "CO2", PortType.CO2, description="Top CO2 to outside port B"),
            PortConnection("MC_AirCan", "port", "CO2_air", "CO2", PortType.CO2, description="Air CO2 to canopy port"),
            PortConnection("MC_ExtAir", "port", "CO2_air", "CO2", PortType.CO2, description="External CO2 to air port"),
        ]
    
    def update_all_connections(self, greenhouse_instance):
        """모든 포트 연결을 자동으로 업데이트"""
        for connection in self.connections:
            self._update_single_connection(greenhouse_instance, connection)
    
    def update_connections_by_type(self, greenhouse_instance, port_type: PortType):
        """특정 타입의 포트 연결만 업데이트"""
        filtered_connections = [c for c in self.connections if c.port_type == port_type]
        for connection in filtered_connections:
            self._update_single_connection(greenhouse_instance, connection)
    
    def _update_single_connection(self, greenhouse_instance, connection: PortConnection):
        """단일 포트 연결을 업데이트"""
        try:
            # 소스 컴포넌트와 포트 가져오기
            source_component = getattr(greenhouse_instance, connection.source_component)
            source_port = self._get_nested_attribute(source_component, connection.source_port)
            
            # 타겟 값 가져오기
            if connection.target_attribute == "":
                # 외부 변수인 경우 (Tout, Tsky, VPout 등)
                target_value = getattr(greenhouse_instance, connection.target_component)
            else:
                target_component = getattr(greenhouse_instance, connection.target_component)
                target_value = self._get_nested_attribute(target_component, connection.target_attribute)
            
            # 포트 연결 실행
            if connection.port_type == PortType.HEAT:
                source_port.T = target_value
            elif connection.port_type == PortType.MASS:
                source_port.VP = target_value
            elif connection.port_type == PortType.RADIATION:
                source_port.T = target_value
            elif connection.port_type == PortType.CO2:
                source_port.CO2 = target_value
                
        except Exception as e:
            print(f"포트 연결 실패: {connection.source_component}.{connection.source_port} -> {connection.target_component}.{connection.target_attribute}")
            print(f"오류: {e}")
            # 오류가 발생해도 시뮬레이션을 계속 진행
            pass
    
    def _get_nested_attribute(self, obj, attr_path: str):
        """중첩된 속성에 접근 (예: massPort.VP)"""
        if not attr_path:
            return obj
        
        attributes = attr_path.split('.')
        current_obj = obj
        for attr in attributes:
            current_obj = getattr(current_obj, attr)
        return current_obj

class PipeConnectionManager:
    """난방 파이프 관련 연결을 관리하는 특화된 클래스"""
    
    def __init__(self):
        self.pipe_radiation_connections = self._initialize_pipe_radiation()
        self.pipe_convection_connections = self._initialize_pipe_convection()
    
    def _initialize_pipe_radiation(self):
        """파이프 복사 연결 정보"""
        return [
            # 하부 파이프 복사
            ("Q_rad_LowFlr", "heatPorts_a", "pipe_low", "T", "ports"),
            ("Q_rad_LowFlr", "port_b", "floor", "T", "single"),
            ("Q_rad_LowCan", "heatPorts_a", "pipe_low", "T", "ports"),
            ("Q_rad_LowCan", "port_b", "canopy", "T", "single"),
            ("Q_rad_LowCov", "heatPorts_a", "pipe_low", "T", "ports"),
            ("Q_rad_LowCov", "port_b", "cover", "T", "single"),
            ("Q_rad_LowScr", "heatPorts_a", "pipe_low", "T", "ports"),
            ("Q_rad_LowScr", "port_b", "thScreen", "T", "single"),
            
            # 상부 파이프 복사
            ("Q_rad_UpFlr", "heatPorts_a", "pipe_up", "T", "ports"),
            ("Q_rad_UpFlr", "port_b", "floor", "T", "single"),
            ("Q_rad_UpCan", "heatPorts_a", "pipe_up", "T", "ports"),
            ("Q_rad_UpCan", "port_b", "canopy", "T", "single"),
            ("Q_rad_UpCov", "heatPorts_a", "pipe_up", "T", "ports"),
            ("Q_rad_UpCov", "port_b", "cover", "T", "single"),
            ("Q_rad_UpScr", "heatPorts_a", "pipe_up", "T", "ports"),
            ("Q_rad_UpScr", "port_b", "thScreen", "T", "single"),
        ]
    
    def _initialize_pipe_convection(self):
        """파이프 대류 연결 정보"""
        return [
            ("Q_cnv_LowAir", "heatPorts_a", "pipe_low", "T", "ports"),
            ("Q_cnv_LowAir", "port_b", "air", "T", "single"),
            ("Q_cnv_UpAir", "heatPorts_a", "pipe_up", "T", "ports"),
            ("Q_cnv_UpAir", "port_b", "air", "T", "single"),
        ]
    
    def update_pipe_connections(self, greenhouse_instance):
        """모든 파이프 연결 업데이트"""
        self._update_pipe_radiation(greenhouse_instance)
        self._update_pipe_convection(greenhouse_instance)
    
    def _update_pipe_radiation(self, greenhouse_instance):
        """파이프 복사 연결 업데이트"""
        for connection in self.pipe_radiation_connections:
            self._update_pipe_connection(greenhouse_instance, connection)
    
    def _update_pipe_convection(self, greenhouse_instance):
        """파이프 대류 연결 업데이트"""
        for connection in self.pipe_convection_connections:
            self._update_pipe_connection(greenhouse_instance, connection)
    
    def _update_pipe_connection(self, greenhouse_instance, connection):
        """단일 파이프 연결 업데이트"""
        try:
            source_comp, source_port, target_comp, target_attr, connection_type = connection
            
            source_component = getattr(greenhouse_instance, source_comp)
            target_component = getattr(greenhouse_instance, target_comp)
            target_value = getattr(target_component, target_attr)
            
            if connection_type == "ports":
                # 여러 포트에 동일한 값 설정
                ports_obj = getattr(source_component, source_port)
                # ports가 리스트인지 객체인지 확인
                if hasattr(ports_obj, 'ports'):
                    # ports 객체인 경우
                    for port in ports_obj.ports:
                        port.T = target_value
                elif isinstance(ports_obj, list):
                    # ports가 리스트인 경우
                    for port in ports_obj:
                        port.T = target_value
                else:
                    # 단일 포트 객체인 경우
                    ports_obj.T = target_value
            else:
                # 단일 포트 설정
                source_port_obj = getattr(source_component, source_port)
                source_port_obj.T = target_value
        except Exception as e:
            print(f"파이프 연결 업데이트 실패: {source_comp}.{source_port} -> {target_comp}.{target_attr}")
            print(f"오류: {e}")
            # 오류가 발생해도 시뮬레이션을 계속 진행
            pass 