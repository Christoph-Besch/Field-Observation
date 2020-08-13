##
import pandas as pd
import numpy as np
import xarray as xr
from pathlib import Path; home = str(Path.home())      ### Zieht sich home vom system
working_directory = home + '/Seafile/Ana-Lena_Phillip/data/scripts/pypdd'
input_path = home + '/Seafile/Ana-Lena_Phillip/data/input_output/input/'

input_file = '20200625_Umrumqi_ERA5_2011_2018_cosipy.csv'
input_file_nc = '20200625_Umrumqi_ERA5_2011_2018_cosipy.nc'

input = input_path + input_file
input_nc = input_path + input_file_nc

#Time slice:
time_start = '2011-01-01T00:00'
time_end = '2018-12-31T23:00'

cosipy_df = pd.read_csv(input)
cosipy_df = cosipy_df.set_index('TIMESTAMP') # set Time as index
cosipy_df.index = pd.to_datetime(cosipy_df.index)
cosipy_df = cosipy_df.assign(temp= cosipy_df.T2-273.15) # temp in degree celsius

era5 = xr.open_dataset(input_nc)
## selfmade DDM: Part I - PDD
# input is a dataframe with time as index and temp in Celsius

def calculate_PDD_from_df(df):
    df.index = pd.to_datetime(df.index) # make sure it is datetime format
    # make sure temp unit is celsius
    temp_min = df.temp.resample('D').min()
    temp_max = df.temp.resample('D').max()
    temp_mean = df.temp.resample('D').mean()
    prec = df.RRR.resample('D').sum()

    degreedays_df = {'temp_min': temp_min, 'temp_max': temp_max, "temp_avg": temp_mean, "prec": prec}
    degreedays_df = pd.DataFrame(degreedays_df)
    degreedays_df["Date"] = degreedays_df.index

    # calculate the hydrological year
    def calc_hydrological_year(df):
        if 10 <= df.Date.month <= 12:
            water_year = df.Date.year + 1
            return water_year
        else:
            return df.Date.year

    degreedays_df['hydrological_year'] = degreedays_df.apply(lambda x: calc_hydrological_year(x), axis=1)
    degreedays_df.drop(["Date"], axis=1, inplace=True)

    # calculate the positive degree days
    def degree_days(df):
        if df["temp_avg"] > 0:
            return df["temp_avg"]
        else:
            return 0

    degreedays_df["PDD"] = degreedays_df.apply(degree_days, axis=1)
    degreedays_df["PDD_cum"] = degreedays_df["PDD"].cumsum()
    degreedays_df["PDD_cum_yearly"] = degreedays_df.groupby("hydrological_year")["PDD"].cumsum()

    return (degreedays_df)

degreedays_df =calculate_PDD_from_df(cosipy_df)

## selfmade DDM: Part II - calculating glacier melt etc. with formulas from pypdd
# for dataframes

#>>>> next task
PARAMETERS = {
    'pdd_factor_snow':  5.7, # mm per day per Celsius, from Hock 2003
    'pdd_factor_ice':   7.4, # mm per day per Celsius
    'temp_snow':        0.0,
    'temp_rain':        2.0,
    'refreeze_snow': 0.0,
    'refreeze_ice': 0.0}

def calculate_glaciermelt(df):
    temp = degreedays_df["temp_avg"]
    prec = degreedays_df["prec"]
    pdd = degreedays_df["PDD"]
    time = degreedays_df.index

    # pypdd line 311
    reduced_temp = (PARAMETERS["temp_rain"] - temp) / (PARAMETERS["temp_rain"] - PARAMETERS["temp_snow"])
    snowfrac = np.clip(reduced_temp, 0, 1) #np.clip needs a min and max value. Everything under becomes the min and \
                                            # everything above becomes the max value
    accu_rate = snowfrac * prec

    # initialize snow depth and melt rates
    snow_depth = np.zeros_like(temp)
    snow_melt_rate = np.zeros_like(temp)
    ice_melt_rate = np.zeros_like(temp)

    # pypdd
    def melt_rates(snow, pdd):
    # compute a potential snow melt
        pot_snow_melt = PARAMETERS['pdd_factor_snow'] * pdd
    # effective snow melt can't exceed amount of snow
        snow_melt = np.minimum(snow, pot_snow_melt)
    # ice melt is proportional to excess snow melt
        ice_melt = (pot_snow_melt - snow_melt) * PARAMETERS['pdd_factor_ice'] / PARAMETERS['pdd_factor_snow']
    # return melt rates
        return (snow_melt, ice_melt)

    # pypdd line 219
    for i in range(len(temp)):
        if i > 0:
            snow_depth[i] = snow_depth[i - 1]
        snow_depth[i] += accu_rate[i]
        snow_melt_rate[i], ice_melt_rate[i] = melt_rates(snow_depth[i], pdd[i])
        snow_depth[i] -= snow_melt_rate[i]
    snow_melt_rate = pd.Series(snow_melt_rate, index=time)
    ice_melt_rate = pd.Series(ice_melt_rate, index=time)
    total_melt = snow_melt_rate + ice_melt_rate
    runoff_rate = total_melt - PARAMETERS["refreeze_snow"] * snow_melt_rate \
                  - PARAMETERS["refreeze_ice"] * ice_melt_rate
    inst_smb = accu_rate - runoff_rate

    # making the final df
    glacier_melt = pd.concat([accu_rate, ice_melt_rate, snow_melt_rate, total_melt, inst_smb, runoff_rate], axis=1)
    glacier_melt.columns = ["accumulation_rate", "ice_melt", "snow_melt", "total_melt", "smb", "runoff"]
    glacier_melt["hydrological_year"] = df["hydrological_year"]
    return glacier_melt

glacier_melt = calculate_glaciermelt(degreedays_df) # output in mm
glacier_melt_yearly = glacier_melt.groupby("hydrological_year").sum()

## selfmade DDM: Part I - PDD
# input is a dataset
def calculate_PDD(ds):
    temp_min = ds['T2'].resample(time="D").min(dim="time") - 273.15 # now °C
    temp_max = ds['T2'].resample(time="D").max(dim="time") - 273.15
    temp_mean = ds['T2'].resample(time="D").mean(dim="time") - 273.15
    prec = ds['RRR'].resample(time="D").sum(dim="time")
    time = temp_mean["time"]

    ds = xr.merge([xr.DataArray(temp_mean, name="temp_mean"), xr.DataArray(temp_min, name="temp_min"), \
                   xr.DataArray(temp_max, name="temp_max"), prec])

    # calculate the hydrological year
    def calc_hydrological_year(time):
        water_year = []
        for i in time:
            if 10 <= i["time.month"] <= 12:
                water_year.append(i["time.year"] + 1)
            else:
                water_year.append(i["time.year"])
        return np.asarray(water_year)

    water_year = calc_hydrological_year(time)
    ds = ds.assign_coords(water_year = water_year)

    # calculate the positive degree days
    ds["pdd"] = xr.where(temp_mean > 0, temp_mean, 0)

    return ds

degreedays_ds = calculate_PDD(era5)
## selfmade DDM: Part II - calculating glacier melt etc. with formulas from pypdd
# for datasets

PARAMETERS = {
    'pdd_factor_snow':  5.7, # mm per day per Celsius, from Hock 2003
    'pdd_factor_ice':   7.4, # mm per day per Celsius
    'temp_snow':        0.0,
    'temp_rain':        2.0,
    'refreeze_snow': 0.0,
    'refreeze_ice': 0.0}

def calculate_glaciermelt(ds):
    temp = degreedays_ds["temp_mean"]
    prec = degreedays_ds["RRR"]
    pdd = degreedays_ds["pdd"]
    time = degreedays_ds["time"]

    # pypdd line 311
    reduced_temp = (PARAMETERS["temp_rain"] - temp) / (PARAMETERS["temp_rain"] - PARAMETERS["temp_snow"])
    snowfrac = np.clip(reduced_temp, 0, 1) #np.clip needs a min and max value. Everything under becomes the min and \
                                            # everything above becomes the max value
    accu_rate = snowfrac * prec

    # initialize snow depth and melt rates
    snow_depth = xr.zeros_like(temp)
    snow_melt_rate = xr.zeros_like(temp)
    ice_melt_rate = xr.zeros_like(temp)

    # pypdd
    def melt_rates(snow, pdd):
    # compute a potential snow melt
        pot_snow_melt = PARAMETERS['pdd_factor_snow'] * pdd
    # effective snow melt can't exceed amount of snow
        snow_melt = np.minimum(snow, pot_snow_melt)
    # ice melt is proportional to excess snow melt
        ice_melt = (pot_snow_melt - snow_melt) * PARAMETERS['pdd_factor_ice'] / PARAMETERS['pdd_factor_snow']
    # return melt rates
        return (snow_melt, ice_melt)

    # pypdd line 219
    for i in np.arange(len(temp)):
        if i > 0:
            snow_depth[i] = snow_depth[i - 1]
        snow_depth[i] += accu_rate[i]
        snow_melt_rate[i], ice_melt_rate[i] = melt_rates(snow_depth[i], pdd[i])
        snow_depth[i] -= snow_melt_rate[i]
    total_melt = snow_melt_rate + ice_melt_rate
    runoff_rate = total_melt - PARAMETERS["refreeze_snow"] * snow_melt_rate \
                  - PARAMETERS["refreeze_ice"] * ice_melt_rate
    inst_smb = accu_rate - runoff_rate

    # making the final ds
    glacier_melt = xr.merge([xr.DataArray(accu_rate, name="accumulation_rate"), xr.DataArray(ice_melt_rate, \
                            name="ice_melt_rate"), xr.DataArray(snow_melt_rate, name="snow_melt_rate"), \
                             xr.DataArray(total_melt, name="total_melt"), xr.DataArray(inst_smb, name="smb")])
    glacier_melt = glacier_melt.assign_coords(water_year = ds["water_year"])
    return glacier_melt

glacier_melt = calculate_glaciermelt(degreedays_ds) # output in mm
## PHILLIPs Test area:

temp_min = era5['T2'].resample(time="D").min(dim="time") - 273.15 # now °C
temp_max = era5['T2'].resample(time="D").max(dim="time") - 273.15
temp_mean = era5['T2'].resample(time="D").mean(dim="time") - 273.15
prec = era5['RRR'].resample(time="D").sum(dim="time")

ds = xr.merge([xr.DataArray(temp_mean, name="temp_mean"), xr.DataArray(temp_min, name="temp_min"), \
               xr.DataArray(temp_max, name="temp_max"), prec])

# calculate the hydrological year

water_year = []
for i in np.arange(len(ds.time)):
    if 10 <= ds.isel(time=i)["time.month"] <= 12:
        water_year.append(ds.isel(time=i)["time.year"].values + 1)
    else:
        water_year.append(ds.isel(time=i)["time.year"].values)


## ANSELMS water year approach

def calculate_water_year(data, method):
    year_list = []
    yearly_values = []
    for year in data.resample(time='y').sum().time.dt.year.values:
        time_start = str(year -1) + '-10-01'
        time_end = str(year) + '-09-30'
        if (time_start >= str(data.time[0].values)) and (time_end <= str(data.time[-1].values)):
            year_value = data.sel(time=slice(time_start, time_end))
            year_list.append(year)
            if method == 'sum':
                yearly_values.append(np.sum(year_value.values))
            elif method == 'mean':
                yearly_values.append(np.mean(year_value.values))
    return np.array(year_list), np.array(yearly_values)