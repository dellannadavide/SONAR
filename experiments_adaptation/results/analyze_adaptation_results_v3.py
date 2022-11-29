import math

import numpy as np
import pandas as pd
import os
import skfuzzy

from sar.utils.moea import PHI_Q

pd.set_option('display.max_columns', None)

# aggregated_final_results = pd.DataFrame()
# res_folder = "20220918/exp_exp_20220905195629/"
res_folder = "final/exp_exp_20220929110809/" #G1
# res_folder = "final/exp_exp_20220929110904/" #G2
# res_folder = "final/exp_exp_20220929110937/" #G3
# res_folder = "final/exp_exp_20221115171111/" #G3 missing pt1
# res_folder = "20220918/exp_exp_20220905195659/"
# for filename in os.listdir(res_folder):
#     f = os.path.join(res_folder, filename)
#     if os.path.isfile(f) and f.endswith(".csv"):
#         dataset_df = pd.read_csv(f)
#         last_row = dataset_df.iloc[-1:] # I'm taking only the last row
#         aggregated_final_results = pd.concat([aggregated_final_results, last_row])


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

res_folders = ["final/exp_exp_20220929110809/", #G1,
                    "final/exp_exp_20220929110904/", #G2
                    "final/exp_exp_20220929110937/", #G3
                    "final/exp_exp_20221115171111/" #G3 missing pt1
    ]

""" Analysis steps

... Step 1. 
- from the files obtained by running simulations, compute, in an efficient way, the interpretability indeces and the NRMSE of every step. 
- generate a new file <original_filename>_ext.xlsx containing the new info

... Step 2.
- given the output files of step 1, compute, for every file (i.e., experimetn) the RMSE of the NRMSEerrors of core center and width and of interpretability
- generate a new file results_<foldername>.xlsx containing one row per experiments with the full list of param + the resulting RMSEs.
"""
analysis_step = 2

if analysis_step == 2:
    res_folders = [
        # "final/exp_exp_20220929110809/",  # G1,
                   "final/exp_exp_20220929110904/",  # G2
                   # "final/exp_exp_20220929110937/",  # G3
                   # "final/exp_exp_20221115171111/"  # G3 missing pt1
                   ]
    for res_folder in res_folders:
        res_group = pd.DataFrame()

        all_rmse_means_errors = []
        all_rmse_stdev_errors = []
        all_rmse_interp_errors = []

        for filename in os.listdir(res_folder):
            f = os.path.join(res_folder, filename)
            if os.path.isfile(f) and f.endswith("_ext.xlsx"):
                print(filename)
                dataset_df = pd.read_excel(f)

                last_row = dataset_df.iloc[-1:]  # taking the last row just to store all the experiments parameters
                res_group = pd.concat([res_group, last_row])

                sum_squares_means_errors = 0.0
                sum_squares_stdevs_errors = 0.0
                sum_squares_interpr_errors_VS1 = 0.0
                N = 0
                for index, row in dataset_df.iterrows():
                    """ For every data point (row in the dataframe)"""
                    sum_squares_means_errors += (row['Average NRMSE of Means (core center)'])**2 #NOTE THE ROW ALAREDY CONTAINS THEERROR, SO I DO NOT MAKE A DIFFERENCE
                    sum_squares_stdevs_errors += (row['Average NRMSE of Stdevs (core width)'])**2
                    sum_squares_interpr_errors_VS1 += (1 - row['Average Interpretability'])**2 #i'M USING 1 AS BEST INTERPRETABILITY (BUT NOT SURE IT'S GOOD)
                    N += 1

                rmse_means_errors = math.sqrt((1/N)*sum_squares_means_errors)
                rmse_stdev_errors = math.sqrt((1/N)*sum_squares_stdevs_errors)
                rmse_interp_errors_VS1 = math.sqrt((1/N)*sum_squares_interpr_errors_VS1)

                all_rmse_means_errors.append(rmse_means_errors)
                all_rmse_stdev_errors.append(rmse_stdev_errors)
                all_rmse_interp_errors.append(rmse_interp_errors_VS1)

        res_group['rmse_means_errors'] = all_rmse_means_errors
        res_group['rmse_stdev_errors'] = all_rmse_stdev_errors
        res_group['rmse_interp_errors_VS1'] = all_rmse_interp_errors
        res_group.to_excel(os.path.join(res_folder, "res_group.xlsx"))


if analysis_step == 1:
    memory_to_speed_up = {}

    for res_folder in res_folders:
        for filename in os.listdir(res_folder):
            f = os.path.join(res_folder, filename)
            if os.path.isfile(f) and f.endswith(".csv"):
                print(filename)
                dataset_df = pd.read_csv(f)

                fsi = "FSQ_position_qualifier"
                average_nrmse_means = []
                average_nrmse_stdevs = []
                average_interpretabilities = []
                for index, row in dataset_df.iterrows():
                    """ For every data point (row in the dataframe)"""
                    # print(index)
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
                            # print(fuzzyset)
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

                        # print(str(partition))
                        part_str = dyn_var+"_"+str(partition)
                        if part_str in memory_to_speed_up.keys():
                            """ here then I just retrieve the vals I am interested in """
                            average_nrmse_mean = average_nrmse_mean + memory_to_speed_up[part_str]["nrmse_mean"]
                            average_nrmse_stdev = average_nrmse_stdev + memory_to_speed_up[part_str]["nrmse_stdev"]
                            average_interpretability = average_interpretability + memory_to_speed_up[part_str]["phi_q"]
                        else:
                            rmse_mean = math.sqrt(rmse_mean / len(fuzzy_sets))
                            rmse_stdev = math.sqrt(rmse_stdev / len(fuzzy_sets))
                            # print(len(fuzzy_sets))
                            # print(rmse_mean, rmse_stdev)
                            #
                            # print(means)
                            # print(stdevs)

                            normalizer_mean = np.mean(np.asarray(means))
                            normalizer_stdev = np.mean(np.asarray(stdevs))

                            nrmse_mean = 0.0
                            nrmse_stdev = 0.0
                            if normalizer_mean > 0.0000001:
                                nrmse_mean = rmse_mean / normalizer_mean

                            if normalizer_stdev > 0.0000001:
                                nrmse_stdev = rmse_stdev / normalizer_stdev

                            phi_q = PHI_Q([min(mapping_ranges[dyn_var]), max(mapping_ranges[dyn_var])], partition)

                            memory_to_speed_up[part_str] = {
                                # "rmse_mean": rmse_mean,
                                # "rmse_stdev": rmse_stdev,
                                # "normalized_mean": normalizer_mean,
                                # "normalized_stdev": normalizer_stdev,
                                "nrmse_mean": nrmse_mean,
                                "nrmse_stdev": nrmse_stdev,
                                "phi_q": phi_q
                            }

                            # print(nrmse_mean, nrmse_stdev)
                            average_nrmse_mean = average_nrmse_mean + nrmse_mean
                            average_nrmse_stdev = average_nrmse_stdev + nrmse_stdev
                            average_interpretability = average_interpretability + phi_q


                    average_nrmse_mean = average_nrmse_mean/len(mappings.keys())
                    average_nrmse_stdev = average_nrmse_stdev / len(mappings.keys())
                    average_interpretability = average_interpretability/len(mappings.keys())

                    # print(index, "--->", average_nrmse_mean, average_nrmse_stdev, average_interpretability)
                    average_nrmse_means.append(average_nrmse_mean)
                    average_nrmse_stdevs.append(average_nrmse_stdev)
                    average_interpretabilities.append(average_interpretability)


                # print(rmse_df)
                dataset_df['Average NRMSE of Means (core center)'] = average_nrmse_means
                dataset_df['Average NRMSE of Stdevs (core width)'] = average_nrmse_stdevs
                dataset_df['Average Interpretability'] = average_interpretabilities
                dataset_df.to_excel(os.path.join(res_folder, filename.replace(".csv","")+"_ext.xlsx"))
