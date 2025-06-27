import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List, Optional
import logging
from pathlib import Path
import json
from Greenhouse_1 import Greenhouse_1
import time
import signal
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('greenhouse_simulation.log'),
        logging.StreamHandler()
    ]
)

# 전역 변수로 시뮬레이션 중단 플래그 설정
simulation_interrupted = False

def signal_handler(signum, frame):
    """Ctrl+C 시그널 핸들러"""
    global simulation_interrupted
    print("\n\n시뮬레이션을 중단합니다... (Ctrl+C 감지됨)")
    logging.info("사용자에 의해 시뮬레이션이 중단되었습니다 (Ctrl+C)")
    simulation_interrupted = True

# 시그널 핸들러 등록
signal.signal(signal.SIGINT, signal_handler)

@dataclass
class SimulationConfig:
    """시뮬레이션 설정값을 관리하는 클래스"""
    dt: float = 1.0                    # 시간 간격 [s] (1초로 변경)
    sim_time: float = 24 * 3600.0      # 시뮬레이션 시간 [s] (24시간)
    time_unit_scaling: float = 1.0     # 시간 단위 스케일링
    debug_interval: int = 3600         # 디버그 출력 간격 (스텝, 1시간마다)
    
    def __post_init__(self):
        """초기화 후 검증"""
        if self.sim_time % self.dt != 0:
            logging.warning(f"시뮬레이션 시간({self.sim_time}초)이 dt({self.dt}초)의 배수가 아니어 조정합니다.")
            self.sim_time = (self.sim_time // self.dt) * self.dt
    
    @classmethod
    def from_file(cls, filepath: str) -> 'SimulationConfig':
        """JSON 파일에서 설정을 로드합니다."""
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        return cls(**config_dict)
    
    def save(self, filepath: str) -> None:
        """설정을 JSON 파일로 저장합니다."""
        with open(filepath, 'w') as f:
            json.dump(self.__dict__, f, indent=4)

class SimulationResults:
    """시뮬레이션 결과를 관리하는 클래스"""
    def __init__(self, n_steps: int):
        self.times = np.linspace(0, 0, n_steps)  # 시간 [h]
        self.data: Dict[str, np.ndarray] = {
            'temperatures': {
                'air': np.zeros(n_steps),
                'air_top': np.zeros(n_steps),
                'canopy': np.zeros(n_steps),
                'cover': np.zeros(n_steps),
                'floor': np.zeros(n_steps),
                'screen': np.zeros(n_steps),
                'pipe_low': np.zeros(n_steps),
                'pipe_up': np.zeros(n_steps),
                'soil': np.zeros(n_steps),
                'outdoor': np.zeros(n_steps),
                'sky': np.zeros(n_steps)
            },
            'humidity': {
                'air_rh': np.zeros(n_steps),
                'air_top_rh': np.zeros(n_steps),
                'air_vp': np.zeros(n_steps),
                'air_top_vp': np.zeros(n_steps),
                'cover_vp': np.zeros(n_steps),
                'screen_vp': np.zeros(n_steps),
                'canopy_vp': np.zeros(n_steps)
            },
            'energy': {
                'heating': {
                    'q_low': np.zeros(n_steps),
                    'q_up': np.zeros(n_steps),
                    'q_tot': np.zeros(n_steps),
                    'E_th_tot_kWhm2': np.zeros(n_steps),
                    'E_th_tot': np.zeros(n_steps)
                },
                'electrical': {
                    'W_el_illu': np.zeros(n_steps),
                    'W_el_illu_instant': np.zeros(n_steps),
                    'E_el_tot_kWhm2': np.zeros(n_steps),
                    'E_el_tot': np.zeros(n_steps)
                }
            },
            'control': {
                'screen': {
                    'SC': np.zeros(n_steps),
                    'SC_usable': np.zeros(n_steps)
                },
                'ventilation': {
                    'U_vents': np.zeros(n_steps),
                    'f_vent': np.zeros(n_steps)
                },
                'heating': {
                    'Mdot': np.zeros(n_steps),
                    'T_supply': np.zeros(n_steps)
                },
                'co2': {
                    'CO2_air': np.zeros(n_steps),
                    'CO2_injection': np.zeros(n_steps)
                },
                'illumination': {
                    'switch': np.zeros(n_steps),
                    'P_el': np.zeros(n_steps)
                }
            },
            'crop': {
                'LAI': np.zeros(n_steps),
                'DM_Har': np.zeros(n_steps),
                'C_Leaf': np.zeros(n_steps),
                'C_Stem': np.zeros(n_steps),
                'R_PAR_can': np.zeros(n_steps),
                'MC_AirCan': np.zeros(n_steps)
            }
        }
    
    def update(self, step: int, state: Dict) -> None:
        """한 스텝의 상태를 결과에 저장합니다."""
        self.times[step] = state.get('time', 0)
        
        # 온도 데이터 업데이트
        for key, value in state['temperatures'].items():
            if key in self.data['temperatures']:
                self.data['temperatures'][key][step] = value
        
        # 습도 데이터 업데이트
        for key, value in state['humidity'].items():
            if key in self.data['humidity']:
                self.data['humidity'][key][step] = value
        
        # 에너지 데이터 업데이트
        for category in ['heating', 'electrical']:
            for key, value in state['energy'][category].items():
                if key in self.data['energy'][category]:
                    self.data['energy'][category][key][step] = value
        
        # 제어 데이터 업데이트
        for category in ['screen', 'ventilation', 'heating', 'co2', 'illumination']:
            for key, value in state['control'][category].items():
                if key in self.data['control'][category]:
                    self.data['control'][category][key][step] = value
        
        # 작물 데이터 업데이트
        for key, value in state['crop'].items():
            if key in self.data['crop']:
                self.data['crop'][key][step] = value
    
    def save(self, filepath: str) -> None:
        """결과를 NPZ 파일로 저장합니다."""
        save_dict = {'times': self.times}
        for category, subcategories in self.data.items():
            if isinstance(subcategories, dict):
                for subcategory, data in subcategories.items():
                    if isinstance(data, dict):
                        for key, array in data.items():
                            save_dict[f'{category}_{subcategory}_{key}'] = array
                    else:
                        save_dict[f'{category}_{subcategory}'] = data
            else:
                save_dict[category] = subcategories
        np.savez(filepath, **save_dict)
    
    @classmethod
    def load(cls, filepath: str) -> 'SimulationResults':
        """NPZ 파일에서 결과를 로드합니다."""
        data = np.load(filepath)
        n_steps = len(data['times'])
        results = cls(n_steps)
        results.times = data['times']
        # 데이터 복원 로직 구현 필요
        return results

def plot_results(results: SimulationResults, save_path: Optional[str] = None) -> None:
    """시뮬레이션 결과를 시각화합니다."""
    fig = plt.figure(figsize=(20, 15))
    
    # 1. 온도 그래프
    ax1 = plt.subplot(4, 2, 1)
    for name, data in results.data['temperatures'].items():
        if name in ['air', 'air_top', 'canopy', 'cover', 'floor', 'outdoor']:
            ax1.plot(results.times, data, label=name.replace('_', ' ').title())
    ax1.set_title('Temperature Changes')
    ax1.set_xlabel('Time [h]')
    ax1.set_ylabel('Temperature [°C]')
    ax1.legend()
    ax1.grid(True)
    
    # 2. 습도 그래프
    ax2 = plt.subplot(4, 2, 2)
    ax2.plot(results.times, results.data['humidity']['air_rh'], label='Indoor')
    ax2.plot(results.times, results.data['humidity']['air_top_rh'], label='Top')
    ax2.set_title('Relative Humidity Changes')
    ax2.set_xlabel('Time [h]')
    ax2.set_ylabel('Relative Humidity [%]')
    ax2.legend()
    ax2.grid(True)
    
    # 3. 열량 그래프
    ax3 = plt.subplot(4, 2, 3)
    ax3.plot(results.times, results.data['energy']['heating']['q_tot'], label='Total')
    ax3.plot(results.times, results.data['energy']['heating']['q_low'], label='Low Pipe')
    ax3.plot(results.times, results.data['energy']['heating']['q_up'], label='Up Pipe')
    ax3.set_title('Heat Load')
    ax3.set_xlabel('Time [h]')
    ax3.set_ylabel('Heat Load [W/m²]')
    ax3.legend()
    ax3.grid(True)
    
    # 4. 에너지 그래프
    ax4 = plt.subplot(4, 2, 4)
    ax4.plot(results.times, results.data['energy']['heating']['E_th_tot_kWhm2'], 
             label='Heating')
    ax4.plot(results.times, results.data['energy']['electrical']['E_el_tot_kWhm2'], 
             label='Electrical')
    ax4.set_title('Cumulative Energy Consumption')
    ax4.set_xlabel('Time [h]')
    ax4.set_ylabel('Energy [kWh/m²]')
    ax4.legend()
    ax4.grid(True)
    
    # 5. CO2 그래프
    ax5 = plt.subplot(4, 2, 5)
    ax5.plot(results.times, results.data['control']['co2']['CO2_air'])
    ax5.set_title('CO₂ Concentration')
    ax5.set_xlabel('Time [h]')
    ax5.set_ylabel('CO₂ [mg/m³]')
    ax5.grid(True)
    
    # 6. 제어 그래프
    ax6 = plt.subplot(4, 2, 6)
    ax6.plot(results.times, results.data['control']['screen']['SC'], 
             label='Thermal Screen')
    ax6.plot(results.times, results.data['control']['ventilation']['U_vents'], 
             label='Ventilation')
    ax6.set_title('Control Variables')
    ax6.set_xlabel('Time [h]')
    ax6.set_ylabel('Opening Rate [0-1]')
    ax6.legend()
    ax6.grid(True)

    # 7. 작물 그래프
    ax7 = plt.subplot(4, 2, 7)
    ax7.plot(results.times, results.data['crop']['DM_Har'])
    ax7.set_title('Tomato Dry Matter')
    ax7.set_xlabel('Time [h]')
    ax7.set_ylabel('Dry Matter [mg/m²]')
    ax7.grid(True)
    
    # 8. 엽면적지수 그래프
    ax8 = plt.subplot(4, 2, 8)
    ax8.plot(results.times, results.data['crop']['LAI'])
    ax8.set_title('Leaf Area Index')
    ax8.set_xlabel('Time [h]')
    ax8.set_ylabel('LAI [m²/m²]')
    ax8.grid(True)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()

def simulate_greenhouse(config: Optional[SimulationConfig] = None) -> SimulationResults:
    """
    온실 시뮬레이션을 실행합니다.
    
    Args:
        config: 시뮬레이션 설정값. None인 경우 기본값 사용
    
    Returns:
        SimulationResults: 시뮬레이션 결과
    
    Raises:
        ValueError: 시뮬레이션 중 오류 발생 시
        KeyboardInterrupt: 사용자가 Ctrl+C로 중단한 경우
    """
    global simulation_interrupted
    
    try:
        # 시뮬레이션 중단 플래그 초기화
        simulation_interrupted = False
        
        # 설정값 로드 또는 기본값 사용
        if config is None:
            config = SimulationConfig()
        
        # 온실 모델 생성
        greenhouse = Greenhouse_1(time_unit_scaling=config.time_unit_scaling)
        n_steps = int(config.sim_time / config.dt)
        
        logging.info(f"시뮬레이션 시작: {n_steps}시간 ({n_steps} 스텝)")
        logging.info(f"시간 간격: {config.dt}초")
        logging.info(f"총 시뮬레이션 시간: {config.sim_time/3600:.1f}시간")
        logging.info("시뮬레이션을 중단하려면 Ctrl+C를 누르세요.")
        
        # 결과 저장소 초기화
        results = SimulationResults(n_steps)
        
        # 시뮬레이션 루프
        for i in range(n_steps):
            try:
                # 시뮬레이션 중단 확인
                if simulation_interrupted:
                    logging.info(f"시뮬레이션이 {i} 스텝에서 중단되었습니다 (t={i*config.dt/3600:.1f}h)")
                    # 현재까지의 결과만 반환
                    results.times = results.times[:i]
                    for category, subcategories in results.data.items():
                        if isinstance(subcategories, dict):
                            for subcategory, data in subcategories.items():
                                if isinstance(data, dict):
                                    for key, array in data.items():
                                        results.data[category][subcategory][key] = array[:i]
                                else:
                                    results.data[category][subcategory] = data[:i]
                        else:
                            results.data[category] = subcategories[:i]
                    return results
                
                # 시뮬레이션 스텝 실행
                greenhouse.step(config.dt, i)
                state = greenhouse._get_state()
                state['time'] = i * config.dt / 3600  # 시간 [h] 추가
                results.update(i, state)
                
                # 디버그 출력 (매 시간마다)
                if i % config.debug_interval == 0:
                    logging.info(f"\n=== Step {i} | t={state['time']:.1f} h ===")
                    logging.info(
                        f" T_air={state['temperatures']['air']:.2f}°C, "
                        f"T_air_top={state['temperatures']['air_top']:.2f}°C, "
                        f"T_out={state['temperatures']['outdoor']:.2f}°C, "
                        f"RH_air={state['humidity']['air_rh']:.1f}%, "
                        f"CO2={state['control']['co2']['CO2_air']:.1f} mg/m³"
                    )
                    logging.info(
                        f" q_tot={state['energy']['heating']['q_tot']:.1f} W/m², "
                        f"E_th={state['energy']['heating']['E_th_tot_kWhm2']:.2f} kWh/m², "
                        f"E_el={state['energy']['electrical']['E_el_tot_kWhm2']:.2f} kWh/m²"
                    )
                    logging.info(
                        f" SC={state['control']['screen']['SC']:.2f}, "
                        f"vent={state['control']['ventilation']['U_vents']:.2f}, "
                        f"illumination={state['control']['illumination']['switch']:.1f}, "
                        f"DM_Har={state['crop']['DM_Har']:.2f} mg/m²"
                    )
            
            except KeyboardInterrupt:
                logging.info(f"시뮬레이션이 {i} 스텝에서 중단되었습니다 (t={i*config.dt/3600:.1f}h)")
                # 현재까지의 결과만 반환
                results.times = results.times[:i]
                for category, subcategories in results.data.items():
                    if isinstance(subcategories, dict):
                        for subcategory, data in subcategories.items():
                            if isinstance(data, dict):
                                for key, array in data.items():
                                    results.data[category][subcategory][key] = array[:i]
                            else:
                                results.data[category][subcategory] = data[:i]
                    else:
                        results.data[category] = subcategories[:i]
                return results
            except Exception as e:
                logging.error(f"스텝 {i} (t={i*config.dt/3600:.1f}h) 실행 중 오류 발생: {str(e)}")
                raise
        
        logging.info("시뮬레이션 완료")
        return results
    
    except Exception as e:
        logging.error(f"시뮬레이션 실행 중 오류 발생: {str(e)}")
        raise

def main():
    """메인 실행 함수"""
    try:
        # 설정 파일 경로
        config_path = Path('simulation_config.json')
        
        # 설정 로드 또는 기본값 사용
        if config_path.exists():
            config = SimulationConfig.from_file(str(config_path))
            logging.info("설정 파일을 로드했습니다.")
        else:
            config = SimulationConfig()
            config.save(str(config_path))
            logging.info("기본 설정을 사용하고 설정 파일을 저장했습니다.")
        
        # 시뮬레이션 시작 시간 기록
        start_time = time.time()
        logging.info("시뮬레이션을 시작합니다...")
        print("시뮬레이션을 시작합니다... (중단하려면 Ctrl+C를 누르세요)")
        
        # 시뮬레이션 실행
        results = simulate_greenhouse(config)
        
        # 시뮬레이션 종료 시간 기록
        end_time = time.time()
        elapsed = end_time - start_time
        logging.info(f"시뮬레이션 소요 시간: {elapsed:.2f}초 ({elapsed/60:.2f}분)")
        print(f"시뮬레이션 소요 시간: {elapsed:.2f}초 ({elapsed/60:.2f}분)")
        
        # 결과 저장
        results_path = Path('simulation_results.npz')
        results.save(str(results_path))
        logging.info(f"시뮬레이션 결과를 {results_path}에 저장했습니다.")
        
        # 결과 시각화
        plot_path = Path('simulation_results.png')
        plot_results(results, str(plot_path))
        logging.info(f"시뮬레이션 결과 그래프를 {plot_path}에 저장했습니다.")
        
    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 중단되었습니다.")
        logging.info("프로그램이 사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"프로그램 실행 중 오류 발생: {str(e)}")
        raise

if __name__ == "__main__":
    main()
