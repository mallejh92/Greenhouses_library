"""
개선된 Control_ThScreen 테스트
Modelica 원본과 동일한 StateGraph 논리 구현 검증
"""

import numpy as np
import matplotlib.pyplot as plt
from ControlSystems.Climate.Control_ThScreen import Control_ThScreen

def test_improved_screen_control():
    """개선된 스크린 제어 로직 테스트"""
    print("=== 개선된 Control_ThScreen 테스트 ===")
    
    # 스크린 제어기 초기화
    sc = Control_ThScreen(R_Glob_can_min=35)
    
    # 테스트 시나리오 설정
    dt = 60  # 1분 간격
    total_time = 24 * 3600  # 24시간
    time_steps = int(total_time / dt)
    
    # 시간 배열
    time_array = np.linspace(0, total_time, time_steps)
    
    # 결과 저장 배열
    sc_values = []
    states = []
    timers = []
    
    print("\n시뮬레이션 시작...")
    
    for i, t in enumerate(time_array):
        # 시간에 따른 입력값 변화 (실제 데이터와 유사하게)
        hour = t / 3600
        
        # 일사량: 낮에는 높고, 밤에는 낮음
        if 6 <= hour <= 18:  # 6시~18시
            sc.R_Glob_can = 800 + 200 * np.sin(np.pi * (hour - 6) / 12)
        else:
            sc.R_Glob_can = 0
        
        # 외부 온도: 낮에는 따뜻하고, 밤에는 차가움
        sc.Tout_Kelvin = 273.15 + 15 + 10 * np.sin(np.pi * (hour - 6) / 12)
        
        # 설정 온도
        sc.T_air_sp = 273.15 + 20  # 20°C
        
        # 상대습도: 시간에 따라 변화
        sc.RH_air = 0.6 + 0.2 * np.sin(np.pi * hour / 12)
        
        # 스크린 사용 가능 여부
        sc.SC_usable = 1.0 if 6 <= hour <= 18 else 0.0
        
        # 스크린 제어 업데이트
        sc.step(dt)
        
        # 결과 저장
        sc_values.append(sc.SC)
        states.append(sc.state)
        timers.append(sc.timer)
        
    
    # 결과 분석
    print(f"\n=== 시뮬레이션 결과 분석 ===")
    print(f"총 시뮬레이션 시간: {total_time/3600:.1f}시간")
    print(f"SC 값 범위: {min(sc_values):.2f} ~ {max(sc_values):.2f}")
    print(f"상태 변화 횟수: {len(set(states))}")
    print(f"사용된 상태들: {set(states)}")
    
    # 그래프 그리기
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
    
    # 1. SC 값 변화
    ax1.plot(time_array / 3600, sc_values, 'b-', linewidth=2)
    ax1.set_ylabel('SC (Screen Closure)')
    ax1.set_title('Improved Control_ThScreen - SC Value Changes')
    ax1.grid(True)
    ax1.set_ylim(-0.1, 1.1)
    
    # 2. 상태 변화
    state_nums = [list(set(states)).index(s) for s in states]
    ax2.plot(time_array / 3600, state_nums, 'r-', linewidth=2)
    ax2.set_ylabel('State')
    ax2.set_title('State Transitions')
    ax2.set_yticks(range(len(set(states))))
    ax2.set_yticklabels(list(set(states)))
    ax2.grid(True)
    
    # 3. 타이머 변화
    ax3.plot(time_array / 3600, np.array(timers) / 60, 'g-', linewidth=2)
    ax3.set_xlabel('Time [hours]')
    ax3.set_ylabel('Timer [minutes]')
    ax3.set_title('Timer Changes')
    ax3.grid(True)
    
    plt.tight_layout()
    plt.savefig('improved_screen_control_test.png', dpi=300, bbox_inches='tight')
    plt.show()
    
def test_state_transitions():
    """상태 전이 로직 테스트"""
    print("\n=== 상태 전이 로직 테스트 ===")
    
    # 테스트 케이스들
    test_cases = [
        {
            'name': '일사량 높음 + 외부온도 낮음 → opening_ColdDay',
            'R_Glob_can': 100,
            'Tout_Kelvin': 273.15 + 10,  # 10°C
            'T_air_sp': 273.15 + 20,     # 20°C
            'RH_air': 0.5,
            'SC_usable': 1.0,
            'expected_state': 'opening_ColdDay'
        },
        {
            'name': '일사량 높음 + 외부온도 높음 → opening_WarmDay',
            'R_Glob_can': 100,
            'Tout_Kelvin': 273.15 + 25,  # 25°C
            'T_air_sp': 273.15 + 20,     # 20°C
            'RH_air': 0.5,
            'SC_usable': 1.0,
            'expected_state': 'opening_WarmDay'
        },
        {
            'name': '습도 높음 → crack',
            'R_Glob_can': 0,
            'Tout_Kelvin': 273.15 + 15,
            'T_air_sp': 273.15 + 20,
            'RH_air': 0.9,  # 90%
            'SC_usable': 1.0,
            'expected_state': 'crack'
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n테스트 {i+1}: {test_case['name']}")
        
        # 각 테스트마다 인스턴스 새로 생성!
        sc = Control_ThScreen(R_Glob_can_min=35)
        
        # 5분(300초) 동안 현재 상태 유지
        for _ in range(5):
            sc.step(60)

        # 그 후 입력값을 바꿔서 전이 시도
        sc.R_Glob_can = test_case['R_Glob_can']
        sc.Tout_Kelvin = test_case['Tout_Kelvin']
        sc.T_air_sp = test_case['T_air_sp']
        sc.RH_air = test_case['RH_air']
        sc.SC_usable = test_case['SC_usable']

        # 다시 1분 스텝 실행
        sc.step(60)
        
        # 결과 확인
        actual_state = sc.state
        expected_state = test_case['expected_state']
        
        print(f"  예상 상태: {expected_state}")
        print(f"  실제 상태: {actual_state}")
        print(f"  SC 값: {sc.SC:.2f}")
        print(f"  결과: {'✅ 통과' if actual_state == expected_state else '❌ 실패'}")

if __name__ == "__main__":
    test_improved_screen_control()
    test_state_transitions() 