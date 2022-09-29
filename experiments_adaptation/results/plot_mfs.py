import numpy as np
import skfuzzy as fuzz
import matplotlib.pyplot as plt
import pandas as pd

mappings = {
    "DIST": {
        "L": "low_distance",
        "M": "mid_distance",
        "H": "high_distance"
    },
    "VOLUME": {
        "L": "low_volume",
        "M": "mid_volume",
        "H": "high_volume"
    },
    "MOVEMENTS": {
        "L": "low_mov",
        "M": "mid_mov",
        "H": "high_mov"
    }
}
distributions_averages = {
    "US": {
        "low_distance": 0.5,
        "mid_distance":	1,
        "high_distance":	3,
        "low_volume":	30,
        "mid_volume":	60,
        "high_volume":	80,
        "low_mov":	0.1,
        "mid_mov":	0.4,
        "high_mov":	0.7
    },
    "Austria": {
        "low_distance": 0.46,
        "mid_distance": 0.92,
        "high_distance": 2.5,
        "low_volume": 30,
        "mid_volume": 60,
        "high_volume": 80,
        "low_mov": 0.2,
        "mid_mov": 0.6,
        "high_mov": 0.8
    }
}
distributions_stdevs = {
    "US": {
        "low_distance": 0.15,
        "mid_distance":	0.3,
        "high_distance":	0.5,
        "low_volume":	10,
        "mid_volume":	10,
        "high_volume":	10,
        "low_mov":	0.1,
        "mid_mov":	0.1,
        "high_mov":	0.1
    },
    "Austria": {
        "low_distance": 0.15,
        "mid_distance":	0.3,
        "high_distance":	0.5,
        "low_volume":	10,
        "mid_volume":	10,
        "high_volume":	10,
        "low_mov":	0.1,
        "mid_mov":	0.1,
        "high_mov":	0.1
    }
}

# generic_range = np.arange(0, 1.000001, 0.05)
range_dist = np.arange(0, 4.000001, 0.05)
range_vol = np.arange(0, 100.000001, 0.05)
range_mov = np.arange(0, 1.000001, 0.05)

mapping_ranges = {
    "DIST": range_dist,
    "VOLUME": range_vol,
    "MOVEMENTS": range_mov
}

""" The original mfs """
low_distance_us = fuzz.gaussmf(range_dist,  distributions_averages["US"]["low_distance"], distributions_stdevs["US"]["low_distance"])
mid_distance_us = fuzz.gaussmf(range_dist,  distributions_averages["US"]["mid_distance"], distributions_stdevs["US"]["mid_distance"])
high_distance_us = fuzz.gaussmf(range_dist, distributions_averages["US"]["high_distance"], distributions_stdevs["US"]["high_distance"])
low_volume_us = fuzz.gaussmf(range_vol,     distributions_averages["US"]["low_volume"], distributions_stdevs["US"]["low_volume"])
mid_volume_us = fuzz.gaussmf(range_vol,     distributions_averages["US"]["mid_volume"], distributions_stdevs["US"]["mid_volume"])
high_volume_us = fuzz.gaussmf(range_vol,    distributions_averages["US"]["high_volume"], distributions_stdevs["US"]["high_volume"])
low_mov_us = fuzz.gaussmf(range_mov,        distributions_averages["US"]["low_mov"], distributions_stdevs["US"]["low_mov"])
mid_mov_us = fuzz.gaussmf(range_mov,        distributions_averages["US"]["mid_mov"], distributions_stdevs["US"]["mid_mov"])
high_mov_us = fuzz.gaussmf(range_mov,       distributions_averages["US"]["high_mov"], distributions_stdevs["US"]["high_mov"])

low_distance_a = fuzz.gaussmf(range_dist,   distributions_averages["Austria"]["low_distance"], distributions_stdevs["Austria"]["low_distance"])
mid_distance_a = fuzz.gaussmf(range_dist,   distributions_averages["Austria"]["mid_distance"], distributions_stdevs["Austria"]["mid_distance"])
high_distance_a = fuzz.gaussmf(range_dist,  distributions_averages["Austria"]["high_distance"], distributions_stdevs["Austria"]["high_distance"])
low_volume_a = fuzz.gaussmf(range_vol,      distributions_averages["Austria"]["low_volume"], distributions_stdevs["Austria"]["low_volume"])
mid_volume_a = fuzz.gaussmf(range_vol,      distributions_averages["Austria"]["mid_volume"], distributions_stdevs["Austria"]["mid_volume"])
high_volume_a = fuzz.gaussmf(range_vol,     distributions_averages["Austria"]["high_volume"], distributions_stdevs["Austria"]["high_volume"])
low_mov_a = fuzz.gaussmf(range_mov,         distributions_averages["Austria"]["low_mov"], distributions_stdevs["Austria"]["low_mov"])
mid_mov_a = fuzz.gaussmf(range_mov,         distributions_averages["Austria"]["mid_mov"], distributions_stdevs["Austria"]["mid_mov"])
high_mov_a = fuzz.gaussmf(range_mov,        distributions_averages["Austria"]["high_mov"], distributions_stdevs["Austria"]["high_mov"])

""" Reading one from the results file """

results = pd.read_excel('20220918/exp_exp_20220905195629/aggr_res.xlsx', index_col=0)
# results = pd.read_excel('20220918/exp_exp_20220905195659/aggr_res.xlsx', index_col=0)
index_row_to_plot = 488
# index_row_to_plot = 263
# index_row_to_plot = 14
# index_row_to_plot = 251

results = pd.read_excel('exp_exp_20220928153233/aggr_res.xlsx', index_col=0)
index_row_to_plot = 0

row_to_plot = results.iloc[index_row_to_plot]
row_society = row_to_plot["society"]
print(row_to_plot)
results_mfs = {}
fsi = "FSQ_position_qualifier"

for dyn_var in mappings.keys():
    for dyn_var_value in mappings[dyn_var].values():
        a = float(row_to_plot[fsi + "_" + dyn_var + "_" + dyn_var_value + "_a"])
        b = float(row_to_plot[fsi + "_" + dyn_var + "_" + dyn_var_value + "_b"])
        c = float(row_to_plot[fsi + "_" + dyn_var + "_" + dyn_var_value + "_c"])
        d = float(row_to_plot[fsi + "_" + dyn_var + "_" + dyn_var_value + "_d"])
        results_mfs[dyn_var_value] = fuzz.trapmf(mapping_ranges[dyn_var], [a,b,c,d])

print(results_mfs)

plt.figure(figsize=(12, 8))
plt.subplot(321)
plt.plot(range_dist, low_distance_us, 'k--')
plt.plot(range_dist, mid_distance_us, 'k--')
plt.plot(range_dist, high_distance_us, 'k--')
if row_society=="US":
    plt.plot(range_dist, results_mfs["low_distance"])
    plt.plot(range_dist, results_mfs["mid_distance"])
    plt.plot(range_dist, results_mfs["high_distance"])
plt.subplot(322)
plt.plot(range_dist, low_distance_a, 'k--')
plt.plot(range_dist, mid_distance_a, 'k--')
plt.plot(range_dist, high_distance_a, 'k--')
if row_society=="Austria":
    plt.plot(range_dist, results_mfs["low_distance"])
    plt.plot(range_dist, results_mfs["mid_distance"])
    plt.plot(range_dist, results_mfs["high_distance"])
plt.subplot(323)
plt.plot(range_vol, low_volume_us, 'k--')
plt.plot(range_vol, mid_volume_us, 'k--')
plt.plot(range_vol, high_volume_us, 'k--')
if row_society=="US":
    plt.plot(range_vol, results_mfs["low_volume"])
    plt.plot(range_vol, results_mfs["mid_volume"])
    plt.plot(range_vol, results_mfs["high_volume"])
plt.subplot(324)
plt.plot(range_vol, low_volume_a, 'k--')
plt.plot(range_vol, mid_volume_a, 'k--')
plt.plot(range_vol, high_volume_a, 'k--')
if row_society=="Austria":
    plt.plot(range_vol, results_mfs["low_volume"])
    plt.plot(range_vol, results_mfs["mid_volume"])
    plt.plot(range_vol, results_mfs["high_volume"])
plt.subplot(325)
plt.plot(range_mov, low_mov_us, 'k--')
plt.plot(range_mov, mid_mov_us, 'k--')
plt.plot(range_mov, high_mov_us, 'k--')
if row_society=="US":
    plt.plot(range_mov, results_mfs["low_mov"])
    plt.plot(range_mov, results_mfs["mid_mov"])
    plt.plot(range_mov, results_mfs["high_mov"])
plt.subplot(326)
plt.plot(range_mov, low_mov_a, 'k--')
plt.plot(range_mov, mid_mov_a, 'k--')
plt.plot(range_mov, high_mov_a, 'k--')
if row_society=="Austria":
    plt.plot(range_mov, results_mfs["low_mov"])
    plt.plot(range_mov, results_mfs["mid_mov"])
    plt.plot(range_mov, results_mfs["high_mov"])

plt.show()