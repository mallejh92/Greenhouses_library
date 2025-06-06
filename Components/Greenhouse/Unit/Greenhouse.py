from Components.Greenhouse.Air import Air
from Components.Greenhouse.Canopy import Canopy
from Components.Greenhouse.Cover import Cover
from Components.Greenhouse.Floor import Floor
from Components.Greenhouse.HeatingPipe import HeatingPipe
from Components.Greenhouse.ThermalScreen import ThermalScreen
from Components.Greenhouse.Solar_model import Solar_model
from Components.Greenhouse.Air_Top import Air_Top
from Components.Greenhouse.BasicComponents.AirVP import AirVP
from Flows.HeatTransfer.CanopyFreeConvection import CanopyFreeConvection
from Flows.HeatTransfer.FreeConvection import FreeConvection
from Flows.HeatTransfer.Radiation_T4 import Radiation_T4
from ControlSystems.PID import PID
from Components.CropYield.TomatoYieldModel import TomatoYieldModel
from Flows.HeatTransfer.OutsideAirConvection import OutsideAirConvection
from Flows.HeatTransfer.Radiation_N import Radiation_N
from Components.Greenhouse.Illumination import Illumination
from Flows.VapourMassTransfer.MV_CanopyTranspiration import MV_CanopyTranspiration
from Flows.CO2MassTransfer.CO2_Air import CO2_Air
import pandas as pd

class Greenhouse:
    """
    Ready-to-use Venlo-type greenhouse for tomato crop cultivated from 10Dec-22Nov (weather data from TMY)
    """
    def __init__(self):
        # Load weather and setpoint data
        self.weather_df = pd.read_csv("./10Dec-22Nov.txt", delimiter="\t", skiprows=2, header=None)
        self.weather_df.columns = ["time", "T_out", "RH_out", "P_out", "I_glob",
                                   "u_wind", "T_sky", "T_air_sp", "CO2_air_sp", "ilu_sp"]
        
        self.sp_df = pd.read_csv("./SP_10Dec-22Nov.txt", delimiter="\t", skiprows=2, header=None)
        self.sp_df.columns = ["time", "T_sp", "CO2_sp"]
        
        # Convert temperature from Celsius to Kelvin
        self.weather_df["T_out"] = self.weather_df["T_out"] + 273.15
        self.weather_df["T_sky"] = self.weather_df["T_sky"] + 273.15
        self.weather_df["T_air_sp"] = self.weather_df["T_air_sp"] + 273.15
        self.sp_df["T_sp"] = self.sp_df["T_sp"] + 273.15
        
        self.current_step = 0
        
        # Heat flux variables
        self.q_low = 0.0  # Heat flux for lower heating pipe
        self.q_up = 0.0   # Heat flux for upper heating pipe
        self.q_tot = 0.0  # Total heat flux

        # Energy variables
        self.E_th_tot_kWhm2 = 0.0  # Total thermal energy per square meter
        self.E_th_tot = 0.0        # Total thermal energy
        self.E_el_tot_kWhm2 = 0.0  # Total electrical energy per square meter
        self.E_el_tot = 0.0        # Total electrical energy

        # Crop variables
        self.DM_Har = 0.0  # Accumulated harvested tomato dry matter

        # Electrical variables
        self.W_el_illu = 0.0  # Electrical power for illumination

        # Initialize components
        self.cover = Cover(rho=2600, c_p=840, A=14000, steadystate=True, h_cov=1e-3, phi=0.43633231299858)
        self.air = Air(A=14000, steadystate=True, steadystateVP=True, h_Air=3.8)
        self.canopy = Canopy(A=14000, steadystate=True, LAI=1.06)
        self.floor = Floor(rho=1, c_p=2e6, A=14000, V=0.01*14000, steadystate=True)
        
        # Initialize CO2 air component
        self.CO2_air = CO2_Air(cap_CO2=3.8, CO2_start=1940.0, steadystate=True)
        
        # Initialize heat transfer components
        self.Q_rad_CanCov = Radiation_T4(A=14000, epsilon_a=1, epsilon_b=0.84, FFa=self.canopy.FF, FFb=1)
        self.Q_rad_FlrCan = Radiation_T4(A=14000, epsilon_a=0.89, epsilon_b=1, FFa=1, FFb=self.canopy.FF)
        self.Q_cnv_CanAir = CanopyFreeConvection(A=14000, LAI=self.canopy.LAI)
        self.Q_cnv_FlrAir = FreeConvection(phi=0, A=14000, floor=True)
        self.Q_rad_CovSky = Radiation_T4(epsilon_a=0.84, epsilon_b=1, A=14000)
        
        # Initialize heating pipes
        self.pipe_low = HeatingPipe(d=0.051, freePipe=False, A=14000, N=5, N_p=625, l=50)
        self.pipe_up = HeatingPipe(A=14000, freePipe=True, d=0.025, l=44, N=5, N_p=292)
        
        # Initialize thermal screen
        self.thScreen = ThermalScreen(A=14000, SC=0, steadystate=False)
        
        # Initialize air zones
        self.air_Top = Air_Top(steadystate=True, steadystateVP=True, h_Top=0.4, A=14000)
        
        # Initialize solar model
        self.solar_model = Solar_model(A=14000, LAI=self.canopy.LAI, SC=0, I_glob=0)
        
        # Initialize illumination
        self.illu = Illumination(A=14000, power_input=True, P_el=500, p_el=100)
        self.illu.LAI = self.canopy.LAI
        
        # Initialize tomato yield model
        self.TYM = TomatoYieldModel(LAI_0=self.canopy.LAI)
        
        # Initialize control systems
        self.PID_Mdot = PID(PVmin=291.15, PVmax=295.15, PVstart=0.5, CSstart=0.5, 
                           steadyStateInit=False, CSmin=0, Kp=0.7, Ti=600, CSmax=86.75)
        self.PID_CO2 = PID(PVstart=0.5, CSstart=0.5, steadyStateInit=False, 
                          PVmin=708.1, PVmax=1649, CSmin=0, CSmax=1, Kp=0.4, Ti=0.5)

    def step(self, dt):
        """
        Update the greenhouse state for one time step
        
        Args:
            dt (float): Time step in seconds
        """
        # Get current weather and setpoint data
        current_weather = self.weather_df.iloc[self.current_step % len(self.weather_df)]
        current_sp = self.sp_df.iloc[self.current_step % len(self.sp_df)]
        
        # Update solar model with current global radiation
        self.solar_model.I_glob = current_weather["I_glob"]
        
        # Update PID controllers with current values and setpoints
        self.PID_Mdot.PV = self.air.T  # Current greenhouse temperature
        self.PID_Mdot.SP = current_sp["T_sp"]  # Temperature setpoint
        self.PID_CO2.PV = self.CO2_air.CO2_ppm  # Current CO2 concentration
        self.PID_CO2.SP = current_sp["CO2_sp"]  # CO2 setpoint
        
        # Compute PID controller outputs
        self.PID_Mdot.compute()
        self.PID_CO2.compute()
        
        # Update heat fluxes based on PID controller outputs
        # Convert PID output to heat flux (W/m²)
        self.q_low = self.PID_Mdot.CS * 1000  # Lower pipe heat flux
        self.q_up = 0  # Upper pipe not used in this simulation
        self.q_tot = self.q_low + self.q_up
        
        # Update pipe temperatures based on heat fluxes
        self.pipe_low.flow1DimInc.Q_tot = -self.q_low * 14000  # Convert back to total heat
        self.pipe_up.flow1DimInc.Q_tot = -self.q_up * 14000
        
        # Update energy calculations
        self.E_th_tot_kWhm2 += max(self.q_tot, 0) * dt / (1e3 * 3600)
        self.E_th_tot = self.E_th_tot_kWhm2 * 14000
        
        # Update electrical energy
        self.W_el_illu += self.illu.W_el / 14000 * dt / (1000 * 3600)
        self.E_el_tot_kWhm2 = self.W_el_illu
        self.E_el_tot = self.E_el_tot_kWhm2 * 14000
        
        # Update components
        self.cover.step(dt)
        self.air.step(dt)
        self.canopy.step(dt)
        self.floor.step(dt)
        self.pipe_low.step(dt)
        self.pipe_up.step(dt)
        self.thScreen.step(dt)
        self.air_Top.step(dt)
        self.solar_model.step(dt)
        self.illu.step()
        self.CO2_air.step(dt)
        
        # Update tomato yield model with current conditions
        self.TYM.set_environmental_conditions(
            R_PAR_can=self.solar_model.R_PAR_Can_umol + self.illu.step()["R_PAR_Can_umol"],
            CO2_air=self.CO2_air.CO2_ppm,
            T_canK=self.canopy.T
        )
        self.TYM.step(dt)
        self.DM_Har = self.TYM.DM_Har
        
        # Increment step counter
        self.current_step += 1
