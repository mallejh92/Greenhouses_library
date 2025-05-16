from Flows.VapourMassTransfer.MV_AirThroughScreen import MV_AirThroughScreen

# 사용 예시
screen = MV_AirThroughScreen(
    A=100.0,
    input_f_AirTop=False,
    W=2.0,
    K=0.1
)

# 입력값 설정
screen.SC = 0.5
screen.T_a = 298.0
screen.T_b = 293.0

# 내부 포트의 VP 값 설정
screen.port_a.VP = 2000  # Pa
screen.port_b.VP = 1000  # Pa

# 계산
screen.calculate()
print(screen)  # MV_flow가 0이 아니어야 정상