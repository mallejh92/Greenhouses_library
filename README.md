# 온실 시뮬레이션 라이브러리

이 프로젝트는 온실 환경 시뮬레이션을 위한 Python 및 Modelica 기반 라이브러리입니다.

## 주요 기능
- 온실 온도 및 습도 시뮬레이션
- 환기 시스템 모델링
- 토마토 수확량 예측 모델
- 다양한 환경 제어 시스템 구현

## 설치 방법
```bash
pip install -r requirements.txt
```
필요한 패키지는 `requirements.txt`에 명시되어 있으며 `numpy`, `pandas`,
`matplotlib`, `scipy` 등을 포함합니다.

## 사용 방법
```python
from simulate_greenhouse import GreenhouseSimulation

# 시뮬레이션 실행
sim = GreenhouseSimulation()
results = sim.run()
```

## 라이선스
MIT License