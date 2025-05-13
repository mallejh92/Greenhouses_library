import numpy as np
from BasicComponents.AirVP import AirVP  # Import AirVP class
import matplotlib.pyplot as plt

class Air:
    """
    Python version of the Modelica Greenhouses.Components.Greenhouse.Air model.
    This class models energy and moisture balance in the greenhouse air zone.
    """
    def __init__(self, A, h_Air=4.0, rho=1.2, c_p=1000.0, T_start=298.0, N_rad=2, steadystate=False, steadystateVP=True):
        # Parameters
        self.A = A                          # Greenhouse floor area [m²]
        self.h_Air = h_Air                  # Height of the air zone [m]
        self.rho = rho                      # Air density [kg/m³]
        self.c_p = c_p                      # Specific heat capacity [J/kg·K]
        self.N_rad = N_rad                  # Number of radiation sources
        self.P_atm = 101325.0               # Atmospheric pressure [Pa]
        self.R_a = 287.0                    # Gas constant for dry air [J/(kg·K)]
        self.R_s = 461.5                    # Specific gas constant for water vapor

        # Initial state
        self.T = T_start                    # Temperature [K]
        self.V = self.A * self.h_Air        # Volume [m³]
        self.Q_flow = 0.0                   # Sensible heat flow rate [W]
        self.R_Air_Glob = np.zeros(N_rad)   # Shortwave radiation inputs [W/m²]

        # Vapor pressure related
        self.massPort_VP = 0.0              # Vapor pressure input [Pa]
        self.w_air = 0.0                    # Humidity ratio [kg water / kg dry air]
        self.RH = 0.0                       # Relative humidity [0-1]

        # Options
        self.steadystate = steadystate
        self.steadystateVP = steadystateVP

        # Add AirVP component
        self.airVP = AirVP(V_air=self.V, steadystate=steadystateVP)

    def compute_power_input(self):
        return np.sum(self.R_Air_Glob) * self.A  # W

    def compute_derivatives(self):
        """
        Compute the time derivative of temperature (dT/dt).
        """
        if self.steadystate:
            dTdt = 0.0
        else:
            P_Air = self.compute_power_input()
            dTdt = (self.Q_flow + P_Air) / (self.rho * self.c_p * self.V)
        return dTdt

    def update_humidity(self):
        """
        Compute humidity ratio and relative humidity.
        """
        if self.steadystateVP:
            return  # RH remains unchanged
        
        # Update vapor pressure through AirVP component
        self.airVP.update(self.massPort_VP)
        VP = self.airVP.VP
        
        self.w_air = VP * self.R_a / ((self.P_atm - VP) * self.R_s)
        # RH is computed with a placeholder formula (as in Modelica.Media.Air.MoistAir.relativeHumidity_pTX)
        T_C = self.T - 273.15
        Psat = 610.78 * np.exp(T_C / (T_C + 238.3) * 17.2694)  # Tetens formula
        self.RH = VP / Psat
        self.RH = np.clip(self.RH, 0, 1)

    def step(self, dt):
        """
        Advance the model state by dt seconds.
        """
        dTdt = self.compute_derivatives()
        self.T += dTdt * dt
        self.update_humidity()
        return self.T, self.RH

    def set_inputs(self, Q_flow, R_Air_Glob, massPort_VP):
        self.Q_flow = Q_flow
        # Initialize R_Air_Glob to zeros if None or empty
        if R_Air_Glob is None or len(R_Air_Glob) == 0:
            self.R_Air_Glob = np.zeros(self.N_rad)
        else:
            self.R_Air_Glob = np.array(R_Air_Glob)
        self.massPort_VP = massPort_VP

def simulate_greenhouse_air():
    # Create greenhouse air model
    A = 1000  # Greenhouse floor area [m²]
    air = Air(A=A, h_Air=4.0, T_start=298.0)  # 25°C initial temperature

    # Simulation parameters
    dt = 60  # Time step [s]
    sim_time = 24 * 3600  # 24 hours simulation
    n_steps = int(sim_time / dt)

    # Storage for results
    times = np.linspace(0, sim_time/3600, n_steps)  # Time in hours
    temperatures = np.zeros(n_steps)
    humidities = np.zeros(n_steps)

    # Simulation loop
    for i in range(n_steps):
        # Simulate day/night cycle for radiation
        hour = times[i]
        if 6 <= hour <= 18:  # Daytime
            R_Air_Glob = [800, 200]  # [Sun radiation, artificial lighting] [W/m²]
        else:  # Nighttime
            R_Air_Glob = [0, 100]    # Only artificial lighting at night

        # Set inputs
        Q_flow = 1000  # Constant heat flow [W]
        massPort_VP = 2000  # Constant vapor pressure [Pa]

        # Update model
        air.set_inputs(Q_flow, R_Air_Glob, massPort_VP)
        T, RH = air.step(dt)

        # Store results
        temperatures[i] = T - 273.15  # Convert to Celsius
        humidities[i] = RH * 100      # Convert to percentage

    # Plot results
    plt.figure(figsize=(12, 6))
    
    # Temperature plot
    plt.subplot(2, 1, 1)
    plt.plot(times, temperatures)
    plt.grid(True)
    plt.xlabel('Time [hours]')
    plt.ylabel('Temperature [°C]')
    plt.title('Greenhouse Air Temperature')

    # Humidity plot
    plt.subplot(2, 1, 2)
    plt.plot(times, humidities)
    plt.grid(True)
    plt.xlabel('Time [hours]')
    plt.ylabel('Relative Humidity [%]')
    plt.title('Greenhouse Air Humidity')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    simulate_greenhouse_air()