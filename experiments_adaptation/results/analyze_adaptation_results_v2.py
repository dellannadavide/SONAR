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

res_folders = [
    # "final/exp_exp_20220929110809/", #G1,
    #                 "final/exp_exp_20220929110904/", #G2
                    # "final/exp_exp_20220929110937/", #G3
                    # "final/exp_exp_20221115171111/", #G3 missing pt1,
                    # "final/exp_exp_20221115171427/", #G3 missing pt2
                    # "final/exp_exp_20221213112012/", #g3 longer optim
                    # "final/25-35k/exp_exp_20221221210716/",
                    # "final/25-35k/exp_exp_20221221211115/",
                    # "final/25-35k/exp_exp_20221221211314/",
                    # "final/5datasets",
                    "final/5datasets_2040mindp",
    ]

""" Analysis steps

... Step 1. 
- from the files obtained by running simulations, compute, in an efficient way, the interpretability indeces and the NRMSE of every step. 
- generate a new file <original_filename>_ext.xlsx containing the new info

"""
analysis_step = 0

if analysis_step == 0:
    for res_folder in res_folders:
        print(res_folder)
        for filename in os.listdir(res_folder):
            f = os.path.join(res_folder, filename)
            if os.path.isfile(f) and f.endswith(".csv"):

                dataset_df = pd.read_csv(f)
                row_0 = dataset_df.iloc[0]
                # print(dataset_df.columns)
                print(filename, end="\t")
                for n in dataset_df.columns:
                    print(row_0[n], end="\t")

                print()
                # 'society', 'dataset_file', 'max_dataset_size', 'fuzzy_sets_file',
                # 'ling_vars_file', 'rules_file_id', 'interpretability_index',
                # 'min_nr_datapoints', 'min_certainty_threshold', 'genetic_algo',
                # 'ga_nr_gen', 'pop_size', 'trial', 'STEP/DATAPOINT',
                # 'use_correct_interpretation', 'consider_past_experience',
                # 'contextualize', 'min_nr_adaptations_for_contextualizing',
                # 'correct_interpretation', 'social_interpretation',
                # 'certainty_interpretation',

if analysis_step == 1:
    memory_to_speed_up = {}

    for res_folder in res_folders:
        for filename in os.listdir(res_folder):
            f = os.path.join(res_folder, filename)
            if os.path.isfile(f) and f.endswith(".csv"):
                print(filename)
                newfilename = filename.replace(".csv", "") + "_ext.xlsx"
                if not os.path.isfile(os.path.join(res_folder, newfilename)):
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
                    dataset_df.to_excel(os.path.join(res_folder, newfilename))
                else:
                    print("Skipping (already exists)")
