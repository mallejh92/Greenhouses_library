import unittest
import numpy as np
from Components.Greenhouse.Air import Air

class TestAir(unittest.TestCase):
    def setUp(self):
        """테스트를 위한 기본 설정"""
        print("\n테스트 설정 초기화...")
        # 기본 매개변수로 Air 인스턴스 생성
        self.air = Air(
            A=10000.0,  # 바닥 면적 [m²]
            h_Air=4.0,  # 공기층 높이 [m]
            T_start=298.15,  # 초기 온도 [K] (25°C)
            steadystate=False,
            steadystateVP=False
        )
        print("초기화 완료")
    
    def test_initialization(self):
        """초기화 테스트"""
        print("\n초기화 테스트 실행...")
        # 기본 속성 확인
        self.assertEqual(self.air.A, 10000.0)
        self.assertEqual(self.air.h_Air, 4.0)
        self.assertEqual(self.air.T, 298.15)
        self.assertEqual(self.air.V, 40000.0)  # A * h_Air = 10000 * 4 = 40000
        print("기본 속성 확인 완료")
        
        # 포트 확인
        self.assertIsNotNone(self.air.heatPort)
        self.assertIsNotNone(self.air.massPort)
        self.assertIsNotNone(self.air.R_Air_Glob)
                # Radiation input vector should be initialized with zeros
        self.assertEqual(len(self.air.R_Air_Glob.values), 2)
        self.assertTrue(all(hf.value == 0.0 for hf in self.air.R_Air_Glob.values))
        print("포트 확인 완료")
    
    def test_temperature_update(self):
        """온도 업데이트 테스트"""
        print("\n온도 업데이트 테스트 실행...")
        # 초기 온도 저장
        initial_T = self.air.T
        print(f"초기 온도: {initial_T}K")
        
        # 열유속 설정
        Q_flow = 1000.0  # 1kW의 열유속
        R_Air_Glob = [100.0, 50.0]  # 태양광과 조명으로부터의 방사열
        self.air.set_inputs(Q_flow, R_Air_Glob, None)
        
        # 한 스텝 진행
        dt = 60.0  # 1분
        T, RH = self.air.step(dt)
        print(f"스텝 후 온도: {T}K")
        
        # 온도가 증가했는지 확인
        self.assertGreater(T, initial_T)
        print("온도 증가 확인 완료")
    
    def test_humidity_update(self):
        """습도 업데이트 테스트"""
        print("\n습도 업데이트 테스트 실행...")
        # 초기 습도 저장
        initial_RH = self.air.RH
        print(f"초기 상대습도: {initial_RH*100:.1f}%")
        
        # 수증기압 설정
        massPort_VP = 2000.0  # 2kPa의 수증기압
        self.air.set_inputs(0.0, None, massPort_VP)
        
        # 한 스텝 진행
        dt = 60.0
        T, RH = self.air.step(dt)
        print(f"스텝 후 상대습도: {RH*100:.1f}%")
        
        # 습도가 변경되었는지 확인
        self.assertNotEqual(RH, initial_RH)
        print("습도 변화 확인 완료")
    
    def test_steady_state(self):
        """정상 상태 테스트"""
        print("\n정상 상태 테스트 실행...")
        # 정상 상태 모드로 변경
        steady_air = Air(
            A=10000.0,
            h_Air=4.0,
            T_start=298.15,
            steadystate=True,
            steadystateVP=True
        )
        print("정상 상태 모드로 초기화 완료")
        
        # 열유속 설정
        Q_flow = 1000.0
        R_Air_Glob = [100.0, 50.0]
        steady_air.set_inputs(Q_flow, R_Air_Glob, None)
        
        # 초기 온도 저장
        initial_T = steady_air.T
        print(f"초기 온도: {initial_T}K")
        
        # 한 스텝 진행
        dt = 60.0
        T, RH = steady_air.step(dt)
        print(f"스텝 후 온도: {T}K")
        
        # 정상 상태에서는 온도가 변화하지 않아야 함
        self.assertEqual(T, initial_T)
        print("정상 상태 확인 완료")
    
    def test_power_input(self):
        """방사열 입력 테스트"""
        print("\n방사열 입력 테스트 실행...")
        # 방사열 설정
        R_Air_Glob = [100.0, 50.0]  # 태양광과 조명으로부터의 방사열
        self.air.set_inputs(0.0, R_Air_Glob, None)

        # Ensure values are stored correctly
        for hf, expected in zip(self.air.R_Air_Glob.values, R_Air_Glob):
            self.assertAlmostEqual(hf.value, expected)
        
        # 방사열로부터의 전력 계산
        P_Air = self.air.compute_power_input()
        print(f"계산된 전력: {P_Air}W")
        
        # 예상 전력: (100 + 50) * 10000 = 1500000W
        expected_power = 1500000.0
        self.assertAlmostEqual(P_Air, expected_power)
        print("방사열 전력 계산 확인 완료")

if __name__ == '__main__':
    unittest.main(verbosity=2) 