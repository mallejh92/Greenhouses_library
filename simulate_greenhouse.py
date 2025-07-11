import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
from Greenhouse_1 import Greenhouse_1
import time
import signal
import sys

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 시뮬레이션 중단 플래그
simulation_interrupted = False

def signal_handler(signum, frame):
    """Ctrl+C 시그널 핸들러"""
    global simulation_interrupted
    print("\n시뮬레이션을 중단합니다... (Ctrl+C 감지됨)")
    simulation_interrupted = True

# 시그널 핸들러 등록
signal.signal(signal.SIGINT, signal_handler)

def simulate_greenhouse(dt=1.0, sim_time=24*3600, debug_interval=3600):
    """
    온실 시뮬레이션 실행
    
    Args:
        dt (float): 시간 간격 [초]
        sim_time (float): 시뮬레이션 시간 [초]
        debug_interval (int): 디버그 출력 간격 [초]
    
    Returns:
        dict: 시뮬레이션 결과
    """
    global simulation_interrupted
    
    # 시뮬레이션 설정
    n_steps = int(sim_time / dt)
    logging.info(f"시뮬레이션 시작: {n_steps} 스텝, dt={dt}초")
    
    # 온실 모델 초기화
    try:
        greenhouse = Greenhouse_1()
        logging.info("온실 모델 초기화 완료")
    except Exception as e:
        logging.error(f"온실 모델 초기화 실패: {e}")
        return None
    
    # 결과 저장 배열
    results = {
        'time': np.zeros(n_steps),
        'T_air': np.zeros(n_steps),
        'T_air_top': np.zeros(n_steps),
        'T_canopy': np.zeros(n_steps),
        'T_cover': np.zeros(n_steps),
        'T_floor': np.zeros(n_steps),
        'RH_air': np.zeros(n_steps),
        'RH_air_top': np.zeros(n_steps),
        'VP_air': np.zeros(n_steps),
        'VP_air_top': np.zeros(n_steps),
        'CO2_air': np.zeros(n_steps),
        'q_heat_tot': np.zeros(n_steps),
        'E_thermal': np.zeros(n_steps),
        'LAI': np.zeros(n_steps),
        'DM_harvest': np.zeros(n_steps)
    }
    
    # 시뮬레이션 루프
    start_time = time.time()
    
    for step in range(n_steps):
        if simulation_interrupted:
            logging.info(f"시뮬레이션이 {step} 스텝에서 중단되었습니다.")
            break
        
        try:
            # 시뮬레이션 스텝 실행
            greenhouse.step(dt)
            
            # 결과 저장
            current_time = step * dt / 3600  # 시간 단위
            results['time'][step] = current_time
            
            # 온도 데이터
            results['T_air'][step] = greenhouse.air.T
            results['T_air_top'][step] = greenhouse.air_Top.T
            results['T_canopy'][step] = greenhouse.canopy.T
            results['T_cover'][step] = greenhouse.cover.T
            results['T_floor'][step] = greenhouse.floor.T
            
            # 습도 데이터
            results['RH_air'][step] = greenhouse.air.RH
            results['RH_air_top'][step] = greenhouse.air_Top.RH
            results['VP_air'][step] = greenhouse.air.massPort.VP
            results['VP_air_top'][step] = greenhouse.air_Top.massPort.VP
            
            # CO2 데이터
            if hasattr(greenhouse, 'CO2_air'):
                results['CO2_air'][step] = greenhouse.CO2_air.CO2_ppm
            
            # 에너지 데이터
            results['q_heat_tot'][step] = greenhouse.q_tot
            results['E_thermal'][step] = greenhouse.E_th_tot_kWhm2
            
            # 작물 데이터
            if hasattr(greenhouse, 'canopy'):
                results['LAI'][step] = greenhouse.canopy.LAI
            if hasattr(greenhouse, 'TYM'):
                results['DM_harvest'][step] = greenhouse.TYM.DM_Har
            
            # 진행 상황 출력
            if step % (debug_interval // dt) == 0:
                elapsed = time.time() - start_time
                progress = (step / n_steps) * 100
                logging.info(f"진행률: {progress:.1f}% ({step}/{n_steps}), "
                           f"시간: {current_time:.1f}h, "
                           f"실행시간: {elapsed:.1f}초, "
                           f"T_air: {results['T_air'][step]:.1f}K, "
                           f"RH_air: {results['RH_air'][step]*100:.1f}%")
                
                # RH 100% 포화 경고
                if results['RH_air'][step] >= 0.99:
                    logging.warning(f"상대습도 포화 상태: {results['RH_air'][step]*100:.1f}%")
        
        except Exception as e:
            logging.error(f"시뮬레이션 오류 (스텝 {step}): {e}")
            break
    
    # 시뮬레이션 완료
    elapsed_total = time.time() - start_time
    logging.info(f"시뮬레이션 완료: {elapsed_total:.1f}초")
    
    return results

def plot_results(results):
    """시뮬레이션 결과 시각화"""
    if results is None:
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 온도 그래프
    ax1 = axes[0, 0]
    ax1.plot(results['time'], results['T_air'] - 273.15, 'b-', label='Air', linewidth=2)
    ax1.plot(results['time'], results['T_air_top'] - 273.15, 'r-', label='Air Top', linewidth=2)
    ax1.plot(results['time'], results['T_canopy'] - 273.15, 'g-', label='Canopy', linewidth=2)
    ax1.plot(results['time'], results['T_cover'] - 273.15, 'c-', label='Cover', linewidth=2)
    ax1.plot(results['time'], results['T_floor'] - 273.15, 'm-', label='Floor', linewidth=2)
    ax1.set_xlabel('Time (hours)')
    ax1.set_ylabel('Temperature (°C)')
    ax1.set_title('Greenhouse Temperatures')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 습도 그래프
    ax2 = axes[0, 1]
    ax2.plot(results['time'], results['RH_air'] * 100, 'b-', label='Air RH', linewidth=2)
    ax2.plot(results['time'], results['RH_air_top'] * 100, 'r-', label='Air Top RH', linewidth=2)
    ax2.set_xlabel('Time (hours)')
    ax2.set_ylabel('Relative Humidity (%)')
    ax2.set_title('Relative Humidity')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 100)
    
    # 증기압 그래프
    ax3 = axes[1, 0]
    ax3.plot(results['time'], results['VP_air'], 'b-', label='Air VP', linewidth=2)
    ax3.plot(results['time'], results['VP_air_top'], 'r-', label='Air Top VP', linewidth=2)
    ax3.set_xlabel('Time (hours)')
    ax3.set_ylabel('Vapor Pressure (Pa)')
    ax3.set_title('Vapor Pressure')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 에너지 그래프
    ax4 = axes[1, 1]
    ax4.plot(results['time'], results['q_heat_tot'], 'r-', label='Heat Flux', linewidth=2)
    ax4.plot(results['time'], results['E_thermal'], 'g-', label='Thermal Energy', linewidth=2)
    ax4.set_xlabel('Time (hours)')
    ax4.set_ylabel('Energy (W/m² or kWh/m²)')
    ax4.set_title('Energy Consumption')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('simulation_results.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """메인 실행 함수"""
    print("=== 온실 시뮬레이션 시작 ===")
    
    # 시뮬레이션 실행
    results = simulate_greenhouse(
        dt=1.0,           # 1초 간격
        sim_time=24*3600, # 24시간
        debug_interval=3600  # 1시간마다 출력
    )
    
    if results is not None:
        # 결과 저장
        np.savez('simulation_results.npz', **results)
        print("결과가 'simulation_results.npz'에 저장되었습니다.")
        
        # 시각화
        plot_results(results)
        
        # 최종 상태 출력
        print("\n=== 최종 상태 ===")
        print(f"최종 공기 온도: {results['T_air'][-1] - 273.15:.1f}°C")
        print(f"최종 공기 습도: {results['RH_air'][-1]*100:.1f}%")
        print(f"총 열에너지: {results['E_thermal'][-1]:.2f} kWh/m²")
        if not np.all(results['DM_harvest'] == 0):
            print(f"수확량: {results['DM_harvest'][-1]:.3f} kg/m²")
    else:
        print("시뮬레이션이 실패했습니다.")

if __name__ == "__main__":
    main()
