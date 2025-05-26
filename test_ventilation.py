import numpy as np
from Flows.HeatAndVapourTransfer.Ventilation import Ventilation

def test_ventilation():
    # 테스트 파라미터 설정
    A = 1000.0  # 온실 바닥 면적 [m²]
    
    # 메인 공기 구역용 환기 모델 초기화
    vent_main = Ventilation(
        A=A,
        thermalScreen=True,
        topAir=False
    )
    
    # 상부 공기 구역용 환기 모델 초기화
    vent_top = Ventilation(
        A=A,
        thermalScreen=True,
        topAir=True
    )
    
    # 테스트 조건 설정
    SC = 0.0  # 스크린 개방
    u = 2.0   # 풍속 [m/s]
    U_vents = 0.5  # 환기창 개도 (0-1)
    
    # 포트 온도 및 수증기압 설정
    T_a = 293.15  # 내부 온도 [K] (20°C)
    T_b = 283.15  # 외부 온도 [K] (10°C)
    VP_a = 2000   # 내부 수증기압 [Pa]
    VP_b = 1000   # 외부 수증기압 [Pa]
    
    # 메인 구역 환기 계산
    Q_flow_main, MV_flow_main = vent_main.update(
        SC=SC,
        u=u,
        U_vents=U_vents,
        T_a=T_a,
        T_b=T_b,
        VP_a=VP_a,
        VP_b=VP_b
    )
    
    # 상부 구역 환기 계산
    Q_flow_top, MV_flow_top = vent_top.update(
        SC=SC,
        u=u,
        U_vents=U_vents,
        T_a=T_a,
        T_b=T_b,
        VP_a=VP_a,
        VP_b=VP_b
    )
    
    # 결과 출력
    print("\n=== 환기 모델 테스트 결과 ===")
    print("\n[메인 공기 구역]")
    print(f"환기율 (f_vent): {vent_main.f_vent:.6f} m³/(m²·s)")
    print(f"총 환기율 (f_vent_total): {vent_main.f_vent_total:.6f} m³/(m²·s)")
    print(f"열유속 (Q_flow): {Q_flow_main:.2f} W")
    print(f"수증기 유량 (MV_flow): {MV_flow_main:.6f} kg/s")
    
    print("\n[상부 공기 구역]")
    print(f"환기율 (f_vent): {vent_top.f_vent:.6f} m³/(m²·s)")
    print(f"총 환기율 (f_vent_total): {vent_top.f_vent_total:.6f} m³/(m²·s)")
    print(f"열유속 (Q_flow): {Q_flow_top:.2f} W")
    print(f"수증기 유량 (MV_flow): {MV_flow_top:.6f} kg/s")
    
    # 기계 환기 테스트
    print("\n[기계 환기 테스트]")
    vent_forced = Ventilation(
        A=A,
        thermalScreen=True,
        topAir=False,
        forcedVentilation=True,
        phi_VentForced=1.0  # 1 m³/s 용량
    )
    
    Q_flow_forced, MV_flow_forced = vent_forced.update(
        SC=SC,
        u=u,
        U_vents=U_vents,
        T_a=T_a,
        T_b=T_b,
        VP_a=VP_a,
        VP_b=VP_b,
        U_VentForced=0.5  # 50% 개도
    )
    
    print(f"기계 환기율 (f_ventForced): {vent_forced.f_ventForced:.6f} m³/(m²·s)")
    print(f"총 환기율 (f_vent_total): {vent_forced.f_vent_total:.6f} m³/(m²·s)")
    print(f"열유속 (Q_flow): {Q_flow_forced:.2f} W")
    print(f"수증기 유량 (MV_flow): {MV_flow_forced:.6f} kg/s")

if __name__ == "__main__":
    test_ventilation() 