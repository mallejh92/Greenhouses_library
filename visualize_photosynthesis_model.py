#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
토마토 광합성 모델 수식 시각화
각 단계별 함수의 특성을 그래프로 표현
"""

import numpy as np
import matplotlib.pyplot as plt

# matplotlib 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def sigmoid(x, k=-5e-3):
    """시그모이드 함수"""
    return 1 / (1 + np.exp(-k * x))

def temperature_response(T_K, T_25K=298.15, E_j=37000, S=710, H=220000, Rg=8.314):
    """온도 반응 함수 (Arrhenius with high-temp inhibition)"""
    exp_arg1 = np.clip(E_j * (T_K - T_25K) / (Rg * T_K * T_25K), -50, 50)
    exp_arg2 = np.clip((S * T_25K - H) / (Rg * T_25K), -50, 50)
    exp_arg3 = np.clip((S * T_K - H) / (Rg * T_K), -50, 50)
    
    return np.exp(exp_arg1) * (1 + np.exp(exp_arg2)) / (1 + np.exp(exp_arg3))

def light_response(R_PAR, J_POT=200, alpha=0.385, theta=0.7):
    """광 반응 함수 (Michaelis-Menten type)"""
    discriminant = (J_POT + alpha * R_PAR)**2 - 4 * theta * J_POT * alpha * R_PAR
    discriminant = np.maximum(0, discriminant)
    return (J_POT + alpha * R_PAR - np.sqrt(discriminant)) / (2 * theta)

def photosynthesis_rate(CO2_stom, Gamma, J):
    """광합성률 함수"""
    return np.where(
        (CO2_stom + 2 * Gamma > 0) & (J > 0),
        J / 4 * (CO2_stom - Gamma) / (CO2_stom + 2 * Gamma),
        0
    )

def visualize_photosynthesis_model():
    """광합성 모델 시각화"""
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Tomato Photosynthesis Model Components', fontsize=16, fontweight='bold')
    
    # 1. Temperature Response
    ax1 = axes[0, 0]
    T_range = np.linspace(15, 45, 100) + 273.15  # K
    temp_response = temperature_response(T_range)
    ax1.plot(T_range - 273.15, temp_response, 'r-', linewidth=2)
    ax1.set_xlabel('Temperature (°C)')
    ax1.set_ylabel('Temperature Response Factor')
    ax1.set_title('Temperature Response\n(Arrhenius + High-temp Inhibition)')
    ax1.grid(True, alpha=0.3)
    ax1.axvline(25, color='gray', linestyle='--', alpha=0.7, label='Reference (25°C)')
    ax1.legend()
    
    # 2. Light Response
    ax2 = axes[0, 1]
    PAR_range = np.linspace(0, 2000, 100)  # μmol/m²/s
    light_resp = light_response(PAR_range)
    ax2.plot(PAR_range, light_resp, 'g-', linewidth=2)
    ax2.set_xlabel('PAR (μmol/m²/s)')
    ax2.set_ylabel('Electron Transport Rate J (μmol/m²/s)')
    ax2.set_title('Light Response\n(Michaelis-Menten Type)')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(200*0.5, color='gray', linestyle='--', alpha=0.7, label='50% J_max')
    ax2.legend()
    
    # 3. CO₂ Response
    ax3 = axes[0, 2]
    CO2_range = np.linspace(200, 1500, 100)  # mg/m³
    Gamma = 60  # mg/m³
    J_fixed = 150  # μmol/m²/s
    photo_rate = photosynthesis_rate(CO2_range, Gamma, J_fixed)
    ax3.plot(CO2_range, photo_rate, 'b-', linewidth=2)
    ax3.set_xlabel('CO₂ Concentration (mg/m³)')
    ax3.set_ylabel('Photosynthesis Rate P (mg/m²/s)')
    ax3.set_title('CO₂ Response\n(Rubisco-limited)')
    ax3.grid(True, alpha=0.3)
    ax3.axvline(Gamma, color='gray', linestyle='--', alpha=0.7, label=f'Γ = {Gamma} mg/m³')
    ax3.legend()
    
    # 4. Buffer Limitation
    ax4 = axes[1, 0]
    C_buf_range = np.linspace(-0.5, 2.5, 100)  # kg/m²
    C_buf_max = 1.0  # kg/m²
    buffer_effect = sigmoid(C_buf_range - C_buf_max)
    ax4.plot(C_buf_range, buffer_effect, 'm-', linewidth=2)
    ax4.set_xlabel('C_Buf (kg/m²)')
    ax4.set_ylabel('Buffer Limitation Factor')
    ax4.set_title('Buffer Limitation\n(Sigmoid Function)')
    ax4.grid(True, alpha=0.3)
    ax4.axvline(C_buf_max, color='gray', linestyle='--', alpha=0.7, label=f'C_Buf_MAX = {C_buf_max}')
    ax4.legend()
    
    # 5. Combined Effect (Temperature × Light)
    ax5 = axes[1, 1]
    T_test = np.array([15, 20, 25, 30, 35, 40]) + 273.15
    PAR_test = np.linspace(0, 2000, 100)
    
    for i, T in enumerate(T_test):
        temp_factor = temperature_response(np.array([T]))[0]
        J_POT_temp = 200 * temp_factor
        light_resp_temp = light_response(PAR_test, J_POT=J_POT_temp)
        ax5.plot(PAR_test, light_resp_temp, linewidth=2, 
                label=f'{T-273.15:.0f}°C (factor={temp_factor:.2f})')
    
    ax5.set_xlabel('PAR (μmol/m²/s)')
    ax5.set_ylabel('Electron Transport Rate J (μmol/m²/s)')
    ax5.set_title('Temperature × Light Interaction')
    ax5.grid(True, alpha=0.3)
    ax5.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 6. Daily Pattern Simulation
    ax6 = axes[1, 2]
    hours = np.linspace(0, 24, 100)
    
    # Simulate daily patterns
    PAR_daily = 1000 * np.maximum(0, np.sin(np.pi * (hours - 6) / 12))  # Bell curve
    T_daily = 20 + 10 * np.sin(np.pi * (hours - 6) / 12)  # Temperature follows light
    CO2_daily = 400 - 50 * np.sin(np.pi * (hours - 6) / 12)  # CO₂ depletion during day
    
    # Calculate photosynthesis
    photo_daily = []
    for i in range(len(hours)):
        if PAR_daily[i] > 0:
            temp_factor = temperature_response(np.array([T_daily[i] + 273.15]))[0]
            J = light_response(np.array([PAR_daily[i]]), J_POT=200*temp_factor)[0]
            P = photosynthesis_rate(np.array([CO2_daily[i]]), 60, J)[0]
            photo_daily.append(P)
        else:
            photo_daily.append(0)
    
    ax6_twin = ax6.twinx()
    line1 = ax6.plot(hours, photo_daily, 'g-', linewidth=2, label='Photosynthesis')
    line2 = ax6_twin.plot(hours, PAR_daily/10, 'orange', linewidth=1, alpha=0.7, label='PAR/10')
    line3 = ax6_twin.plot(hours, T_daily, 'r--', linewidth=1, alpha=0.7, label='Temperature')
    
    ax6.set_xlabel('Time (hours)')
    ax6.set_ylabel('Photosynthesis Rate (mg/m²/s)', color='g')
    ax6_twin.set_ylabel('PAR/10 (μmol/m²/s) & Temperature (°C)')
    ax6.set_title('Daily Pattern Simulation')
    ax6.grid(True, alpha=0.3)
    
    # Combine legends
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax6.legend(lines, labels, loc='upper right')
    
    plt.tight_layout()
    plt.savefig('photosynthesis_model_visualization.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("시각화 완료: photosynthesis_model_visualization.png 저장됨")

def print_model_summary():
    """모델 요약 출력"""
    print("=== 토마토 광합성 모델 요약 ===\n")
    
    print("1. 주요 입력 변수:")
    print("   - 환경: CO₂ 농도, 온도, PAR 광량")
    print("   - 식물: LAI, 최대 전자전달률")
    print("   - 상태: 탄수화물 버퍼량\n")
    
    print("2. 핵심 프로세스:")
    print("   - 온도 의존성: Arrhenius + 고온 억제")
    print("   - 광 의존성: Michaelis-Menten 포화")
    print("   - CO₂ 의존성: Rubisco 제한")
    print("   - 제품 억제: 시그모이드 버퍼 효과\n")
    
    print("3. 출력:")
    print("   - 순 탄소 동화율 [kg/s]")
    print("   - 실시간 광합성률 [mg/m²/s]\n")
    
    print("4. 모델 특징:")
    print("   - 물리학적 기반 (FvCB 모델)")
    print("   - 환경 반응성")
    print("   - 수치적 안정성 (clipping, 조건부 계산)")
    print("   - 실시간 시뮬레이션 적합")

if __name__ == "__main__":
    print("🌱 토마토 광합성 모델 시각화 🌱\n")
    
    print_model_summary()
    print("\n" + "="*50)
    print("그래프 생성 중...")
    
    visualize_photosynthesis_model()
    
    print("\n✅ 모든 시각화가 완료되었습니다!")
    print("📁 생성된 파일: photosynthesis_model_visualization.png")
    print("📁 수식 문서: photosynthesis_model_equations.md") 