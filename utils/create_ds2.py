import csv
import random

import pandas as pd
import numpy as np

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

# import numpy as np
# import matplotlib.pyplot as plt
# data = np.random.normal(0.92, 0.3, 25000)
# plt.hist(data, bins=25, density=True, alpha=0.6, color='b')
# plt.show()
# exit()

behavioral_rules = { #first element refers to distance, second element refers to volume, third refers to movement
    "DUTY":         ["M","L","L"],
    "INTELLECT":    ["H","L","L"],
    "ADVERSITY":    ["H","H","H"],
    "MATING":       ["L","L","L"],
    "POSITIVITY":   ["M","M","M"],
    "NEGATIVITY":   ["M","M","M"],
    "DECEPTION":    ["L","M","M"],
    "SOCIALITY":    ["M","M","M"]
}



cue2diam_file = "../data/societies_norms/cues-to-diamonds-fs-all.xlsx"


societies = ["Austria", "US"]
nr_data_points = 20000
data = []
cues_string = "Cue"

for society in societies:
    soc_cue2diam_df = pd.read_excel(cue2diam_file, engine='openpyxl', sheet_name=society)
    cues = list(soc_cue2diam_df[cues_string])
    if len(data)==0:
        data.append(["Society", "SocialInterpretation"] + cues + list(mappings.keys()))
    # print(data)
    social_interpretations = soc_cue2diam_df.columns.values.tolist()
    social_interpretations.remove(cues_string)
    nr_data_points_soc = 0
    while nr_data_points_soc<nr_data_points:
        print(nr_data_points_soc)
        for social_interpretation in social_interpretations:
            nr_cues = 0
            temp_list = []
            while nr_cues<1:
                nr_cues = 0
                temp_list = []
                for cue in cues:
                    corr_val = float(soc_cue2diam_df.loc[soc_cue2diam_df[cues_string]==cue, social_interpretation].iloc[0])
                    # print("corr val of ", cue, social_interpretation, ": ", corr_val)
                    # ignore_condition = (
                    #                            (corr_val < 0.05) or
                    #                            ((social_interpretation == "ADVERSITY") and (cue in ["WORKING", "FRIENDS", "COMMUNICATING"])) or
                    #                            ((social_interpretation == "DECEPTION") and (
                    #                                        cue in ["WORKING"])) or
                    #                            ((social_interpretation == "NEGATIVITY") and (
                    #                                    cue in ["WORKING"])) or
                    #                            ((social_interpretation == "INTELLECT") and (cue in ["FAMILY", "WORKING", "BAR", "MATE", "FRIENDS", "EATING", "DRINKING"]))
                    #                    ) \
                    #                    and \
                    #                    (
                    #                        not ((social_interpretation == "ADVERSITY") and (cue == "MUSIC")) and
                    #                        not ((social_interpretation == "INTELLECT") and (cue == "READING"))
                    #                    )
                    # ignore_condition = (corr_val < 0.05)
                    ignore_condition = (corr_val < 0)
                    # print("ignore ", ignore_condition)
                    if ignore_condition:
                        temp_list.append("0")
                    else:
                        if random.random()<=0.5:
                            temp_list.append("1")
                            nr_cues = nr_cues+1
                        else:
                            temp_list.append("0")

            dp = [society, social_interpretation]
            dp.extend(temp_list)

            #here need to add also the distance, etc.
            # dynamic_var_vals = []
            for mf_index in range(len(behavioral_rules[social_interpretation])):
                mf_val_identifier = behavioral_rules[social_interpretation][mf_index]
                mf_id = mappings[list(mappings.keys())[mf_index]][mf_val_identifier]
                dp.append(np.random.normal(
                    distributions_averages[society][mf_id],
                    distributions_stdevs[society][mf_id]))

            # print(dp)
            data.append(dp)
            nr_data_points_soc = nr_data_points_soc + 1

print(data)
with open("../data/societies_norms/data_{}_{}dp_v11_simple.csv".format(str(societies), str(nr_data_points)), "w+",newline="") as file:
    write = csv.writer(file)
    write.writerows(data)