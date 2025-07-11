import numpy as np

class Flow1DimInc:
    """
    1-D 비압축성 유체 흐름 모델 (Modelica Flow1DimInc와 동일)
    유한 체적 이산화 기반 - 비압축성 유체 모델
    """
    
    def __init__(self, N=10, Nt=1, A=16.18, V=0.03781, Mdotnom=0.2588, Unom=1000,
                 pstart=101325, Tstart_inlet=293.15, Tstart_outlet=313.15, 
                 steadystate=True, Discretization='centr_diff'):
        """
        초기화 파라미터 (Modelica와 동일)
        """
        # 기본 파라미터
        self.N = N                    # 셀 개수
        self.Nt = Nt                  # 병렬 셀 개수
        self.A = A                    # 열교환 면적 [m²]
        self.V = V                    # 체적 [m³]
        self.Mdotnom = Mdotnom        # 공칭 질량 유량 [kg/s]
        self.Unom = Unom              # 열전달 계수 [W/m²·K]
        self.pstart = pstart          # 초기 압력 [Pa]
        self.Tstart_inlet = Tstart_inlet    # 입구 온도 [K]
        self.Tstart_outlet = Tstart_outlet  # 출구 온도 [K]
        self.steadystate = steadystate
        self.Discretization = Discretization
        
        # 상태 변수들 (Modelica와 동일)
        self.T = np.linspace(Tstart_inlet, Tstart_outlet, N)  # 온도 분포 [K]
        self.h = np.zeros(N)          # 엔탈피 [J/kg]
        self.rho = np.full(N, 1000.0) # 밀도 [kg/m³]
        self.p = np.full(N, pstart)   # 압력 [Pa]
        self.qdot = np.zeros(N)       # 열유속 [W/m²]
        
        # 요약 변수들 (Modelica Summary와 동일)
        self.Q_tot = 0.0              # 총 열유량 [W]
        self.M_tot = 0.0              # 총 질량 [kg]
        self.Mdot = Mdotnom           # 질량 유량 [kg/s]
        
        # 엔탈피 초기화
        self._initialize_enthalpy()
    
    def _initialize_enthalpy(self):
        """엔탈피 초기화 (Modelica와 동일한 방식)"""
        cp = 4186.0  # 물의 비열 [J/kg·K]
        for i in range(self.N):
            self.h[i] = cp * (self.T[i] - 273.15)
    
    def step(self, dt):
        """시뮬레이션 스텝 실행"""
        # 총 열유량 계산 (Modelica: Q_tot = A/N*sum(Cells.qdot)*Nt)
        self.Q_tot = self.A / self.N * np.sum(self.qdot) * self.Nt
        
        # 총 질량 계산 (Modelica: M_tot = V/N*sum(Cells.rho))
        self.M_tot = self.V / self.N * np.sum(self.rho)
        
        # 온도 업데이트 (단순화된 열전달)
        if not self.steadystate:
            cp = 4186.0  # 물의 비열
            for i in range(self.N):
                if self.rho[i] > 0:
                    dT_dt = self.qdot[i] / (self.rho[i] * cp)
                    self.T[i] += dT_dt * dt
                    self.h[i] = cp * (self.T[i] - 273.15)
    
    def set_heat_input(self, heat_input):
        """열 입력 설정"""
        if isinstance(heat_input, (list, np.ndarray)):
            self.qdot = np.array(heat_input)[:self.N]
        else:
            self.qdot = np.full(self.N, heat_input)
    
    def get_state(self):
        """현재 상태 반환"""
        return {
            'T': self.T.copy(),
            'h': self.h.copy(),
            'rho': self.rho.copy(),
            'p': self.p.copy(),
            'Q_tot': self.Q_tot,
            'M_tot': self.M_tot,
            'Mdot': self.Mdot
        }

