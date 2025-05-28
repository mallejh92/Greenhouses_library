import numpy as np
from Flows.HeatTransfer.FreeConvection import FreeConvection

def test_free_convection():
    """
    FreeConvection 클래스의 동작을 테스트하는 함수
    """
    # 테스트 파라미터
    A = 1.0  # 면적 [m²]
    phi = 0.0  # 경사각 [rad]
    
    print("\n=== FreeConvection 테스트 시작 ===")
    
    # 1. 일반 열전달 테스트 (floor=False)
    print("\n1. 일반 열전달 테스트 (floor=False)")
    conv = FreeConvection(phi=phi, A=A, floor=False)
    
    # 테스트 케이스들
    test_cases = [
        {"T_a": 293.15, "T_b": 283.15, "desc": "10K 차이"},
        {"T_a": 303.15, "T_b": 293.15, "desc": "10K 차이 (더 높은 온도)"},
        {"T_a": 293.15, "T_b": 293.15, "desc": "동일 온도"},
        {"T_a": 283.15, "T_b": 293.15, "desc": "역방향 10K 차이"}
    ]
    
    for case in test_cases:
        # 포트 온도 설정
        conv.heatPort_a.T = case["T_a"]
        conv.heatPort_b.T = case["T_b"]
        
        # 열전달 계산
        conv.step(dt=1.0)
        
        print(f"\n케이스: {case['desc']}")
        print(f"T_a: {case['T_a']-273.15:.1f}°C, T_b: {case['T_b']-273.15:.1f}°C")
        print(f"dT: {conv.dT:.1f}K")
        print(f"HEC_ab: {conv.HEC_ab:.3f} W/(m²·K)")
        print(f"Q_flow: {conv.Q_flow:.1f} W")
    
    # 2. 지면 열전달 테스트 (floor=True)
    print("\n2. 지면 열전달 테스트 (floor=True)")
    conv_floor = FreeConvection(phi=phi, A=A, floor=True)
    
    for case in test_cases:
        # 포트 온도 설정
        conv_floor.heatPort_a.T = case["T_a"]
        conv_floor.heatPort_b.T = case["T_b"]
        
        # 열전달 계산
        conv_floor.step(dt=1.0)
        
        print(f"\n케이스: {case['desc']}")
        print(f"T_a: {case['T_a']-273.15:.1f}°C, T_b: {case['T_b']-273.15:.1f}°C")
        print(f"dT: {conv_floor.dT:.1f}K")
        print(f"HEC_up_flr: {conv_floor.HEC_up_flr:.3f} W/(m²·K)")
        print(f"HEC_down_flr: {conv_floor.HEC_down_flr:.3f} W/(m²·K)")
        print(f"HEC_ab: {conv_floor.HEC_ab:.3f} W/(m²·K)")
        print(f"Q_flow: {conv_floor.Q_flow:.1f} W")
    
    # 3. 경사각에 따른 테스트
    print("\n3. 경사각에 따른 테스트")
    angles = [0.0, np.pi/6, np.pi/4, np.pi/3]  # 0°, 30°, 45°, 60°
    
    for angle in angles:
        conv_angle = FreeConvection(phi=angle, A=A, floor=False)
        conv_angle.heatPort_a.T = 293.15
        conv_angle.heatPort_b.T = 283.15
        
        conv_angle.step(dt=1.0)
        
        print(f"\n경사각: {angle*180/np.pi:.1f}°")
        print(f"HEC_ab: {conv_angle.HEC_ab:.3f} W/(m²·K)")
        print(f"Q_flow: {conv_angle.Q_flow:.1f} W")
    
    # 4. 온도 차이 제한 테스트
    print("\n4. 온도 차이 제한 테스트")
    conv_limit = FreeConvection(phi=phi, A=A, floor=False)
    
    extreme_cases = [
        {"T_a": 373.15, "T_b": 273.15, "desc": "100K 차이"},
        {"T_a": 473.15, "T_b": 273.15, "desc": "200K 차이"},
        {"T_a": 273.15, "T_b": 373.15, "desc": "-100K 차이"}
    ]
    
    for case in extreme_cases:
        conv_limit.heatPort_a.T = case["T_a"]
        conv_limit.heatPort_b.T = case["T_b"]
        
        conv_limit.step(dt=1.0)
        
        print(f"\n케이스: {case['desc']}")
        print(f"T_a: {case['T_a']-273.15:.1f}°C, T_b: {case['T_b']-273.15:.1f}°C")
        print(f"dT: {conv_limit.dT:.1f}K")
        print(f"HEC_ab: {conv_limit.HEC_ab:.3f} W/(m²·K)")
        print(f"Q_flow: {conv_limit.Q_flow:.1f} W")

if __name__ == "__main__":
    test_free_convection()