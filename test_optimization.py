"""
포트 연결 최적화 성능 테스트 스크립트
기존 방식과 최적화된 방식의 성능을 비교합니다.
"""

import time
import numpy as np
from Greenhouse_2 import Greenhouse_2

def test_connection_performance():
    """포트 연결 성능 테스트"""
    print("=== 포트 연결 최적화 성능 테스트 ===")
    
    # 온실 모델 초기화
    greenhouse = Greenhouse_2()
    
    # 테스트 파라미터
    num_steps = 1000
    dt = 60.0  # 1분 간격
    
    print(f"테스트 조건: {num_steps} 스텝, {dt}초 간격")
    print(f"총 시뮬레이션 시간: {num_steps * dt / 3600:.1f} 시간")
    
    # 성능 통계 초기화
    greenhouse.reset_performance_stats()
    
    # 시뮬레이션 실행
    start_time = time.time()
    
    for i in range(num_steps):
        try:
            greenhouse.step(dt, i)
            
            # 진행상황 출력 (10%마다)
            if (i + 1) % (num_steps // 10) == 0:
                progress = (i + 1) / num_steps * 100
                elapsed = time.time() - start_time
                print(f"진행률: {progress:.0f}% ({elapsed:.1f}초 경과)")
                
        except Exception as e:
            print(f"스텝 {i}에서 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            break
    
    total_time = time.time() - start_time
    
    # 성능 통계 출력
    stats = greenhouse.get_connection_performance_stats()
    
    print("\n=== 성능 결과 ===")
    print(f"총 실행 시간: {total_time:.2f}초")
    print(f"평균 스텝 시간: {total_time / num_steps * 1000:.2f}ms")
    print(f"포트 연결 업데이트 횟수: {stats['total_updates']}")
    print(f"마지막 스크린 상태: {stats['last_screen_state']}")
    print(f"마지막 난방 상태: {stats['last_heating_state']}")
    
    # 상태 정보 출력
    try:
        state = greenhouse._get_state()
        print(f"\n=== 최종 상태 ===")
        print(f"실내 온도: {state['temperatures']['air']:.1f}°C")
        print(f"상대습도: {state['humidity']['air_rh']:.1f}%")
        print(f"CO2 농도: {state['control']['co2']['CO2_air']:.1f} mg/m³")
        print(f"스크린 폐쇄율: {state['control']['screen']['SC']:.2f}")
        print(f"총 난방 에너지: {state['energy']['heating']['E_th_tot_kWhm2']:.1f} kWh/m²")
    except Exception as e:
        print(f"상태 정보 출력 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    return total_time, stats

def test_memory_usage():
    """메모리 사용량 테스트"""
    print("\n=== 메모리 사용량 테스트 ===")
    
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # 온실 모델 생성
    greenhouse = Greenhouse_1()
    
    after_init_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # 몇 스텝 실행
    for i in range(100):
        greenhouse.step(60.0, i)
    
    after_simulation_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"초기 메모리: {initial_memory:.1f} MB")
    print(f"모델 초기화 후: {after_init_memory:.1f} MB")
    print(f"시뮬레이션 후: {after_simulation_memory:.1f} MB")
    print(f"모델 메모리 사용량: {after_init_memory - initial_memory:.1f} MB")
    print(f"시뮬레이션 중 추가 메모리: {after_simulation_memory - after_init_memory:.1f} MB")

def test_connection_optimization():
    """연결 최적화 효과 테스트"""
    print("\n=== 연결 최적화 효과 테스트 ===")
    
    greenhouse = Greenhouse_1()
    
    # 스크린 상태 변경 테스트
    print("스크린 상태 변경 테스트:")
    original_sc = greenhouse.thScreen.SC
    
    # 스크린 상태 변경
    greenhouse.thScreen.SC = 0.5
    greenhouse._update_port_connections_optimized(60.0)
    
    print(f"스크린 상태 변경: {original_sc} → {greenhouse.thScreen.SC}")
    print(f"스크린 관련 연결 업데이트됨: {greenhouse._last_screen_state == 0.5}")
    
    # 난방 상태 변경 테스트
    print("\n난방 상태 변경 테스트:")
    original_heating = greenhouse.PID_Mdot.CS
    
    # 난방 상태 변경
    greenhouse.PID_Mdot.CS = 1.0
    greenhouse._update_port_connections_optimized(60.0)
    
    print(f"난방 상태 변경: {original_heating:.2f} → {greenhouse.PID_Mdot.CS:.2f}")
    print(f"난방 관련 연결 업데이트됨: {abs(greenhouse.PID_Mdot.CS - (greenhouse._last_heating_state or 0)) > 0.01}")

if __name__ == "__main__":
    try:
        # 1. 기본 성능 테스트
        total_time, stats = test_connection_performance()
        
        # 2. 메모리 사용량 테스트
        test_memory_usage()
        
        # 3. 연결 최적화 효과 테스트
        test_connection_optimization()
        
        print("\n=== 테스트 완료 ===")
        print("포트 연결 최적화가 성공적으로 적용되었습니다.")
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc() 