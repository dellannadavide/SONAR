import math

import numpy as np
import pandas as pd
import os
import skfuzzy

from sar.utils.moea import PHI_Q

pd.set_option('display.max_columns', None)

aggregated_final_results = pd.DataFrame()
res_folder = "20220918/exp_exp_20220905195629/"
res_folder = "exp_exp_20220928153233/"
# res_folder = "20220918/exp_exp_20220905195659/"
for filename in os.listdir(res_folder):
    f = os.path.join(res_folder, filename)
    if os.path.isfile(f) and f.endswith(".csv"):
        dataset_df = pd.read_csv(f)
        last_row = dataset_df.iloc[-1:]
        aggregated_final_results = pd.concat([aggregated_final_results, last_row])


# fuzzy_sets_file_austria = "data/fuzzy_rules/social_interpretation2sim/fuzzy_sets_multiple_GOLDSTANDARD_Austria.xlsx"
# fuzzy_sets_file_us = "data/fuzzy_rules/social_interpretation2sim/fuzzy_sets_multiple_GOLDSTANDARD_US.xlsx"
# ling_vars_file = "data/fuzzy_rules/social_interpretation2sim/ling_var_multiple.xlsx"
# rules_file_austria = "data/fuzzy_rules/social_interpretation2sim/rules_DIAMONDS_multiple_Austria.xlsx"
# rules_file_us = "data/fuzzy_rules/social_interpretation2sim/rules_DIAMONDS_multiple_US.xlsx"
# fsis = {
#     "Austria": FuzzySocialInterpreter(fuzzy_sets_file_austria, ling_vars_file, rules_file_austria, 0.2),
#     "US": FuzzySocialInterpreter(fuzzy_sets_file_us, ling_vars_file, rules_file_us, 0.2)
# }
#
# aggregated_final_results.to_excel(os.path.join(res_folder, "aggr_res.xlsx"))
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
# gen_range = np.arange(0, 1.000001, 0.05)
range_dist = np.arange(0, 4.000001, 0.05)
range_vol = np.arange(0, 100.000001, 0.05)
range_mov = np.arange(0, 1.000001, 0.05)



mapping_ranges = {
    "DIST": range_dist,
    "VOLUME": range_vol,
    "MOVEMENTS": range_mov
}

aggregated_final_results = aggregated_final_results.reset_index()  # make sure indexes pair with number of rows
fsi = "FSQ_position_qualifier"
average_nrmse_means = []
average_nrmse_stdevs = []
average_interpretabilities = []
for index, row in aggregated_final_results.iterrows():
    average_nrmse_mean = 0.0
    average_nrmse_stdev = 0.0
    average_interpretability = 0.0
    society = row["society"]
    for dyn_var in mappings.keys():
        rmse_mean = 0.0
        rmse_stdev = 0.0
        # max_mean = -99999999
        # max_stdev = -99999999
        # min_mean = 999999999
        # min_stdev = 999999999
        means = []
        stdevs = []
        fuzzy_sets = mappings[dyn_var].values()
        partition = []
        for fuzzyset in fuzzy_sets:
            mean_cap = distributions_averages[society][fuzzyset]
            stdev_cap = distributions_stdevs[society][fuzzyset]

            a = row[fsi+"_"+dyn_var+"_"+fuzzyset+"_a"]
            b = row[fsi+"_"+dyn_var+"_"+fuzzyset+"_b"]
            c = row[fsi+"_"+dyn_var+"_"+fuzzyset+"_c"]
            d = row[fsi+"_"+dyn_var+"_"+fuzzyset+"_d"]

            if b<a:
                b=a
            if c<b:
                c=b
            if d<c:
                d=c
            partition.append(skfuzzy.trapmf(mapping_ranges[dyn_var], [a,b,c,d]))

            mean_est = b+c/2.0
            stdev_est = c-b

            rmse_mean = rmse_mean + ((mean_est-mean_cap)**2)
            rmse_stdev = rmse_stdev + ((stdev_est-stdev_cap)**2)

            means.append(mean_est)
            stdevs.append(stdev_est)
            # min_mean= min(min_mean, mean_est)
            # max_mean = max(max_mean, mean_est)
            # min_stdev = min(min_stdev, stdev_est)
            # max_stdev = max(max_stdev, stdev_est)

            # print(fuzzyset, mean_cap, stdev_cap, mean_est, stdev_est, rmse_mean, rmse_stdev, min_mean,max_mean, min_stdev, max_stdev)

        rmse_mean = math.sqrt(rmse_mean/len(fuzzy_sets))
        rmse_stdev = math.sqrt(rmse_stdev /len(fuzzy_sets))
        # print(len(fuzzy_sets))
        print(rmse_mean, rmse_stdev)

        print(means)
        print(stdevs)

        normalizer_mean = np.mean(np.asarray(means))
        normalizer_stdev = np.mean(np.asarray(stdevs))
        nrmse_mean = 0.0
        nrmse_stdev=0.0
        if normalizer_mean>0.0000001:
            nrmse_mean = rmse_mean/normalizer_mean
            average_nrmse_mean = average_nrmse_mean + nrmse_mean
        if normalizer_stdev > 0.0000001:
            nrmse_stdev = rmse_stdev / normalizer_stdev
            average_nrmse_stdev = average_nrmse_stdev + nrmse_stdev
        print(nrmse_mean, nrmse_stdev)

        average_interpretability = average_interpretability + PHI_Q([min(mapping_ranges[dyn_var]), max(mapping_ranges[dyn_var])], partition)


    average_nrmse_mean = average_nrmse_mean/len(mappings.keys())
    average_nrmse_stdev = average_nrmse_stdev / len(mappings.keys())
    average_interpretability = average_interpretability/len(mappings.keys())

    print(index, "--->", average_nrmse_mean, average_nrmse_stdev, average_interpretability)
    average_nrmse_means.append(average_nrmse_mean)
    average_nrmse_stdevs.append(average_nrmse_stdev)
    average_interpretabilities.append(average_interpretability)


# print(rmse_df)
aggregated_final_results['Average NRMSE of Means'] = average_nrmse_means
aggregated_final_results['Average NRMSE of Stdevs'] = average_nrmse_stdevs
aggregated_final_results['Average Interpretability'] = average_interpretabilities
aggregated_final_results.to_excel(os.path.join(res_folder, "aggr_res.xlsx"))
