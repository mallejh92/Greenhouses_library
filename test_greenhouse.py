#!/usr/bin/env python3
"""
Greenhouse_1 클래스 테스트 스크립트
기본 동작과 값 계산을 확인합니다.
"""

import numpy as np
from Greenhouse_1 import Greenhouse_1

def test_greenhouse_basic():
    """기본 온실 모델 테스트"""
    print("=== Greenhouse_1 기본 테스트 ===")
    
    # 온실 모델 생성
    greenhouse = Greenhouse_1()
    
    print(f"초기 온도:")
    print(f"  - 공기: {greenhouse.air.T - 273.15:.2f}°C")
    print(f"  - 외피: {greenhouse.cover.T - 273.15:.2f}°C")
    print(f"  - 작물: {greenhouse.canopy.T - 273.15:.2f}°C")
    print(f"  - 바닥: {greenhouse.floor.T - 273.15:.2f}°C")
    
    print(f"\n초기 습도:")
    print(f"  - 공기: {greenhouse.air.RH:.1f}%")
    print(f"  - 상부공기: {greenhouse.air_Top.RH:.1f}%")
    
    print(f"\n초기 CO2:")
    print(f"  - 공기: {greenhouse.CO2_air.CO2:.1f} mg/m³")
    
    print(f"\n초기 제어 상태:")
    print(f"  - 스크린: {greenhouse.thScreen.SC:.3f}")
    print(f"  - 환기: {greenhouse.U_vents.U_vents:.3f}")
    print(f"  - 조명: {greenhouse.illu.switch:.3f}")
    
    print(f"\n초기 작물 상태:")
    print(f"  - LAI: {greenhouse.TYM.LAI:.3f}")
    print(f"  - 건물중: {greenhouse.TYM.DM_Har:.1f} mg/m²")
    
    # 한 스텝 실행
    print(f"\n=== 첫 번째 스텝 실행 ===")
    try:
        greenhouse.step(3600.0, 0)  # 1시간 스텝
        
        # 상태 가져오기
        state = greenhouse._get_state()
        
        print(f"스텝 후 온도:")
        print(f"  - 공기: {state['temperatures']['air']:.2f}°C")
        print(f"  - 외부: {state['temperatures']['outdoor']:.2f}°C")
        print(f"  - 작물: {state['temperatures']['canopy']:.2f}°C")
        
        print(f"\n스텝 후 습도:")
        print(f"  - 공기: {state['humidity']['air_rh']:.1f}%")
        
        print(f"\n스텝 후 에너지:")
        print(f"  - 총 열량: {state['energy']['heating']['q_tot']:.1f} W/m²")
        print(f"  - 조명 전력: {state['energy']['electrical']['W_el_illu_instant']:.1f} W/m²")
        
        print(f"\n스텝 후 제어:")
        print(f"  - 스크린: {state['control']['screen']['SC']:.3f}")
        print(f"  - 환기: {state['control']['ventilation']['U_vents']:.3f}")
        
        print(f"\n스텝 후 작물:")
        print(f"  - LAI: {state['crop']['LAI']:.3f}")
        print(f"  - 건물중: {state['crop']['DM_Har']:.1f} mg/m²")
        
        print("\n✅ 테스트 성공!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_greenhouse_basic() 