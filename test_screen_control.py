from Flows.FluidFlow.Flow1DimInc import Flow1DimInc
# from Flows.HeatAndVapourTransfer.HeatTransfer.HeatTransfer import HeatTransfer

flow = Flow1DimInc(
    N=10,              # 10개의 셀
    A=16.18,           # 16.18 m² 측면 표면적
    V=0.03781,         # 0.03781 m³ 관 부피
    Mdotnom=0.2588,    # 0.2588 kg/s 정상 유량
    Unom=1000.0,       # 1000 W/(m²·K) 열전달 계수
    pstart=1e5,        # 1 bar 초기 압력
    Tstart_inlet=293.15,   # 20°C 입구 온도
    Tstart_outlet=283.15   # 10°C 출구 온도
)

# Q_tot, M_tot = flow.update(
#     dt=0.1,            # 0.1 s 시간 단계
#     h_in=1.1e5,        # 입구 엔탈피
#     h_out=0.9e5,       # 출구 엔탈피
#     heat_transfer=heat_transfer_model  # 열전달 모델
# )