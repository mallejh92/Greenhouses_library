#!/usr/bin/env python3
"""
Greenhouse_1 간단 테스트
기본 동작과 값 계산을 확인합니다.
"""

from Greenhouse_1 import Greenhouse_1

def main():
    print("Greenhouse_1 간단 테스트 시작...")
    
    try:
        # 온실 모델 생성 (초기화 출력 포함)
        greenhouse = Greenhouse_1()
        
        # 첫 번째 스텝 실행
        print("\n첫 번째 스텝 실행 중...")
        greenhouse.step(3600.0, 0)  # 1시간 스텝
        
        # 상태 가져오기
        state = greenhouse._get_state()
        
        print(f"\n=== 시뮬레이션 결과 ===")
        print(f"온도:")
        print(f"  - 공기: {state['temperatures']['air']:.2f}°C")
        print(f"  - 외부: {state['temperatures']['outdoor']:.2f}°C")
        print(f"  - 작물: {state['temperatures']['canopy']:.2f}°C")
        
        print(f"\n습도: {state['humidity']['air_rh']:.1f}%")
        print(f"CO2: {state['control']['co2']['CO2_air']:.1f} mg/m³")
        
        print(f"\n에너지:")
        print(f"  - 총 열량: {state['energy']['heating']['q_tot']:.1f} W/m²")
        print(f"  - 조명 전력: {state['energy']['electrical']['W_el_illu_instant']:.1f} W/m²")
        
        print(f"\n제어:")
        print(f"  - 스크린: {state['control']['screen']['SC']:.3f}")
        print(f"  - 환기: {state['control']['ventilation']['U_vents']:.3f}")
        print(f"  - 조명: {state['control']['illumination']['switch']:.3f}")
        
        print(f"\n작물:")
        print(f"  - LAI: {state['crop']['LAI']:.3f}")
        print(f"  - 건물중: {state['crop']['DM_Har']:.1f} mg/m²")
        
        print("\n✅ 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 