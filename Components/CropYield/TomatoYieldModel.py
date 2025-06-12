import os
import numpy as np
from scipy.integrate import odeint


class TomatoYieldModel:
    def __init__(
        self,
        n_dev=50,
        LAI_MAX=3.5,
        LAI_0=0.4,
        T_canSumC_0=0,
        C_Leaf_0=15e3,
        C_Stem_0=15e3,
        T_canK=293.15,
        CO2_air=600,
        R_PAR_can=460
    ):
        # Model parameters
        self.n_dev = n_dev
        self.LAI_MAX = LAI_MAX
        self.R_PAR_can = R_PAR_can
        self.CO2_air = CO2_air
        self.T_canK = T_canK

        # Initial states
        self.C_Buf = 5000.0  # 버퍼를 적당히 설정
        self.C_Leaf = C_Leaf_0
        self.C_Stem = C_Stem_0
        self.C_Fruit = np.zeros(n_dev)
        self.N_Fruit = np.zeros(n_dev)
        self.T_can24C = 20.0
        self.T_canSumC = T_canSumC_0
        self.DM_Har = 0.0
        self.W_Fruit_1_Pot = 10.0

        # SLA 설정
        self.SLA = LAI_0 / C_Leaf_0
        self.LAI = LAI_0

        # Plant density
        self.n_plants = 2.5

        # Physical constants
        self.M_CH2O = 30e-3
        self.M_CO2 = 44e-3
        self.alpha = 0.385
        self.theta = 0.7
        self.E_j = 37e3
        self.H = 22e4
        self.T_25K = 298.15
        self.Rg = 8.314
        self.S = 710
        self.J_25Leaf_MAX = 210
        self.eta_CO2airStom = 0.67
        self.c_Gamma = 1.7

        # Buffer parameters - 원본 Modelica 값 사용
        self.C_Buf_MAX = 20e3
        self.C_Buf_MIN = 1e3

        # Temperature limits - 원본 Modelica 값 사용
        self.T_can_MIN = 10
        self.T_can_MAX = 34
        self.T_can24_MIN = 15
        self.T_can24_MAX = 24.5
        self.T_endSumC = 1035

        # Growth rates
        self.rg_Fruit = 0.328
        self.rg_Leaf = 0.095
        self.rg_Stem = 0.074

        # Fruit set parameters
        self.r_BufFruit_MAXFrtSet = 0.05
        self.c_BufFruit_1_MAX = -1.71e-7
        self.c_BufFruit_2_MAX = 7.31e-7

        # Development parameters
        self.c_dev_1 = -7.64e-9
        self.c_dev_2 = 1.16e-8
        self.G_MAX = 1e4

        # Respiration coefficients
        self.c_Fruit_g = 0.27
        self.c_Leaf_g = 0.28
        self.c_Stem_g = 0.3
        self.c_Fruit_m = 1.16e-7
        self.c_Leaf_m = 3.47e-7
        self.c_Stem_m = 1.47e-7
        self.Q_10_m = 2.0
        self.c_RGR = 2.85e6

        # Other parameters
        self.eta_C_DM = 1.0
        self.tau = 86400.0
        self.k = 1.0

    @staticmethod
    def _safe_sigmoid(x, scale=1.0):
        """Safe sigmoid function"""
        return 1.0 / (1.0 + np.exp(-np.clip(x * scale, -700, 700)))

    def set_environmental_conditions(self, R_PAR_can=None, CO2_air=None, T_canK=None):
        """Update environmental conditions"""
        if R_PAR_can is not None: 
            self.R_PAR_can = max(0, R_PAR_can)
        if CO2_air is not None: 
            self.CO2_air = max(430, CO2_air)
        if T_canK is not None: 
            self.T_canK = max(273.15, T_canK)

    def calculate_plant_density(self, t):
        """Plant density increases over time"""
        if t < 2678400:  # First month
            return 2.5
        elif t < 5356800:  # Second month  
            progress = (t - 2678400) / (5356800 - 2678400)
            return 2.5 + progress * 1.0
        else:
            return 3.5

    def calculate_fruit_growth_rates(self, r_dev):
        """Calculate growth rates for each development stage"""
        if r_dev <= 1e-12:
            return np.ones(self.n_dev) * 0.1
        
        FGP = max(1.0, 1.0 / (r_dev * 86400))
        M = max(1.0, -4.93 + 0.548 * FGP)
        B = max(0.01, 1.0 / (2.44 + 0.403 * M))
        
        GR = np.zeros(self.n_dev)
        for j in range(self.n_dev):
            t_j_FGP = ((j) + 0.5) / self.n_dev * FGP
            exp_arg = np.clip(-B * (t_j_FGP - M), -700, 700)
            inner_exp = np.clip(-np.exp(exp_arg), -700, 700)
            GR[j] = self.G_MAX * np.exp(inner_exp) * B * np.exp(exp_arg)
        
        return np.maximum(GR, 0.01)

    def calculate_derivatives(self, y, t):
        """Calculate derivatives for all state variables"""
        try:
            # Unpack state vector
            C_Buf = max(0, y[0])
            C_Leaf = max(0, y[1]) 
            C_Stem = max(0, y[2])
            C_Fruit = np.maximum(0, y[3:3+self.n_dev])
            N_Fruit = np.maximum(0, y[3+self.n_dev:3+2*self.n_dev])
            T_can24C = y[3+2*self.n_dev]
            T_canSumC = max(0, y[3+2*self.n_dev+1])
            W_Fruit_1_Pot = max(0, y[3+2*self.n_dev+2])
            DM_Har = max(0, y[3+2*self.n_dev+3])

            # Temperature
            T_canC = self.T_canK - 273.15

            # Update LAI
            LAI = max(0.01, self.SLA * C_Leaf)

            # Plant density
            n_plants = self.calculate_plant_density(t)

            # === PHOTOSYNTHESIS ===
            CO2_stom = self.eta_CO2airStom * self.CO2_air
            J_25Can_MAX = LAI * self.J_25Leaf_MAX
            
            # CO2 compensation point
            if J_25Can_MAX > 1e-6:
                Gamma = (self.J_25Leaf_MAX / J_25Can_MAX) * self.c_Gamma * T_canC + \
                       20 * self.c_Gamma * (1 - self.J_25Leaf_MAX / J_25Can_MAX)
            else:
                Gamma = 20 * self.c_Gamma

            # Electron transport
            exp_arg1 = np.clip(self.E_j * (self.T_canK - self.T_25K) / (self.Rg * self.T_canK * self.T_25K), -50, 50)
            exp_arg2 = np.clip((self.S * self.T_25K - self.H) / (self.Rg * self.T_25K), -50, 50)
            exp_arg3 = np.clip((self.S * self.T_canK - self.H) / (self.Rg * self.T_canK), -50, 50)
            
            J_POT = J_25Can_MAX * np.exp(exp_arg1) * (1 + np.exp(exp_arg2)) / (1 + np.exp(exp_arg3))
            
            # Electron transport rate J
            if self.R_PAR_can > 0 and J_POT > 0:
                discriminant = (J_POT + self.alpha * self.R_PAR_can)**2 - 4 * self.theta * J_POT * self.alpha * self.R_PAR_can
                discriminant = max(0, discriminant)
                J = (J_POT + self.alpha * self.R_PAR_can - np.sqrt(discriminant)) / (2 * self.theta)
            else:
                J = 0

            # Photosynthesis and photorespiration
            if CO2_stom + 2 * Gamma > 0 and J > 0:
                P = J / 4 * (CO2_stom - Gamma) / (CO2_stom + 2 * Gamma)
                R = P * Gamma / CO2_stom if CO2_stom > 0 else 0
            else:
                P = R = 0

            # Net photosynthesis
            h_CBuf_MCairBuf = self._safe_sigmoid(C_Buf - self.C_Buf_MAX, -5e-3)
            MC_AirBuf = self.M_CH2O * h_CBuf_MCairBuf * max(0, P - R)

            # === GROWTH FLOWS (핵심 수정) ===
            
            # 원본 Modelica 코드의 정확한 억제 함수들
            # h_CBuf_MCBufOrg = 1/(1+exp(-5e-2*(C_Buf-C_Buf_MIN)))
            h_CBuf_MCBufOrg = self._safe_sigmoid(C_Buf - self.C_Buf_MIN, 5e-2)  # 부호 변경!
            
            # h_Tcan = 1/(1+exp(-0.869*(T_canC-T_can_MIN))) * 1/(1+exp(0.5793*(T_canC-T_can_MAX)))
            h_Tcan = self._safe_sigmoid(T_canC - self.T_can_MIN, 0.869) * \
                     self._safe_sigmoid(self.T_can_MAX - T_canC, 0.5793)
            
            # h_Tcan24 = 1/(1+exp(-1.1587*(T_can24C-T_can24_MIN))) * 1/(1+exp(1.3904*(T_can24C-T_can24_MAX)))
            h_Tcan24 = self._safe_sigmoid(T_can24C - self.T_can24_MIN, 1.1587) * \
                       self._safe_sigmoid(self.T_can24_MAX - T_can24C, 1.3904)
            
            # Generative phase - 원본 Modelica 구현
            if self.T_endSumC > 0:
                ratio = T_canSumC / self.T_endSumC
                term1 = ratio + np.sqrt(ratio**2 + 1e-4)
                term2 = (ratio - 1) + np.sqrt((ratio - 1)**2 + 1e-4)
                h_TcanSum = 0.5 * term1 - 0.5 * term2
                h_TcanSum = max(0, min(1, h_TcanSum))  # 0-1 범위로 제한
            else:
                h_TcanSum = 0

            # g_Tcan24 = 0.047*T_can24C + 0.06
            g_Tcan24 = 0.047 * T_can24C + 0.06

            # Growth flows
            MC_BufFruit = h_CBuf_MCBufOrg * h_Tcan * h_Tcan24 * h_TcanSum * g_Tcan24 * self.rg_Fruit
            MC_BufLeaf = h_CBuf_MCBufOrg * h_Tcan24 * g_Tcan24 * self.rg_Leaf
            MC_BufStem = h_CBuf_MCBufOrg * h_Tcan24 * g_Tcan24 * self.rg_Stem

            # === FRUIT DEVELOPMENT ===
            r_dev = max(1e-12, self.c_dev_1 + self.c_dev_2 * T_can24C)
            
            # Fruit set
            MN_BufFruit_1_MAX = max(0, n_plants * (self.c_BufFruit_1_MAX + self.c_BufFruit_2_MAX * T_can24C))
            MN_BufFruit_1 = self._safe_sigmoid(MC_BufFruit - self.r_BufFruit_MAXFrtSet, 58.9) * MN_BufFruit_1_MAX
            
            # Growth rates
            GR = self.calculate_fruit_growth_rates(r_dev)
            
            # First stage carbohydrate flow
            MC_BufFruit_1 = W_Fruit_1_Pot * MN_BufFruit_1

            # Development flows
            h_T_canSum_MN_Fruit = self._safe_sigmoid(T_canSumC, 5e-2)  # 부호 변경!

            # === RESPIRATION ===
            MC_FruitAir_g = self.c_Fruit_g * MC_BufFruit
            MC_LeafAir_g = self.c_Leaf_g * MC_BufLeaf  
            MC_StemAir_g = self.c_Stem_g * MC_BufStem
            MC_BufAir = MC_FruitAir_g + MC_LeafAir_g + MC_StemAir_g

            # Maintenance respiration
            Q10_factor = self.Q_10_m ** (0.1 * (T_can24C - 25))
            
            # Individual fruit maintenance respiration
            MC_FruitAir_j = np.zeros(self.n_dev)
            for j in range(self.n_dev):
                if GR[j] > 0 and self.G_MAX > 0:
                    RGR_Fruit_j = GR[j] / self.G_MAX / 86400
                    MC_FruitAir_j[j] = self.c_Fruit_m * Q10_factor * C_Fruit[j] * \
                                      (1 - np.exp(-self.c_RGR * RGR_Fruit_j))

            MC_FruitAir = np.sum(MC_FruitAir_j)
            
            # Leaf and stem maintenance
            RGR_Leaf = self.rg_Leaf / max(1e-6, C_Leaf)
            RGR_Stem = self.rg_Stem / max(1e-6, C_Stem)
            
            MC_LeafAir = self.c_Leaf_m * Q10_factor * C_Leaf * (1 - np.exp(-self.c_RGR * RGR_Leaf))
            MC_StemAir = self.c_Stem_m * Q10_factor * C_Stem * (1 - np.exp(-self.c_RGR * RGR_Stem))

            # === HARVEST CALCULATION ===
            MC_FruitHar = max(0, r_dev * self.n_dev * C_Fruit[-1])

            # === LEAF PRUNING ===
            C_Leaf_MAX = self.LAI_MAX / self.SLA
            if C_Leaf > C_Leaf_MAX:
                MC_LeafHar = self._safe_sigmoid(C_Leaf - C_Leaf_MAX, 5e-5) * (C_Leaf - C_Leaf_MAX)
            else:
                MC_LeafHar = 0

            # === DERIVATIVES ===
            
            # Buffer
            dC_Buf = MC_AirBuf - MC_BufFruit - MC_BufLeaf - MC_BufStem - MC_BufAir

            # Organs
            dC_Leaf = MC_BufLeaf - MC_LeafAir - MC_LeafHar
            dC_Stem = MC_BufStem - MC_StemAir

            # Fruit derivatives
            dC_Fruit = np.zeros(self.n_dev)
            
            # First stage
            dC_Fruit[0] = MC_BufFruit_1 - MC_FruitAir_j[0]
            if self.n_dev > 1:
                dC_Fruit[0] -= r_dev * self.n_dev * C_Fruit[0]

            # Middle stages
            for j in range(1, self.n_dev-1):
                inflow = r_dev * self.n_dev * C_Fruit[j-1]
                outflow = r_dev * self.n_dev * C_Fruit[j] + MC_FruitAir_j[j]
                dC_Fruit[j] = inflow - outflow

            # Last stage (includes harvest)
            if self.n_dev > 1:
                inflow = r_dev * self.n_dev * C_Fruit[-2]
                outflow = MC_FruitHar + MC_FruitAir_j[-1]
                dC_Fruit[-1] = inflow - outflow

            # Fruit numbers
            dN_Fruit = np.zeros(self.n_dev)
            dN_Fruit[0] = MN_BufFruit_1 - r_dev * self.n_dev * h_T_canSum_MN_Fruit * N_Fruit[0]
            
            for j in range(1, self.n_dev-1):
                inflow = r_dev * self.n_dev * h_T_canSum_MN_Fruit * N_Fruit[j-1]
                outflow = r_dev * self.n_dev * h_T_canSum_MN_Fruit * N_Fruit[j]
                dN_Fruit[j] = inflow - outflow

            if self.n_dev > 1:
                dN_Fruit[-1] = r_dev * self.n_dev * h_T_canSum_MN_Fruit * N_Fruit[-2]

            # Other derivatives
            dT_can24C = (self.k * T_canC - T_can24C) / self.tau
            dT_canSumC = T_canC / 86400
            dW_Fruit_1_Pot = GR[0] / 86400 if len(GR) > 0 else 0
            dDM_Har = max(0, self.eta_C_DM * MC_FruitHar)

            # # 디버깅 정보 (시뮬레이션 초기에만)
            # if t < 86400 and t % 3600 < 60:  # 매시간마다
            #     print(f"t={t/3600:.1f}h: LAI={LAI:.3f}, MC_BufLeaf={MC_BufLeaf:.6f}, MC_LeafAir={MC_LeafAir:.6f}, dC_Leaf={dC_Leaf:.6f}")
            #     print(f"  h_CBuf={h_CBuf_MCBufOrg:.3f}, h_T24={h_Tcan24:.3f}, g_T24={g_Tcan24:.3f}, MC_AirBuf={MC_AirBuf:.3f}")

            return np.concatenate([
                [dC_Buf, dC_Leaf, dC_Stem],
                dC_Fruit,
                dN_Fruit, 
                [dT_can24C, dT_canSumC, dW_Fruit_1_Pot, dDM_Har]
            ])

        except Exception as e:
            print(f"Error in derivatives calculation: {e}")
            return np.zeros_like(y)

    def simulate(self, csv_file=None, duration_days=100):
        """Run simulation"""
        print(f"Starting simulation for {duration_days} days...")
        print(f"Initial LAI: {self.LAI}")
        print(f"SLA: {self.SLA}")
        print(f"Initial C_Leaf: {self.C_Leaf}")
        print(f"Initial C_Buf: {self.C_Buf}")
        
        # Time vector
        t = np.linspace(0, duration_days * 86400, duration_days * 24)
        
        # Initial state
        y0 = np.concatenate([
            [self.C_Buf, self.C_Leaf, self.C_Stem],
            self.C_Fruit,
            self.N_Fruit,
            [self.T_can24C, self.T_canSumC, self.W_Fruit_1_Pot, self.DM_Har]
        ])

        try:
            sol = odeint(self.calculate_derivatives, y0, t, 
                        rtol=1e-8, atol=1e-10, mxstep=5000)
            print("Integration successful")
                
            # Extract final state
            final = sol[-1]
            self.C_Buf = max(0, final[0])
            self.C_Leaf = max(0, final[1])
            self.C_Stem = max(0, final[2])
            self.C_Fruit = np.maximum(0, final[3:3+self.n_dev])
            self.N_Fruit = np.maximum(0, final[3+self.n_dev:3+2*self.n_dev])
            idx = 3 + 2*self.n_dev
            self.T_can24C = final[idx]
            self.T_canSumC = max(0, final[idx+1])
            self.W_Fruit_1_Pot = max(0, final[idx+2])
            self.DM_Har = max(0, final[idx+3])
            
            self.LAI = self.SLA * self.C_Leaf

            return {
                'C_Buf': float(self.C_Buf),
                'C_Leaf': float(self.C_Leaf), 
                'C_Stem': float(self.C_Stem),
                'LAI': float(self.LAI),
                'Fruit_C_total': float(np.sum(self.C_Fruit)),
                'Fruit_N_total': float(np.sum(self.N_Fruit)),
                'T_can24C': float(self.T_can24C),
                'T_canSumC': float(self.T_canSumC),
                'W_Fruit_1_Pot': float(self.W_Fruit_1_Pot),
                'DM_Har': float(self.DM_Har),
                'simulation_data': sol
            }
            
        except Exception as e:
            print(f"Integration failed: {e}")
            return None

    def step(self, dt, R_PAR_can=None, CO2_air=None, T_canK=None):
        """Single time step"""
        self.set_environmental_conditions(R_PAR_can, CO2_air, T_canK)
        
        y = np.concatenate([
            [self.C_Buf, self.C_Leaf, self.C_Stem],
            self.C_Fruit,
            self.N_Fruit,
            [self.T_can24C, self.T_canSumC, self.W_Fruit_1_Pot, self.DM_Har]
        ])
        
        dy = self.calculate_derivatives(y, 0)
        
        self.C_Buf = max(0, self.C_Buf + dy[0] * dt)
        self.C_Leaf = max(0, self.C_Leaf + dy[1] * dt)
        self.C_Stem = max(0, self.C_Stem + dy[2] * dt)
        self.C_Fruit = np.maximum(0, self.C_Fruit + dy[3:3+self.n_dev] * dt)
        self.N_Fruit = np.maximum(0, self.N_Fruit + dy[3+self.n_dev:3+2*self.n_dev] * dt)
        
        idx = 3 + 2*self.n_dev
        self.T_can24C += dy[idx] * dt
        self.T_canSumC = max(0, self.T_canSumC + dy[idx+1] * dt)
        self.W_Fruit_1_Pot = max(0, self.W_Fruit_1_Pot + dy[idx+2] * dt)
        self.DM_Har = max(0, self.DM_Har + dy[idx+3] * dt)
        
        self.LAI = self.SLA * self.C_Leaf
