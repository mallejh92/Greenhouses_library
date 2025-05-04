# main.py

import matplotlib.pyplot as plt
from Components.greenhouse import GreenhouseClimateModel

def main():
    params = {
        "A_glass": 100.0,
        "C_air": 1.0e5,
        "Q_loss": 500.0
    }
    initial_temp = [20.0]
    t_span = (0, 180)

    model = GreenhouseClimateModel(params)
    t, y = model.simulate(t_span, initial_temp)

    plot_temperature(t, y[0])

def plot_temperature(t, T):
    plt.plot(t, T, label="Indoor Temperature")
    plt.xlabel("Time [h]")
    plt.ylabel("Temperature [°C]")
    plt.title("Greenhouse Air Temperature (Autonomous)")
    plt.grid()
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
