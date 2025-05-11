import numpy as np
from scipy.integrate import odeint

class TomatoYieldModel:
    def __init__(self, n_dev=50):
        #***************** Parameters *******************//
        self.n_dev = n_dev  # "Number of fruit development stages"
        self.LAI_MAX = 3.5  # "Maximum leaf area index, m2 leaf/m2 greenhouse"
        
        #***************** Varying inputs *******************//
        self.R_PAR_can = 460  # "Total PAR absorbed by the canopy, umol/(s.m2)"
        self.CO2_air = 600    # "CO2 concentration of the greenhouse air, umol CO2/mol air"
        self.T_canK = 293.15  # "Instantaneous canopy temperature, K"
        
        #***************** Constant parameters characteristic of the plant ***************************//
        self.C_Buf_MAX = 20e3  # "Maximum buffer capacity, mg/m2"
        self.C_Buf_MIN = 1e3   # "Minimum amount of carbohydrates in the buffer, mg/m2"
        
        #***************** Initialization parameters *******************//
        self.LAI_0 = 0.4       # "Initial leaf area index"
        self.T_canSumC_0 = 0   # "Initial temperature sum"
        self.C_Leaf_0 = 15e3   # "Initial carbohydrate weight of leaves, mg/m2"
        self.C_Stem_0 = 15e3   # "Initial carbohydrate weight of stems and roots, mg/m2"
        self.n_plants = 2.5    # "Number of plants per square meter"
        
        #***************** Protected parameters *********************/
        self.M_CH2O = 30e-3    # "Molar mass of CH2O, mg/umol"
        self.M_CO2 = 44e-3     # "Molar mass of CO2, mg/umol"
        self.alpha = 0.385     # "Conversion factor from photons to electrons"
        self.theta = 0.7       # "Degree of curvature of the electron transport rate"
        self.E_j = 37e3        # "Activation energy for J_POT, J/mol"
        self.H = 22e4          # "Deactivation energy, J/mol"
        self.T_25K = 298.15    # "Reference temperature at 25ºC, K"
        self.Rg = 8.314        # "Molar gas constant, J/(mol.K)"
        self.S = 710           # "Entropy term, J/(mol.K)"
        self.J_25Leaf_MAX = 210  # "Maximum rate of electron transport at 25ºC for the leaf"
        self.eta_CO2airStom = 0.67  # "Conversion factor from the CO2 concentration"
        self.c_Gamma = 1.7     # "Effect of canopy temperature on CO2 compensation point"
        
        # Temperature parameters
        self.T_can_MIN = 10    # "Minimum canopy temperature, degC"
        self.T_can_MAX = 34    # "Maximum canopy temperature, degC"
        self.T_can24_MIN = 15  # "Minimum 24h mean temperature, degC"
        self.T_can24_MAX = 24.5  # "Maximum 24h mean temperature, degC"
        self.T_endSumC = 1035  # "Temperature sum for full potential growth"
        
        # Growth parameters
        self.rg_Fruit = 0.328  # "Potential fruit growth rate coefficient at 20ºC"
        self.rg_Leaf = 0.095   # "Potential leaf growth rate coefficient at 20ºC"
        self.rg_Stem = 0.074   # "Potential stem growth rate coefficient at 20ºC"
        
        # Fruit development parameters
        self.r_BufFruit_MAXFrtSet = 0.05  # "Maximal fruit set threshold"
        self.c_BufFruit_1_MAX = -1.71e-7  # "Regression coefficient"
        self.c_BufFruit_2_MAX = 7.31e-7   # "Regression coefficient"
        self.c_dev_1 = -7.64e-9  # "Regression coefficient"
        self.c_dev_2 = 1.16e-8   # "Regression coefficient"
        self.G_MAX = 1e4        # "Potential fruit weight, mg"
        
        # Respiration parameters
        self.c_Fruit_g = 0.27   # "Growth respiration coefficient of fruit"
        self.c_Leaf_g = 0.28    # "Growth respiration coefficient of leaf"
        self.c_Stem_g = 0.3     # "Growth respiration coefficient of stem"
        self.c_Fruit_m = 1.16e-7  # "Maintenance respiration coefficient of fruit"
        self.c_Leaf_m = 3.47e-7   # "Maintenance respiration coefficient of leaf"
        self.c_Stem_m = 1.47e-7   # "Maintenance respiration coefficient of stem"
        self.Q_10_m = 2          # "Q_10 value for temperature effect"
        self.c_RGR = 2.85e6      # "Regression coefficient for maintenance respiration"
        
        # Other parameters
        self.SLA = 2.66e-5      # "Specific leaf area index, m2/mg"
        self.eta_C_DM = 1       # "Conversion factor from carbohydrate to dry matter"
        self.tau = 86400        # "Time constant for 24h mean temperature"
        self.k = 1              # "Gain for 24h mean temperature"
        
        # Initialize state variables
        self.initialize_state()
        
    def initialize_state(self):
        # State variables
        self.C_Buf = 0          # "Carbohydrates in the buffer, mg/m2"
        self.C_Leaf = self.C_Leaf_0  # "Carbohydrate weight of leaves, mg/m2"
        self.C_Stem = self.C_Stem_0  # "Carbohydrate weight of stems, mg/m2"
        self.C_Fruit = np.zeros(self.n_dev)  # "Fruit carbohydrates, mg/m2"
        self.N_Fruit = np.zeros(self.n_dev)  # "Number of fruits, 1/m2"
        self.T_can24C = 0       # "24h mean temperature, degC"
        self.T_canSumC = self.T_canSumC_0  # "Temperature sum, degC"
        self.DM_Har = 0         # "Accumulated harvested dry matter, mg/m2"
        self.W_Fruit_1_Pot = 0  # "Potential dry matter per fruit, mg"
        
        # Additional variables
        self.MN_Fruit = np.zeros((self.n_dev-1, self.n_dev))  # "Fruit flow through stages"
        self.MC_Fruit = np.zeros((self.n_dev, self.n_dev+1))  # "Fruit carbohydrate flow"
        self.MC_BufFruit_j = np.zeros(self.n_dev)  # "Buffer to fruit flow"
        self.MC_FruitAir_j = np.zeros(self.n_dev)  # "Fruit maintenance respiration"
        
    def calculate_derivatives(self, t, y):
        # Unpack state variables
        C_Buf, C_Leaf, C_Stem = y[0:3]
        C_Fruit = y[3:3+self.n_dev]
        N_Fruit = y[3+self.n_dev:3+2*self.n_dev]
        T_can24C, T_canSumC = y[3+2*self.n_dev:3+2*self.n_dev+2]
        DM_Har = y[-1]
        
        # Calculate intermediate variables
        T_canC = self.T_canK - 273.15
        LAI = max(0, self.SLA * C_Leaf)
        
        # Photosynthesis calculations
        J_25Can_MAX = LAI * self.J_25Leaf_MAX
        CO2_stom = self.eta_CO2airStom * self.CO2_air
        Gamma = self.J_25Leaf_MAX / (J_25Can_MAX + 1e-6) * self.c_Gamma * T_canC + \
                20 * self.c_Gamma * (1 - self.J_25Leaf_MAX / (J_25Can_MAX + 1e-6))
        
        J_POT = J_25Can_MAX * np.exp(self.E_j * (self.T_canK - self.T_25K) / 
                (self.Rg * self.T_canK * self.T_25K)) * \
                (1 + np.exp((self.S * self.T_25K - self.H) / (self.Rg * self.T_25K))) / \
                (1 + np.exp((self.S * self.T_canK - self.H) / (self.Rg * self.T_canK)))
        
        J = (J_POT + self.alpha * self.R_PAR_can - np.sqrt((J_POT + self.alpha * self.R_PAR_can)**2 - 
             4 * self.theta * J_POT * self.alpha * self.R_PAR_can)) / (2 * self.theta)
        
        P = J / 4 * (CO2_stom - Gamma) / (CO2_stom + 2 * Gamma)
        R = P * Gamma / CO2_stom
        
        # Calculate flows
        h_CBuf_MCairBuf = 1 / (1 + np.exp(5e-3 * (C_Buf - self.C_Buf_MAX)))
        MC_AirBuf = self.M_CH2O * h_CBuf_MCairBuf * (P - R)
        
        h_CBuf_MCBufOrg = 1 / (1 + np.exp(-5e-2 * (C_Buf - self.C_Buf_MIN)))
        h_Tcan24 = 1 / (1 + np.exp(-1.1587 * (T_can24C - 15))) * \
                   1 / (1 + np.exp(1.3904 * (T_can24C - 24.5)))
        g_Tcan24 = 0.047 * T_can24C + 0.06
        h_Tcan = 1 / (1 + np.exp(-0.869 * (T_canC - 10))) * \
                 1 / (1 + np.exp(0.5793 * (T_canC - 34)))
        h_TcanSum = 0.5 * (1 / self.T_endSumC * T_canSumC + 
                          np.sqrt((1 / self.T_endSumC * T_canSumC)**2 + 1e-4)) - \
                    0.5 * (1 / self.T_endSumC * (T_canSumC - self.T_endSumC) + 
                          np.sqrt((1 / self.T_endSumC * (T_canSumC - self.T_endSumC))**2 + 1e-4))
        
        # Calculate carbohydrate flows
        MC_BufFruit = h_CBuf_MCBufOrg * h_Tcan * h_Tcan24 * h_TcanSum * g_Tcan24 * self.rg_Fruit
        MC_BufLeaf = h_CBuf_MCBufOrg * h_Tcan24 * g_Tcan24 * self.rg_Leaf
        MC_BufStem = h_CBuf_MCBufOrg * h_Tcan24 * g_Tcan24 * self.rg_Stem
        
        # Calculate respiration
        MC_FruitAir_g = self.c_Fruit_g * MC_BufFruit
        MC_LeafAir_g = self.c_Leaf_g * MC_BufLeaf
        MC_StemAir_g = self.c_Stem_g * MC_BufStem
        MC_BufAir = MC_FruitAir_g + MC_LeafAir_g + MC_StemAir_g
        
        # Calculate derivatives
        dC_Buf = MC_AirBuf - MC_BufFruit - MC_BufLeaf - MC_BufStem - MC_BufAir
        dC_Leaf = MC_BufLeaf - MC_LeafAir_g
        dC_Stem = MC_BufStem - MC_StemAir_g
        
        # Calculate fruit carbohydrate flows
        MC_BufFruit_j = np.zeros(self.n_dev)
        MC_BufFruit_j[0] = MC_BufFruit * N_Fruit[0] / (np.sum(N_Fruit) + 1e-6)
        for j in range(1, self.n_dev):
            MC_BufFruit_j[j] = MC_BufFruit * N_Fruit[j] / (np.sum(N_Fruit) + 1e-6)
        
        # Calculate fruit maintenance respiration
        MC_FruitAir_m = np.zeros(self.n_dev)
        for j in range(self.n_dev):
            MC_FruitAir_m[j] = self.c_Fruit_m * C_Fruit[j] * self.Q_10_m**((T_canC - 20) / 10)
        
        # Calculate harvest flows
        MC_FruitHar = np.zeros(self.n_dev)
        for j in range(self.n_dev):
            if C_Fruit[j] >= self.G_MAX * N_Fruit[j]:
                MC_FruitHar[j] = C_Fruit[j] / (1 + np.exp(-5e-5 * (C_Fruit[j] - self.G_MAX * N_Fruit[j])))
        
        MC_LeafHar = 0
        C_Leaf_MAX = self.LAI_MAX / self.SLA
        if C_Leaf > C_Leaf_MAX:
            MC_LeafHar = 1 / (1 + np.exp(-5e-5 * (C_Leaf - C_Leaf_MAX))) * (C_Leaf - C_Leaf_MAX)
        
        # Update leaf and fruit derivatives with harvest
        dC_Leaf -= MC_LeafHar
        dC_Fruit = np.zeros(self.n_dev)
        dC_Fruit[0] = MC_BufFruit_j[0] - MC_FruitAir_m[0] - MC_FruitHar[0]
        for j in range(1, self.n_dev):
            dC_Fruit[j] = MC_BufFruit_j[j] - MC_FruitAir_m[j] - MC_FruitHar[j]
        
        # Calculate harvested dry matter
        dDM_Har = np.sum(MC_FruitHar) + MC_LeafHar
        
        # Fruit development calculations
        r_dev = self.c_dev_1 + self.c_dev_2 * T_can24C
        MN_BufFruit_1_MAX = self.n_plants * (self.c_BufFruit_1_MAX + self.c_BufFruit_2_MAX * T_can24C)
        MN_BufFruit_1 = 1 / (1 + np.exp(-58.9 * (MC_BufFruit - self.r_BufFruit_MAXFrtSet))) * MN_BufFruit_1_MAX
        
        dN_Fruit = np.zeros(self.n_dev)
        dN_Fruit[0] = MN_BufFruit_1 - self.MN_Fruit[0,1]
        for j in range(1, self.n_dev-1):
            dN_Fruit[j] = self.MN_Fruit[j-1,j] - self.MN_Fruit[j,j+1]
        dN_Fruit[-1] = self.MN_Fruit[-2,-1]
        
        # Update MN_Fruit matrix
        MN_Fruit = np.zeros((self.n_dev-1, self.n_dev))
        for j in range(self.n_dev-1):
            MN_Fruit[j,j+1] = r_dev * self.n_dev * N_Fruit[j]
        
        # Temperature derivatives
        dT_can24C = 1/self.tau * (self.k * T_canC - T_can24C)
        dT_canSumC = 1/86400 * T_canC
        
        # Combine all derivatives
        derivatives = np.concatenate([
            [dC_Buf, dC_Leaf, dC_Stem],
            dC_Fruit,
            dN_Fruit,
            [dT_can24C, dT_canSumC],
            [dDM_Har]
        ])
        
        return derivatives
    
    def simulate(self, days=10):
        # Initial conditions
        y0 = np.concatenate([
            [self.C_Buf, self.C_Leaf, self.C_Stem],
            self.C_Fruit,
            self.N_Fruit,
            [self.T_can24C, self.T_canSumC],
            [self.DM_Har]
        ]).astype(float)  # Ensure all values are float
        
        # Time points
        t = np.linspace(0, days*86400, int(days*24))
        
        # Solve ODE
        solution = odeint(self.calculate_derivatives, y0, t, tfirst=True)
        
        # Update state variables
        self.C_Buf, self.C_Leaf, self.C_Stem = solution[-1, 0:3]
        self.C_Fruit = solution[-1, 3:3+self.n_dev]
        self.N_Fruit = solution[-1, 3+self.n_dev:3+2*self.n_dev]
        self.T_can24C, self.T_canSumC = solution[-1, 3+2*self.n_dev:3+2*self.n_dev+2]
        self.DM_Har = solution[-1, -1]
        
        # Format results for better readability
        results = {
            "C_Buf": float(self.C_Buf),
            "C_Leaf": float(self.C_Leaf),
            "C_Stem": float(self.C_Stem),
            "C_Fruit": {
                "total": float(np.sum(self.C_Fruit)),
                "mean": float(np.mean(self.C_Fruit)),
                "max": float(np.max(self.C_Fruit)),
                "min": float(np.min(self.C_Fruit)),
                "non_zero": float(np.sum(self.C_Fruit > 0))
            },
            "N_Fruit": {
                "total": float(np.sum(self.N_Fruit)),
                "mean": float(np.mean(self.N_Fruit)),
                "max": float(np.max(self.N_Fruit)),
                "min": float(np.min(self.N_Fruit)),
                "non_zero": float(np.sum(self.N_Fruit > 0))
            },
            "T_can24C": float(self.T_can24C),
            "T_canSumC": float(self.T_canSumC),
            "DM_Har": float(self.DM_Har)
        }
        
        return results

# Example usage
if __name__ == "__main__":
    model = TomatoYieldModel()
    results = model.simulate(10)
    
    # Print results in a formatted way
    print("\n=== 토마토 생장 모델 시뮬레이션 결과 ===")
    print("\n[탄수화물 저장량 (mg/m²)]")
    print(f"버퍼: {results['C_Buf']:.2f}")
    print(f"잎: {results['C_Leaf']:.2f}")
    print(f"줄기: {results['C_Stem']:.2f}")
    
    print("\n[과실 탄수화물 (mg/m²)]")
    print(f"총량: {results['C_Fruit']['total']:.2f}")
    print(f"평균: {results['C_Fruit']['mean']:.2f}")
    print(f"최대: {results['C_Fruit']['max']:.2f}")
    print(f"최소: {results['C_Fruit']['min']:.2f}")
    print(f"비영과실 수: {results['C_Fruit']['non_zero']:.0f}")
    
    print("\n[과실 수 (개/m²)]")
    print(f"총수: {results['N_Fruit']['total']:.2f}")
    print(f"평균: {results['N_Fruit']['mean']:.2f}")
    print(f"최대: {results['N_Fruit']['max']:.2f}")
    print(f"최소: {results['N_Fruit']['min']:.2f}")
    print(f"비영과실 수: {results['N_Fruit']['non_zero']:.0f}")
    
    print("\n[온도 정보]")
    print(f"24시간 평균 온도: {results['T_can24C']:.2f}°C")
    print(f"온도 적산: {results['T_canSumC']:.2f}°C")
    
    print(f"\n수확된 건물중: {results['DM_Har']:.2f} mg/m²")
 