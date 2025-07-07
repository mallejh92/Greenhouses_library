from dataclasses import dataclass

@dataclass
class HelmholtzDerivs:
    """
    무차원 Helmholtz 함수와 δ, τ에 대한 미분값들
    Modelica의 HelmholtzDerivs record를 Python으로 변환
    
    이 클래스는 Modelica의 고정밀 유체 물성 모델에서 Helmholtz 자유에너지 기반 
    상태방정식을 구현할 때, 각종 도함수 값을 저장하고 전달하는 데 사용됩니다.
    
    수학적 정의:
    - α: 무차원 Helmholtz 자유에너지
    - δ: 무차원 밀도 (reduced density)
    - τ: 무차원 온도의 역수 (reduced inverse temperature)
    """
    f: float = 0.0              # 무차원 Helmholtz 자유에너지 α
    fdelta: float = 0.0         # ∂α/∂δ (δ에 대한 1차 편미분)
    ftau: float = 0.0           # ∂α/∂τ (τ에 대한 1차 편미분)
    fdeltadelta: float = 0.0    # ∂²α/∂δ² (δ에 대한 2차 편미분)
    fdeltatau: float = 0.0      # ∂²α/∂δ∂τ (δ, τ에 대한 혼합 2차 편미분)
    ftautau: float = 0.0        # ∂²α/∂τ² (τ에 대한 2차 편미분)
