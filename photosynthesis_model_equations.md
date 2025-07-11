# 토마토 광합성 모델 수식 정리

## 1. 기공 CO₂ 농도 (Stomatal CO₂ Concentration)

```
CO₂_stom = η_CO₂airStom × CO₂_air
```

여기서:
- `CO₂_stom`: 기공 내 CO₂ 농도 [mg/m³]
- `η_CO₂airStom`: 공기에서 기공으로의 CO₂전달 효율 [-]
- `CO₂_air`: 공기 중 CO₂ 농도 [mg/m³]

## 2. 캐노피 최대 전자전달률 (Canopy Maximum Electron Transport Rate)

```
J_25Can_MAX = LAI × J_25Leaf_MAX
```

여기서:
- `J_25Can_MAX`: 25°C에서 캐노피 최대 전자전달률 [μmol/m²/s]
- `LAI`: 엽면적 지수 [m²_leaf/m²_ground]
- `J_25Leaf_MAX`: 25°C에서 잎 단위 최대 전자전달률 [μmol/m²_leaf/s]

## 3. CO₂ 보상점 (CO₂ Compensation Point)

```
Γ = {
    (J_25Leaf_MAX / J_25Can_MAX) × c_Γ × T_canC + 20 × c_Γ × (1 - J_25Leaf_MAX / J_25Can_MAX)  if J_25Can_MAX > 1×10⁻⁶
    20 × c_Γ                                                                                       if J_25Can_MAX ≤ 1×10⁻⁶
}
```

여기서:
- `Γ`: CO₂ 보상점 [mg/m³]
- `c_Γ`: CO₂ 보상점 온도 의존성 계수 [mg/m³/°C]
- `T_canC`: 캐노피 온도 [°C]

## 4. 잠재 전자전달률 (Potential Electron Transport Rate)

```
J_POT = J_25Can_MAX × exp(E_j × (T_canK - T_25K) / (Rg × T_canK × T_25K)) × 
        (1 + exp((S × T_25K - H) / (Rg × T_25K))) / 
        (1 + exp((S × T_canK - H) / (Rg × T_canK)))
```

여기서:
- `J_POT`: 잠재 전자전달률 [μmol/m²/s]
- `E_j`: 전자전달 활성화 에너지 [J/mol]
- `T_canK`: 캐노피 온도 [K]
- `T_25K`: 기준 온도 298.15 [K]
- `Rg`: 기체상수 8.314 [J/mol/K]
- `S`: 엔트로피 항 [J/mol/K]
- `H`: 비활성화 에너지 [J/mol]

## 5. 실제 전자전달률 (Actual Electron Transport Rate)

광 제한 조건에서:

```
J = (J_POT + α × R_PAR_can - √((J_POT + α × R_PAR_can)² - 4θ × J_POT × α × R_PAR_can)) / (2θ)
```

여기서:
- `J`: 실제 전자전달률 [μmol/m²/s]
- `α`: 광 이용 효율 [μmol_e⁻/μmol_photon]
- `R_PAR_can`: 캐노피가 흡수한 PAR [μmol/m²/s]
- `θ`: 광화학 곡선의 곡률 계수 [-]

## 6. 광합성률과 광호흡률 (Photosynthesis and Photorespiration)

```
P = (J/4) × (CO₂_stom - Γ) / (CO₂_stom + 2Γ)
```

```
R = P × Γ / CO₂_stom
```

여기서:
- `P`: 총 광합성률 [mg/m²/s]
- `R`: 광호흡률 [mg/m²/s]

## 7. 순 탄소 동화율 (Net Carbon Assimilation)

```
h_CBuf_MCairBuf = sigmoid(C_Buf - C_Buf_MAX, -5×10⁻³)
```

```
MC_AirBuf = M_CH₂O × h_CBuf_MCairBuf × max(0, P - R)
```

여기서:
- `MC_AirBuf`: 공기에서 탄수화물 버퍼로의 탄소 질량 유량 [kg/s]
- `M_CH₂O`: 탄수화물 몰질량 [kg/mol]
- `h_CBuf_MCairBuf`: 탄수화물 버퍼 제한 함수 [-]
- `C_Buf`: 현재 탄수화물 버퍼량 [kg/m²]
- `C_Buf_MAX`: 최대 탄수화물 버퍼량 [kg/m²]

## 8. 시그모이드 함수 (Sigmoid Function)

```
sigmoid(x, k) = 1 / (1 + exp(-k × x))
```

## 주요 특징

### 8.1 온도 의존성
- 전자전달률은 **Arrhenius 방정식**과 **고온 억제 함수**로 모델링
- CO₂ 보상점은 온도에 **선형 비례**

### 8.2 광 의존성  
- **Michaelis-Menten 형태**의 광포화 곡선
- 초기 기울기는 `α` (광 이용 효율)
- 포화점은 `J_POT` (잠재 전자전달률)

### 8.3 CO₂ 의존성
- **Rubisco 제한** 광합성 (CO₂ 농도에 의존)
- **광호흡**은 CO₂ 농도에 반비례

### 8.4 버퍼 효과
- 탄수화물 축적으로 인한 **제품 억제** 모델링
- 시그모이드 함수로 **부드러운 전환** 구현

이 모델은 **환경 조건**(광, 온도, CO₂)과 **생리적 상태**(LAI, 버퍼량)를 모두 고려하여 실시간으로 광합성률을 계산합니다. 