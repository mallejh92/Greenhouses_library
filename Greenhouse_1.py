import numpy as np
import pandas as pd
from Components.Greenhouse.Cover import Cover
from Components.Greenhouse.Air import Air
from Components.Greenhouse.Canopy import Canopy
from Components.Greenhouse.Floor import Floor
from Components.Greenhouse.Air_Top import TopAirCompartment
from Components.Greenhouse.Solar_model import SolarModel
from Components.Greenhouse.HeatingPipe import HeatingPipe
from Components.Greenhouse.Illumination import Illumination
from Components.Greenhouse.ThermalScreen import ThermalScreen
from Flows.HeatTransfer.CanopyFreeConvection import CanopyFreeConvection
from Flows.HeatTransfer.FreeConvection import FreeConvection
from Flows.HeatTransfer.OutsideAirConvection import OutsideAirConvection
from Flows.CO2MassTransfer.MC_AirCan import MC_AirCan

class Greenhouse_1:
    """
    Simulation of a Venlo-type greenhouse for tomato crop cultivated from 10Dec-22Nov
    (weather data from TMY)
    """
    
    def __init__(self):
        # Constants
        self.surface = 1.4e4  # Floor surface area [m²]
        
        # Initialize components
        self.cover = Cover(
            rho=2600,
            c_p=840,
            A=self.surface,
            steadystate=True,
            h_cov=1e-3,
            phi=0.43633231299858
        )
        
        self.air = Air(
            A=self.surface,
            steadystate=True,
            steadystateVP=True,
            h_Air=3.8  # Will be updated dynamically
        )
        
        self.canopy = Canopy(
            A=self.surface,
            steadystate=True,
            LAI=1.06  # Will be updated from TYM
        )
        
        self.floor = Floor(
            rho=1,
            c_p=2e6,
            A=self.surface,
            V=0.01*self.surface,
            steadystate=True
        )
        
        self.air_top = TopAirCompartment(
            A=self.surface,
            steadystate=True,
            steadystateVP=True,
            h_Top=0.4
        )
        
        self.solar_model = SolarModel(
            A=self.surface,
            LAI=1.06,  # Will be updated from TYM
            I_glob=0.0  # Initial value, will be updated from weather data
        )
        
        self.pipe_low = HeatingPipe(
            A=self.surface,
            d=0.051,
            freePipe=False,
            N=5,
            N_p=625,
            l=50
        )
        
        self.pipe_up = HeatingPipe(
            A=self.surface,
            freePipe=True,
            d=0.025,
            l=44,
            N=5,
            N_p=292
        )
        
        self.illu = Illumination(
            A=self.surface,
            power_input=True,
            P_el=500,
            p_el=100
        )
        
        self.thScreen = ThermalScreen(
            A=self.surface,
            SC=0,  # Will be updated from control
            steadystate=False
        )
        
        # Initialize heat transfer components
        self.Q_rad_CanCov = None  # Will be initialized with proper parameters
        self.Q_cnv_CanAir = CanopyFreeConvection(A=self.surface)
        self.Q_cnv_FlrAir = FreeConvection(phi=0, A=self.surface, floor=True)
        self.Q_rad_CovSky = None  # Will be initialized with proper parameters
        self.Q_cnv_CovOut = OutsideAirConvection(A=self.surface, phi=0.43633231299858)
        
        # Initialize CO2 mass transfer
        self.MC_AirCan = MC_AirCan()
        
        # State variables
        self.q_low = 0.0  # Heat flux from lower pipe [W/m²]
        self.q_up = 0.0   # Heat flux from upper pipe [W/m²]
        self.q_tot = 0.0  # Total heat flux [W/m²]
        
        self.E_th_tot_kWhm2 = 0.0  # Total thermal energy per m² [kW·h/m²]
        self.E_th_tot = 0.0        # Total thermal energy [kW·h]
        
        self.DM_Har = 0.0  # Accumulated harvested tomato dry matter [mg/m²]
        
        self.W_el_illu = 0.0       # Electrical energy for illumination per m² [kW·h/m²]
        self.E_el_tot_kWhm2 = 0.0  # Total electrical energy per m² [kW·h/m²]
        self.E_el_tot = 0.0        # Total electrical energy [kW·h]
        
        # Load weather and setpoint data
        self.weather_df = pd.read_csv("./10Dec-22Nov.txt", 
                                    delimiter="\t", skiprows=2, header=None)
        self.weather_df.columns = ["time", "T_air", "P_air", "RH", "I_glob", 
                                 "wind", "T_sky", "VP", "lighting_on", "unused"]
        
        self.sp_df = pd.read_csv("./SP_10Dec-22Nov.txt",
                                delimiter="\t", skiprows=2, header=None)
        self.sp_df.columns = ["time", "T_set", "CO2_set"]
        
    def step(self, dt, time_idx):
        """
        Advance the simulation by one time step
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        time_idx : int
            Index for weather and setpoint data
            
        Returns:
        --------
        dict
            Dictionary containing current state variables
        """
        # Get current weather and setpoint data
        weather = self.weather_df.iloc[time_idx]
        setpoint = self.sp_df.iloc[time_idx]
        
        # Update component states
        self._update_components(dt, weather, setpoint)
        
        # Calculate energy flows
        self._calculate_energy_flows()
        
        # Return current state
        return self._get_state()
        
    def _update_components(self, dt, weather, setpoint):
        """Update all component states"""
        # Update air height based on screen closure
        h_Air = 3.8 + (1 - self.thScreen.SC) * 0.4
        self.air.h_Air = h_Air
        
        # Update component temperatures and states
        self.cover.step(dt)
        self.air.step(dt)
        self.canopy.step(dt)
        self.floor.step(dt)
        self.air_top.step(dt)
        
    def _calculate_energy_flows(self):
        """Calculate all energy flows between components"""
        # Calculate heat fluxes
        self.q_low = -self.pipe_low.Q_tot / self.surface
        self.q_up = -self.pipe_up.Q_tot / self.surface
        self.q_tot = -(self.pipe_low.Q_tot + self.pipe_up.Q_tot) / self.surface
        
        # Update accumulated energies
        if self.q_tot > 0:
            self.E_th_tot_kWhm2 += self.q_tot * 1e-3 * 3600  # Convert to kW·h/m²
        self.E_th_tot = self.E_th_tot_kWhm2 * self.surface
        
        # Update electrical energy
        self.W_el_illu += self.illu.W_el / self.surface
        self.E_el_tot_kWhm2 = self.W_el_illu
        self.E_el_tot = self.E_el_tot_kWhm2 * self.surface
        
    def _get_state(self):
        """Get current state variables"""
        return {
            'q_low': self.q_low,
            'q_up': self.q_up,
            'q_tot': self.q_tot,
            'E_th_tot_kWhm2': self.E_th_tot_kWhm2,
            'E_th_tot': self.E_th_tot,
            'DM_Har': self.DM_Har,
            'W_el_illu': self.W_el_illu,
            'E_el_tot_kWhm2': self.E_el_tot_kWhm2,
            'E_el_tot': self.E_el_tot,
            'T_air': self.air.T - 273.15,  # Convert to Celsius
            'RH_air': self.air.RH * 100,   # Convert to percentage
            'T_canopy': self.canopy.T - 273.15,
            'T_cover': self.cover.T - 273.15,
            'T_floor': self.floor.T - 273.15
        }
