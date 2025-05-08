import numpy as np
import matplotlib.pyplot as plt

class Flow1DimInc:
    """
    Python representation of a 1-D incompressible fluid flow model,
    mimicking the Modelica Flow1DimInc component.
    """

    def __init__(self, N=10, Nt=1, A=16.18, V=0.03781, Mdotnom=0.2588, Unom=1000,
                 pstart=101325, Tstart_inlet=293.15, Tstart_outlet=313.15,
                 steadystate=True, Discretization='centr_diff'):
        self.N = N
        self.Nt = Nt
        self.A = A
        self.V = V
        self.Mdotnom = Mdotnom
        self.Unom = Unom
        self.pstart = pstart
        self.Tstart_inlet = Tstart_inlet
        self.Tstart_outlet = Tstart_outlet
        self.steadystate = steadystate
        self.Discretization = Discretization
        self.pi = np.pi

        # Initialize enthalpy vector linearly between inlet and outlet
        self.hstart = np.linspace(
            self.specific_enthalpy(pstart, Tstart_inlet),
            self.specific_enthalpy(pstart, Tstart_outlet),
            N
        )

        # Create cells and assign initial enthalpy
        self.Cells = []
        for i in range(N):
            cell = self.Cell(i)
            cell.h = self.hstart[i]
            cell.T = Tstart_inlet
            cell.rho = 1000  # assume water density
            cell.qdot = 100 + i * 10  # assign arbitrary heat flow for simulation
            self.Cells.append(cell)

        # Summary class initialization
        self.Summary = self.SummaryClass(
            n=N,
            T=np.array([cell.T for cell in self.Cells]),
            h=np.array([cell.h for cell in self.Cells]),
            hnode=np.zeros(N + 1),
            rho=np.array([cell.rho for cell in self.Cells]),
            Mdot=Mdotnom,
            p=pstart
        )

        self.Q_tot = 0.0
        self.M_tot = 0.0

    class Cell:
        def __init__(self, index):
            self.index = index
            self.T = 293.15
            self.h = 0.0
            self.rho = 1000
            self.p = 101325
            self.qdot = 0.0
            self.hnode_su = 0.0
            self.hnode_ex = 0.0

    class SummaryClass:
        def __init__(self, n, T, h, hnode, rho, Mdot, p):
            self.n = n
            self.T = T
            self.h = h
            self.hnode = hnode
            self.rho = rho
            self.Mdot = Mdot
            self.p = p

    def specific_enthalpy(self, p, T):
        """
        Approximate specific enthalpy of water as function of pressure and temperature.
        This is a placeholder for a real thermodynamic library.
        """
        Cp = 4186  # J/kg.K (approx. specific heat of water)
        return Cp * (T - 273.15)

    def compute_total_heat_flow(self):
        qdots = np.array([cell.qdot for cell in self.Cells])
        self.Q_tot = self.A / self.N * np.sum(qdots) * self.Nt

    def compute_total_mass(self):
        rhos = np.array([cell.rho for cell in self.Cells])
        self.M_tot = self.V / self.N * np.sum(rhos)

    def update_summary(self):
        self.Summary.T = np.array([cell.T for cell in self.Cells])
        self.Summary.h = np.array([cell.h for cell in self.Cells])
        self.Summary.hnode[:-1] = np.array([cell.hnode_su for cell in self.Cells])
        self.Summary.hnode[-1] = self.Cells[-1].hnode_ex
        self.Summary.rho = np.array([cell.rho for cell in self.Cells])
        self.Summary.p = self.Cells[0].p  # assuming uniform pressure

    def simulate_step(self):
        self.compute_total_heat_flow()
        self.compute_total_mass()
        self.update_summary()

# 시뮬레이션 실행 코드
if __name__ == "__main__":
    # 시뮬레이션 파라미터
    dt = 10              # 시간 간격 (초)
    T_total = 3600 * 24 * 8  # 8일 시뮬레이션
    steps = T_total // dt
    
    # 모델 생성
    model = Flow1DimInc(
        N=10,                        # 셀 개수
        V=0.03781,                  # 전체 체적 (m³)
        A=16.18,                    # 열교환 면적 (m²)
        Mdotnom=0.2588,             # 유량 (kg/s)
        Unom=1000,                  # 열전달 계수 (W/m²·K)
        pstart=101325,              # 초기 압력 (Pa)
        Tstart_inlet=293.15,        # 입구 온도 시작값 (K)
        Tstart_outlet=313.15        # 출구 온도 시작값 (K)
    )
    
    # 결과 저장
    T_profile = []
    h_profile = []
    time_points = []
    
    # 시간 루프
    for step in range(steps):
        model.simulate_step()
        
        # 결과 저장
        T_profile.append(model.Summary.T.copy())
        h_profile.append(model.Summary.h.copy())
        time_points.append(step * dt / 3600)  # 시간을 시간 단위로 변환
        
        # 진행상황 출력 (10% 간격)
        if step % (steps // 10) == 0:
            print(f"시뮬레이션 진행률: {step/steps*100:.1f}%")
    
    # 결과 시각화
    plt.figure(figsize=(12, 6))
    
    # 온도 프로파일
    plt.subplot(1, 2, 1)
    for i in range(model.N):
        T_cell = [T[i] for T in T_profile]
        plt.plot(time_points, T_cell, label=f'Cell {i+1}')
    plt.xlabel('Time (hours)')
    plt.ylabel('Temperature (K)')
    plt.title('Temperature Profile')
    plt.grid(True)
    plt.legend()
    
    # 엔탈피 프로파일
    plt.subplot(1, 2, 2)
    for i in range(model.N):
        h_cell = [h[i] for h in h_profile]
        plt.plot(time_points, h_cell, label=f'Cell {i+1}')
    plt.xlabel('Time (hours)')
    plt.ylabel('Enthalpy (J/kg)')
    plt.title('Enthalpy Profile')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.show()

