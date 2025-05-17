import pandas as pd

weather_df = pd.read_csv("./10Dec-22Nov.txt", delimiter="\t", skiprows=2, header=None)
weather_df.columns = ["time", "T_out", "RH_out", "P_out", "I_glob",
                                   "u_wind", "T_sky", "T_air_sp", "CO2_air_sp", "ilu_sp"]

sp_df = pd.read_csv("./SP_10Dec-22Nov.txt", delimiter="\t", skiprows=2, header=None)
sp_df.columns = ["time", "T_sp", "CO2_sp"]

print(weather_df.shape)
# print(weather_df)
print(sp_df.shape)
# print(sp_df)