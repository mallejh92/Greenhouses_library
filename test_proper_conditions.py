import numpy as np
import matplotlib.pyplot as plt
from ControlSystems.Climate.Uvents_RH_T_Mdot import Uvents_RH_T_Mdot

def test_proper_operating_conditions():
    """
    실제 온실 운영 조건에 맞는 적절한 테스트
    """
    
    print("🔍 Modelica 원본 의도에 맞는 테스트")
    print("="*60)
    
    # 시뮬레이션 설정
    sim_time = 24 * 3600  # 24시간
    dt = 60.0  # 1분 간격
    n_steps = int(sim_time / dt)
    times = np.arange(n_steps) * dt / 3600  # 시간 [h]
    
    # 현실적인 온실 운영 조건들
    scenarios = [
        {
            'name': '정상 운영 - 겨울철',
            'T_air': np.full(n_steps, 22 + 273.15),     # 22°C (적정 온도)
            'T_air_sp': np.full(n_steps, 20 + 273.15),  # 20°C 설정값
            'RH': np.full(n_steps, 0.75),               # 75% 습도
            'Mdot': np.full(n_steps, 0.528),            # 기본 난방수 유량
            'description': '정상적인 겨울철 운영 (22°C, 75% RH, 난방 가동)'
        },
        {
            'name': '과열 상황',
            'T_air': np.full(n_steps, 27 + 273.15),     # 27°C (토마토 한계 초과)
            'T_air_sp': np.full(n_steps, 20 + 273.15),  # 20°C 설정값
            'RH': np.full(n_steps, 0.75),               # 75% 습도  
            'Mdot': np.full(n_steps, 0.1),              # 낮은 난방수 유량
            'description': '과열 상황 (27°C > 26°C 토마토 한계, 난방 거의 없음)'
        },
        {
            'name': '고습도 상황',
            'T_air': np.full(n_steps, 22 + 273.15),     # 22°C 
            'T_air_sp': np.full(n_steps, 20 + 273.15),  # 20°C 설정값
            'RH': np.full(n_steps, 0.90),               # 90% 습도 (한계 초과)
            'Mdot': np.full(n_steps, 0.528),            # 기본 난방수 유량
            'description': '고습도 상황 (90% > 85% 한계, 제습 필요)'
        },
        {
            'name': '여름철 운영',
            'T_air': np.full(n_steps, 24 + 273.15),     # 24°C
            'T_air_sp': np.full(n_steps, 22 + 273.15),  # 22°C 설정값 (높음)
            'RH': np.full(n_steps, 0.70),               # 70% 습도
            'Mdot': np.full(n_steps, 0.05),             # 난방 거의 없음
            'description': '여름철 운영 (24°C, 난방 최소, 설정값 높음)'
        }
    ]
    
    # 각 시나리오 테스트
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    
    for i, scenario in enumerate(scenarios):
        # 환기 제어기 초기화
        uvent = Uvents_RH_T_Mdot()
        y_results = np.zeros(n_steps)
        
        # 시뮬레이션 실행
        for j in range(n_steps):
            uvent.T_air = scenario['T_air'][j]
            uvent.T_air_sp = scenario['T_air_sp'][j]
            uvent.Mdot = scenario['Mdot'][j]
            uvent.RH_air = scenario['RH'][j]
            
            y_results[j] = uvent.step(dt)
        
        # 그래프 그리기
        ax = axes[i]
        ax.plot(times, y_results * 100, label='Ventilation (%)', 
                color='blue', linewidth=2)
        
        # 평균 환기율 표시
        avg_vent = np.mean(y_results) * 100
        ax.axhline(y=avg_vent, color='red', linestyle='--', alpha=0.7,
                  label=f'Average: {avg_vent:.1f}%')
        
        ax.set_ylabel('Ventilation Rate (%)')
        ax.set_xlabel('Time [h]')
        ax.set_title(f"{scenario['name']}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)
        
        # 상세 정보 출력
        print(f"\n📊 {scenario['name']}:")
        print(f"  조건: {scenario['description']}")
        print(f"  평균 환기율: {avg_vent:.1f}%")
        print(f"  최대 환기율: {np.max(y_results)*100:.1f}%")
        print(f"  최소 환기율: {np.min(y_results)*100:.1f}%")
    
    plt.tight_layout()
    plt.show()
    
    # PID 개별 분석
    print(f"\n🔍 PID 컨트롤러 개별 분석")
    print("="*60)
    
    uvent = Uvents_RH_T_Mdot()
    
    test_conditions = [
        (22+273.15, 20+273.15, 0.75, 0.528, "정상 운영"),
        (27+273.15, 20+273.15, 0.75, 0.1, "과열 상황"),
        (22+273.15, 20+273.15, 0.90, 0.528, "고습도"),
        (24+273.15, 22+273.15, 0.70, 0.05, "여름철")
    ]
    
    for T_air, T_air_sp, RH, Mdot, desc in test_conditions:
        uvent.T_air = T_air
        uvent.T_air_sp = T_air_sp  
        uvent.Mdot = Mdot
        uvent.RH_air = RH
        
        # PID 설정값들 계산
        PIDT_SP = uvent.Tmax_tomato  # 26°C
        PIDT_noH_SP = T_air_sp + 2.0  # 설정값 + 2°C
        
        result = uvent.step(1.0)
        
        print(f"\n{desc}:")
        print(f"  실내온도: {T_air-273.15:.1f}°C")
        print(f"  설정온도: {T_air_sp-273.15:.1f}°C") 
        print(f"  PIDT SP: {PIDT_SP-273.15:.1f}°C (토마토 한계)")
        print(f"  PIDT_noH SP: {PIDT_noH_SP-273.15:.1f}°C (설정값+2°C)")
        print(f"  습도: {RH*100:.0f}% (한계: 85%)")
        print(f"  난방수 유량: {Mdot:.3f} kg/s")
        print(f"  → 환기율: {result*100:.1f}%")

if __name__ == "__main__":
    test_proper_operating_conditions() 