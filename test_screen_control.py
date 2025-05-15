import time
import numpy as np
from ControlSystems.Climate.Utilities.SC_opening_closing import SC_opening_closing

def simulate_screen_control():
    """
    Simulate screen control for both warm and cold days
    """
    # Create screen control instances for different scenarios
    warm_opening = SC_opening_closing(warmDay=True, opening=True)
    warm_closing = SC_opening_closing(warmDay=True, opening=False)
    cold_opening = SC_opening_closing(warmDay=False, opening=True)
    cold_closing = SC_opening_closing(warmDay=False, opening=False)
    
    # Simulation parameters
    dt = 1.0  # Time step [s]
    sim_time = 3600  # Total simulation time [s]
    entry_time = 0.0  # Start time for control
    
    print("\n=== 따뜻한 날 스크린 개방 시뮬레이션 ===")
    print("시간[s]\t제어신호")
    print("-" * 30)
    
    # Simulate warm day opening
    for t in np.arange(0, sim_time, dt):
        signal = warm_opening.update(entry_time, t)
        if t % 60 == 0:  # Print every minute
            print(f"{t:.0f}\t{signal:.3f}")
    
    print("\n=== 따뜻한 날 스크린 폐쇄 시뮬레이션 ===")
    print("시간[s]\t제어신호")
    print("-" * 30)
    
    # Simulate warm day closing
    for t in np.arange(0, sim_time, dt):
        signal = warm_closing.update(entry_time, t)
        if t % 60 == 0:  # Print every minute
            print(f"{t:.0f}\t{signal:.3f}")
    
    print("\n=== 추운 날 스크린 개방 시뮬레이션 ===")
    print("시간[s]\t제어신호")
    print("-" * 30)
    
    # Simulate cold day opening
    for t in np.arange(0, sim_time, dt):
        signal = cold_opening.update(entry_time, t)
        if t % 60 == 0:  # Print every minute
            print(f"{t:.0f}\t{signal:.3f}")
    
    print("\n=== 추운 날 스크린 폐쇄 시뮬레이션 ===")
    print("시간[s]\t제어신호")
    print("-" * 30)
    
    # Simulate cold day closing
    for t in np.arange(0, sim_time, dt):
        signal = cold_closing.update(entry_time, t)
        if t % 60 == 0:  # Print every minute
            print(f"{t:.0f}\t{signal:.3f}")

if __name__ == "__main__":
    try:
        simulate_screen_control()
    except KeyboardInterrupt:
        print("\n시뮬레이션이 중단되었습니다.")
    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}") 