from Interfaces.Heat.ThermalPort import ThermalPort
from Interfaces.Heat.HeatFluxInput import HeatFlux
import numpy as np

def test_basic_usage():
    """기본적인 ThermalPort 사용 예시"""
    # 기본 생성 (2개 노드)
    port1 = ThermalPort()
    print("\n1. 기본 생성 (2개 노드):")
    print(port1)

    # 여러 노드로 생성
    port2 = ThermalPort(N=5, T_start=300.0)
    print("\n2. 여러 노드 생성 (5개 노드, 300K):")
    print(port2)

def test_temperature_operations():
    """온도 관련 작업 테스트"""
    port = ThermalPort(N=3)
    
    # 온도 설정
    port.set_temperatures([293.15, 298.15, 303.15])
    print("\n3. 온도 설정 후:")
    print(port)
    
    # numpy 배열로 온도 설정
    temps = np.array([290.0, 295.0, 300.0])
    port.set_temperatures(temps)
    print("\n4. numpy 배열로 온도 설정 후:")
    print(port)

def test_heat_flux_operations():
    """열유속 관련 작업 테스트"""
    port = ThermalPort(N=2)
    
    # float 값으로 열유속 설정
    port.set_heat_fluxes([100.0, 200.0])
    print("\n5. float 값으로 열유속 설정 후:")
    print(port)
    
    # HeatFlux 객체로 열유속 설정
    port.set_heat_fluxes([HeatFlux(150.0), HeatFlux(250.0)])
    print("\n6. HeatFlux 객체로 열유속 설정 후:")
    print(port)

def test_connections():
    """커넥터 연결 테스트"""
    # 소스 포트 생성 및 설정
    source = ThermalPort(N=3)
    source.set_temperatures([293.15, 298.15, 303.15])
    source.set_heat_fluxes([100.0, 200.0, 300.0])
    print("\n7. 소스 포트 상태:")
    print(source)
    
    # 대상 포트 생성 및 연결
    target = ThermalPort(N=3)
    target.connect(source)
    print("\n8. 연결 후 대상 포트 상태:")
    print(target)

def test_error_handling():
    """에러 처리 테스트"""
    port = ThermalPort(N=2)
    
    try:
        # 잘못된 노드 수로 생성 시도
        ThermalPort(N=0)
    except ValueError as e:
        print("\n9. 잘못된 노드 수 에러:")
        print(f"Error: {e}")
    
    try:
        # 잘못된 길이의 온도 배열 설정 시도
        port.set_temperatures([293.15, 298.15, 303.15])
    except ValueError as e:
        print("\n10. 잘못된 배열 길이 에러:")
        print(f"Error: {e}")

if __name__ == "__main__":
    print("ThermalPort 테스트 시작\n")
    
    # 모든 테스트 실행
    test_basic_usage()
    test_temperature_operations()
    test_heat_flux_operations()
    test_connections()
    test_error_handling()
    
    print("\n테스트 완료!") 