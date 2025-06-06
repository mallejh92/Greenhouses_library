import numpy as np
import matplotlib.pyplot as plt
from Components.Greenhouse.Floor import Floor
from Components.Greenhouse.Solar_model import Solar_model
from Flows.HeatAndVapourTransfer.Convection_Condensation import Convection_Condensation
from Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_b import HeatPort_b


def test_floor_solar():
    """Simulate floor temperature for 24h with day-night solar cycle."""
    A = 50.0  # floor area [m^2]
    dt = 600  # 10 minute time step [s]
    sim_time = 24 * 3600
    steps = int(sim_time / dt)

    floor = Floor(A=A, T_start=293.15, N_rad=1)
    solar = Solar_model(A=A, I_glob=0)
    conv = Convection_Condensation(phi=0.0, A=A, floor=True)

    air_port = HeatPort_b(T_start=293.15)
    conv.heatPort_a = floor.heatPort
    conv.heatPort_b = air_port

    times = np.linspace(0, sim_time/3600, steps)
    T_floor = np.zeros(steps)

    sunrise = 6 * 3600
    sunset = 18 * 3600
    daylight = sunset - sunrise
    I_max = 800.0

    for i in range(steps):
        t = i * dt
        time_of_day = t % (24 * 3600)
        if sunrise <= time_of_day <= sunset:
            t_day = time_of_day - sunrise
            I_glob = I_max * np.sin(np.pi * t_day / daylight)
        else:
            I_glob = 0.0

        solar.I_glob = I_glob
        solar.step(dt)

        conv.step()
        Q_conv = conv.Q_flow  # positive from floor to air

        floor.set_inputs(Q_flow=-Q_conv, R_Flr_Glob=[solar.R_SunFlr_Glob])
        floor.step(dt)

        conv.heatPort_a.T = floor.T
        T_floor[i] = floor.T - 273.15

    plt.plot(times, T_floor)
    plt.xlabel('Time [h]')
    plt.ylabel('Floor Temperature [C]')
    plt.title('Floor temperature response to sunrise and sunset')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('floor_solar_test.png')
    plt.show()


if __name__ == "__main__":
    test_floor_solar()