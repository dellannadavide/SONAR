import math

import numpy as np
import pandas as pd
import os
import skfuzzy
import matplotlib.pyplot as plt
from mas.utils.moea import PHI_Q


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


rmse_df = pd.DataFrame()
gen_range = np.arange(0, 1.000001, 0.05)
range_dist = np.arange(0, 4.000001, 0.05)
range_vol = np.arange(0, 100.000001, 0.05)
range_mov = np.arange(0, 1.000001, 0.05)



mapping_ranges = {
    "DIST": range_dist,
    "VOLUME": range_vol,
    "MOVEMENTS": range_mov
}

plt.figure(figsize=(12, 8))

var_id = 1
for society in distributions_stdevs.keys():
    print(society)
    average_interpretability = 0.0


    for dyn_var in mappings.keys():
        plt.subplot(320+var_id)
        var_id=var_id+1

        rmse_mean = 0.0
        rmse_stdev = 0.0

        means = []
        stdevs = []
        fuzzy_sets = mappings[dyn_var].values()
        partition = []
        fid = 0
        for fuzzyset in fuzzy_sets:
            # print(fuzzyset)
            mean_cap = distributions_averages[society][fuzzyset]
            stdev_cap = distributions_stdevs[society][fuzzyset]

            a = min(mapping_ranges[dyn_var])

            b = mean_cap - (stdev_cap / 2.0)
            # if fid==0:
            #     b = a

            c = mean_cap + (stdev_cap/2.0)
            # if fid==len(fuzzy_sets)-1:
            #     c = max(mapping_ranges[dyn_var])

            d = max(mapping_ranges[dyn_var])

            if b < a:
                b = a
            if c < b:
                c = b
            if d < c:
                d = c

            partition.append(skfuzzy.trapmf(mapping_ranges[dyn_var], [a, b, c, d]))

            fid = fid+1


        for x in partition:
            plt.plot(mapping_ranges[dyn_var], x, 'k--')

        phi_q = PHI_Q([min(mapping_ranges[dyn_var]), max(mapping_ranges[dyn_var])], partition)
        print("interpretability of ", dyn_var, " (", society, "):", phi_q)
        average_interpretability = average_interpretability + phi_q

    average_interpretability = average_interpretability/len(mappings.keys())
    print(average_interpretability)





""" The original mfs """
print("US GAUSSIAN")
low_distance_us = skfuzzy.gaussmf(range_dist,  distributions_averages["US"]["low_distance"], distributions_stdevs["US"]["low_distance"])
mid_distance_us = skfuzzy.gaussmf(range_dist,  distributions_averages["US"]["mid_distance"], distributions_stdevs["US"]["mid_distance"])
high_distance_us = skfuzzy.gaussmf(range_dist, distributions_averages["US"]["high_distance"], distributions_stdevs["US"]["high_distance"])

part = [low_distance_us, mid_distance_us, high_distance_us]
phi_part = PHI_Q([min(mapping_ranges["DIST"]), max(mapping_ranges["DIST"])], part)
print(phi_part)
# plt.subplot(321)
# for x in part:
#     plt.plot(mapping_ranges["DIST"], x)

low_volume_us = skfuzzy.gaussmf(range_vol,     distributions_averages["US"]["low_volume"], distributions_stdevs["US"]["low_volume"])
mid_volume_us = skfuzzy.gaussmf(range_vol,     distributions_averages["US"]["mid_volume"], distributions_stdevs["US"]["mid_volume"])
high_volume_us = skfuzzy.gaussmf(range_vol,    distributions_averages["US"]["high_volume"], distributions_stdevs["US"]["high_volume"])

part = [low_volume_us, mid_volume_us, high_volume_us]
phi_part = PHI_Q([min(mapping_ranges["VOLUME"]), max(mapping_ranges["VOLUME"])], part)
print(phi_part)
plt.subplot(322)
for x in part:
    plt.plot(mapping_ranges["VOLUME"], x)

low_mov_us = skfuzzy.gaussmf(range_mov,        distributions_averages["US"]["low_mov"], distributions_stdevs["US"]["low_mov"])
mid_mov_us = skfuzzy.gaussmf(range_mov,        distributions_averages["US"]["mid_mov"], distributions_stdevs["US"]["mid_mov"])
high_mov_us = skfuzzy.gaussmf(range_mov,       distributions_averages["US"]["high_mov"], distributions_stdevs["US"]["high_mov"])

part = [low_mov_us, mid_mov_us, high_mov_us]
phi_part = PHI_Q([min(mapping_ranges["MOVEMENTS"]), max(mapping_ranges["MOVEMENTS"])], part)
print(phi_part)
plt.subplot(323)
for x in part:
    plt.plot(mapping_ranges["MOVEMENTS"], x)

low_distance_a = skfuzzy.gaussmf(range_dist,   distributions_averages["Austria"]["low_distance"], distributions_stdevs["Austria"]["low_distance"])
mid_distance_a = skfuzzy.gaussmf(range_dist,   distributions_averages["Austria"]["mid_distance"], distributions_stdevs["Austria"]["mid_distance"])
high_distance_a = skfuzzy.gaussmf(range_dist,  distributions_averages["Austria"]["high_distance"], distributions_stdevs["Austria"]["high_distance"])
low_volume_a = skfuzzy.gaussmf(range_vol,      distributions_averages["Austria"]["low_volume"], distributions_stdevs["Austria"]["low_volume"])
mid_volume_a = skfuzzy.gaussmf(range_vol,      distributions_averages["Austria"]["mid_volume"], distributions_stdevs["Austria"]["mid_volume"])
high_volume_a = skfuzzy.gaussmf(range_vol,     distributions_averages["Austria"]["high_volume"], distributions_stdevs["Austria"]["high_volume"])
low_mov_a = skfuzzy.gaussmf(range_mov,         distributions_averages["Austria"]["low_mov"], distributions_stdevs["Austria"]["low_mov"])
mid_mov_a = skfuzzy.gaussmf(range_mov,         distributions_averages["Austria"]["mid_mov"], distributions_stdevs["Austria"]["mid_mov"])
high_mov_a = skfuzzy.gaussmf(range_mov,        distributions_averages["Austria"]["high_mov"], distributions_stdevs["Austria"]["high_mov"])




print("Initial")
print("dist")
low = skfuzzy.trapmf(range_dist, [0.0, 0.0, 0.0, 0.5])
mid = skfuzzy.trapmf(range_dist, [0.0, 0.5, 0.5, 1.0])
high = skfuzzy.trapmf(range_dist, [0.5, 1.0, 1.0, 1.0])
part = [low, mid, high]
phi_part = PHI_Q([min(mapping_ranges["DIST"]), max(mapping_ranges["DIST"])], part)
print(phi_part)
print("VOLUME")
low = skfuzzy.trapmf(range_vol, [0.0, 0.0, 0.0, 0.5])
mid = skfuzzy.trapmf(range_vol, [0.0, 0.5, 0.5, 1.0])
high = skfuzzy.trapmf(range_vol, [0.5, 1.0, 1.0, 1.0])
part = [low, mid, high]
phi_part = PHI_Q([min(mapping_ranges["VOLUME"]), max(mapping_ranges["VOLUME"])], part)
print(phi_part)
print("MOVEMENTS")
low = skfuzzy.trapmf(range_mov, [0.0, 0.0, 0.0, 0.5])
mid = skfuzzy.trapmf(range_mov, [0.0, 0.5, 0.5, 1.0])
high = skfuzzy.trapmf(range_mov, [0.5, 1.0, 1.0, 1.0])
part = [low, mid, high]
phi_part = PHI_Q([min(mapping_ranges["MOVEMENTS"]), max(mapping_ranges["MOVEMENTS"])], part)
print(phi_part)



print("Test")
print("dist")
low = skfuzzy.trapmf(range_dist, [0.031608909,	0.546751676,	1.593558494,	3.266185312
])
mid = skfuzzy.trapmf(range_dist, [0.140158499,	0.852793461,	1.855641638,	3.53042283
])
high = skfuzzy.trapmf(range_dist, [0.252564247,	1.843075778,	3.320281096,	4.248909187
])
part = [low, mid, high]
phi_part = PHI_Q([min(mapping_ranges["DIST"]), max(mapping_ranges["DIST"])], part)
print(phi_part)

plt.subplot(321)
for x in part:
    plt.plot(mapping_ranges["DIST"], x)

print("VOLUME")
low = skfuzzy.trapmf(range_vol, [0.0, 0.0, 0.0, 0.5])
mid = skfuzzy.trapmf(range_vol, [0.0, 0.5, 0.5, 1.0])
high = skfuzzy.trapmf(range_vol, [0.5, 1.0, 1.0, 1.0])
part = [low, mid, high]
phi_part = PHI_Q([min(mapping_ranges["VOLUME"]), max(mapping_ranges["VOLUME"])], part)
print(phi_part)
print("MOVEMENTS")
low = skfuzzy.trapmf(range_mov, [0.0, 0.0, 0.0, 0.5])
mid = skfuzzy.trapmf(range_mov, [0.0, 0.5, 0.5, 1.0])
high = skfuzzy.trapmf(range_mov, [0.5, 1.0, 1.0, 1.0])
part = [low, mid, high]
phi_part = PHI_Q([min(mapping_ranges["MOVEMENTS"]), max(mapping_ranges["MOVEMENTS"])], part)
print(phi_part)


plt.show()