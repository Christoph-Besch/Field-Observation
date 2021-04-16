## import of necessary packages
import pandas as pd
from pathlib import Path
import sys
import spotpy  # Load the SPOT package into your working storage
from spotpy import analyser  # Load the Plotting extension
home = str(Path.home())
sys.path.append(home + '/Seafile/Ana-Lena_Phillip/data/scripts/Test_area')
import mspot

## Creating an example file

working_directory = home + "/Seafile/Ana-Lena_Phillip/data/"
input_path_data = home + "/Seafile/Ana-Lena_Phillip/data/input_output/input/ERA5/Tien-Shan/At-Bashy/"
input_path_observations = home + "/Seafile/Ana-Lena_Phillip/data/input_output/input/observations/bash_kaindy/"
data_csv = "no182_ERA5_Land_2000_202011_no182_41_75.9_fitted.csv"  # dataframe with columns T2 (Temp in Celsius), RRR (Prec in mm) and if possible PE (in mm)
observation_data = "runoff_bashkaindy_04_2019-11_2020_temp_limit.csv"  # Daily Runoff Observations in mm
output_path = working_directory + "input_output/output/" + data_csv[:15]

df = pd.read_csv(input_path_data + data_csv)
obs = pd.read_csv(input_path_observations + observation_data)
obs["Qobs"] = obs["Qobs"] / 86400 * (46.232 * 1000000) / 1000  # Daten in mm, Umrechnung in m3/s

## Perform parameter sampling (may take a long time depending on # of reps)

best_summary = mspot.psample(df=df, obs=obs, rep=3, set_up_start='2018-01-01 00:00:00', set_up_end='2018-12-31 23:00:00',
                       sim_start='2019-01-01 00:00:00', sim_end='2020-11-01 23:00:00', area_cat=46.232,
                       area_glac=2.566, ele_dat=3864, ele_glac=4042, ele_cat=3360)

best_summary['par_uncertain_plot'].show()


# Weitere Schritte in die Funktion psample
# Gesamte Vielfalt der Algorithmen einbauen



# Find parameter interaction

# spotpy.analyser.plot_parameterInteraction(results)
# posterior = spotpy.analyser.get_posterior(results, percentage=10)
# spotpy.analyser.plot_parameterInteraction(posterior)


## Find best Algorithm

results = []
spot_setup = spot_setup(df, obs)  # Kann man aus irgendeinem Grund nur einmal ausführen.
rep = 50  # ideal number of iterations: spot_setup.par_iter
timeout = 10  # Given in Seconds

parallel = "seq"
dbformat = None  # Change to 'csv' or 'sql' to avoid data loss after long calculations
modelname = 'MATILDA'

sampler = spotpy.algorithms.mc(spot_setup, parallel=parallel, dbname=modelname + '_MC', dbformat=dbformat,
                               sim_timeout=timeout)
sampler.sample(rep)
results.append(sampler.getdata())

sampler = spotpy.algorithms.lhs(spot_setup, parallel=parallel, dbname=modelname + '_LHS', dbformat=dbformat,
                                sim_timeout=timeout)
sampler.sample(rep)
results.append(sampler.getdata())

sampler = spotpy.algorithms.mle(spot_setup, parallel=parallel, dbname=modelname + '_MLE', dbformat=dbformat,
                                sim_timeout=timeout)
sampler.sample(rep)
results.append(sampler.getdata())

sampler = spotpy.algorithms.mcmc(spot_setup, parallel=parallel, dbname=modelname + '_MCMC', dbformat=dbformat,
                                 sim_timeout=timeout)
sampler.sample(rep)
results.append(sampler.getdata())

sampler = spotpy.algorithms.sceua(spot_setup, parallel=parallel, dbname=modelname + '_SCEUA', dbformat=dbformat,
                                  sim_timeout=timeout)
sampler.sample(rep, ngs=4)
results.append(sampler.getdata())

sampler = spotpy.algorithms.sa(spot_setup, parallel=parallel, dbname=modelname + '_SA', dbformat=dbformat,
                               sim_timeout=timeout)
sampler.sample(rep)
results.append(sampler.getdata())

# sampler = spotpy.algorithms.demcz(spot_setup, parallel=parallel, dbname=modelname + '_DEMCz', dbformat=dbformat,
#                                   sim_timeout=timeout)
# sampler.sample(rep, nChains=4)
# results.append(sampler.getdata())

# ROPE works for HBV but stops for MATILDA at repetition 34 or so....

# sampler = spotpy.algorithms.rope(spot_setup, parallel=parallel, dbname=modelname + '_ROPE', dbformat=dbformat,
#                                  sim_timeout=timeout)
# sampler.sample(rep)
# results.append(sampler.getdata())

sampler = spotpy.algorithms.abc(spot_setup, parallel=parallel, dbname=modelname + '_ABC', dbformat=dbformat,
                                sim_timeout=timeout)
sampler.sample(rep)
results.append(sampler.getdata())

sampler = spotpy.algorithms.fscabc(spot_setup, parallel=parallel, dbname=modelname + '_FSABC', dbformat=dbformat,
                                   sim_timeout=timeout)
sampler.sample(rep)
results.append(sampler.getdata())

# sampler = spotpy.algorithms.demcz(spot_setup, parallel=parallel, dbname=modelname + '_DEMCZ', dbformat=dbformat,
#                                   sim_timeout=timeout)
# sampler.sample(rep)
# results.append(sampler.getdata())

sampler = spotpy.algorithms.dream(spot_setup, parallel=parallel, dbname=modelname + '_DREAM', dbformat=dbformat,
                                  sim_timeout=timeout)
sampler.sample(rep)
results.append(sampler.getdata())

algorithms = ['mc', 'lhs', 'mle', 'mcmc', 'sceua', 'sa', 'rope', 'abc', 'fscabc', 'dream']  # 'demcz', , 'demcz'
spotpy.analyser.plot_parametertrace_algorithms(results, algorithms, spot_setup)

## Sensitivity Analysis
spot_setup = spot_setup(df, obs)  # only once

sampler = spotpy.algorithms.fast(spot_setup, dbname='MATILDA_FAST', dbformat=None)
sampler.sample(1000)  # minimum 60 to run through,
# ideal number of iterations: spot_setup.par_iter, immer wieder einzelne Zeilen "out of bounds"
results = sampler.getdata()
analyser.plot_fast_sensitivity(results, number_of_sensitiv_pars=2, fig_name="FAST_sensitivity_MATILDA.png")

SI = spotpy.analyser.get_sensitivity_of_fast(results)  # Sensitivity indexes as dict

## Baustellen:

# TT_snow kann höher sein als TT_rain.
# Die CFMAX-Werte stehen in einem fixen Verhältnis.
# Die Correction-Factors überblenden immer die gesamte Sensitivitäts-Analyse
# Sollte die deltaH-Routine in der class mit eingebaut werden?
