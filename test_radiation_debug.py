#!/usr/bin/env python3
"""
복사 열전달 계산 디버깅 테스트
"""

import numpy as np
from Flows.HeatTransfer.Radiation_T4 import Radiation_T4

def test_radiation_calculation():
    """복사 열전달 계산을 테스트합니다."""
    
    # 온실 면적
    A = 1.4e4  # 14,000 m²
    
    # 온도 설정 (Kelvin)
    T_canopy = 293.15    # 20°C
    T_screen = 298.15    # 25°C
    T_pipe_low = 353.15  # 80°C
    T_pipe_up = 343.15   # 70°C
    T_floor = 288.15     # 15°C
    T_cover = 283.15     # 10°C
    
    print("=== 복사 열전달 계산 테스트 ===")
    print(f"면적: {A:.0f} m²")
    print(f"온도:")
    print(f"  작물: {T_canopy-273.15:.1f}°C")
    print(f"  스크린: {T_screen-273.15:.1f}°C")
    print(f"  하부파이프: {T_pipe_low-273.15:.1f}°C")
    print(f"  상부파이프: {T_pipe_up-273.15:.1f}°C")
    print(f"  바닥: {T_floor-273.15:.1f}°C")
    print(f"  외피: {T_cover-273.15:.1f}°C")
    
    # 1. 작물 → 스크린 복사 테스트
    print(f"\n1. 작물 → 스크린 복사:")
    Q_rad_CanScr = Radiation_T4(
        A=A,
        epsilon_a=1.0,    # 작물 방사율
        epsilon_b=1.0,    # 스크린 방사율
        FFa=0.5,          # 작물 View Factor
        FFb=1.0           # 스크린 View Factor
    )
    
    # 포트 온도 설정
    Q_rad_CanScr.port_a.T = T_canopy
    Q_rad_CanScr.port_b.T = T_screen
    
    # 복사 열전달 계산
    Q_flow = Q_rad_CanScr.step()
    print(f"  Q_flow: {Q_flow:.1f} W")
    print(f"  단위면적당: {Q_flow/A:.1f} W/m²")
    
    # 2. 하부파이프 → 스크린 복사 테스트
    print(f"\n2. 하부파이프 → 스크린 복사:")
    Q_rad_LowScr = Radiation_T4(
        A=A,
        epsilon_a=0.88,   # 파이프 방사율
        epsilon_b=1.0,    # 스크린 방사율
        FFa=0.1,          # 파이프 View Factor (작음)
        FFb=1.0           # 스크린 View Factor
    )
    
    # 포트 온도 설정
    Q_rad_LowScr.port_a.T = T_pipe_low
    Q_rad_LowScr.port_b.T = T_screen
    
    # 복사 열전달 계산
    Q_flow = Q_rad_LowScr.step()
    print(f"  Q_flow: {Q_flow:.1f} W")
    print(f"  단위면적당: {Q_flow/A:.1f} W/m²")
    
    # 3. 상부파이프 → 스크린 복사 테스트
    print(f"\n3. 상부파이프 → 스크린 복사:")
    Q_rad_UpScr = Radiation_T4(
        A=A,
        epsilon_a=0.88,   # 파이프 방사율
        epsilon_b=1.0,    # 스크린 방사율
        FFa=0.05,         # 파이프 View Factor (더 작음)
        FFb=1.0           # 스크린 View Factor
    )
    
    # 포트 온도 설정
    Q_rad_UpScr.port_a.T = T_pipe_up
    Q_rad_UpScr.port_b.T = T_screen
    
    # 복사 열전달 계산
    Q_flow = Q_rad_UpScr.step()
    print(f"  Q_flow: {Q_flow:.1f} W")
    print(f"  단위면적당: {Q_flow/A:.1f} W/m²")
    
    # 4. 바닥 → 스크린 복사 테스트
    print(f"\n4. 바닥 → 스크린 복사:")
    Q_rad_FlrScr = Radiation_T4(
        A=A,
        epsilon_a=0.89,   # 바닥 방사율
        epsilon_b=1.0,    # 스크린 방사율
        FFa=1.0,          # 바닥 View Factor
        FFb=1.0           # 스크린 View Factor
    )
    
    # 포트 온도 설정
    Q_rad_FlrScr.port_a.T = T_floor
    Q_rad_FlrScr.port_b.T = T_screen
    
    # 복사 열전달 계산
    Q_flow = Q_rad_FlrScr.step()
    print(f"  Q_flow: {Q_flow:.1f} W")
    print(f"  단위면적당: {Q_flow/A:.1f} W/m²")
    
    # 5. 스크린 → 외피 복사 테스트
    print(f"\n5. 스크린 → 외피 복사:")
    Q_rad_ScrCov = Radiation_T4(
        A=A,
        epsilon_a=1.0,    # 스크린 방사율
        epsilon_b=0.84,   # 외피 방사율
        FFa=1.0,          # 스크린 View Factor
        FFb=1.0           # 외피 View Factor
    )
    
    # 포트 온도 설정
    Q_rad_ScrCov.port_a.T = T_screen
    Q_rad_ScrCov.port_b.T = T_cover
    
    # 복사 열전달 계산
    Q_flow = Q_rad_ScrCov.step()
    print(f"  Q_flow: {Q_flow:.1f} W")
    print(f"  단위면적당: {Q_flow/A:.1f} W/m²")
    
    # 6. 총 스크린 열 균형 계산
    print(f"\n6. 스크린 열 균형:")
    Q_rad_CanScr.step()  # 다시 계산
    Q_rad_LowScr.step()  # 다시 계산
    Q_rad_UpScr.step()   # 다시 계산
    Q_rad_FlrScr.step()  # 다시 계산
    Q_rad_ScrCov.step()  # 다시 계산
    
    # 스크린으로 들어오는 열 (양수)
    Q_in = Q_rad_CanScr.Q_flow + Q_rad_LowScr.Q_flow + Q_rad_UpScr.Q_flow + Q_rad_FlrScr.Q_flow
    
    # 스크린에서 나가는 열 (음수)
    Q_out = Q_rad_ScrCov.Q_flow
    
    # 스크린 열 균형
    Q_balance = Q_in - Q_out
    
    print(f"  들어오는 열: {Q_in:.1f} W")
    print(f"  나가는 열: {Q_out:.1f} W")
    print(f"  열 균형: {Q_balance:.1f} W")
    print(f"  단위면적당: {Q_balance/A:.1f} W/m²")
    
    # 7. 물리적 한계 확인
    print(f"\n7. 물리적 한계 확인:")
    max_Q_per_m2 = 100.0  # W/m²
    max_Q_total = max_Q_per_m2 * A
    print(f"  최대 허용 열유속: {max_Q_total:.1f} W ({max_Q_per_m2} W/m²)")
    print(f"  현재 열유속: {Q_balance:.1f} W ({Q_balance/A:.1f} W/m²)")
    
    if abs(Q_balance) > max_Q_total:
        print(f"  ⚠️  경고: 열유속이 물리적 한계를 초과했습니다!")
    else:
        print(f"  ✅ 열유속이 물리적 한계 내에 있습니다.")

if __name__ == "__main__":
    test_radiation_calculation() 