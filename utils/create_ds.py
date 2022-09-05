import csv
import random

import numpy as np

from sar.norm.fuzzysocialinterpreter import FuzzySocialInterpreter

behavioral_patterns = { #first element refers to distance, second element refers to volume, third refers to movement
    "FAMILY":           ["L","M","M"],
    "MATE":             ["L","L","L"],
    "FRIENDS":          ["M","H","H"],
    "COHABITANTS":      ["M","M","L"],
    "COLLEAGUES":       ["M","L","L"],
    "ALONE":            ["H","L","L"],
    "SPORTS":           ["H","H","H"],
    "EXAM":             ["H","L","L"],
    "FOOD":             ["M","H","H"],
    "EATING":           ["M","M","M"],
    "DRINKING":         ["M","H","H"],
    "COMMUNICATING":    ["M","M","M"],
    "TV":               ["L","L","L"],
    "COMMUTING":        ["M","L","M"],
    "COMPUTER":         ["L","L","L"],
    "VIDEOGAMES":       ["L","H","H"],
    "READING":          ["M","L","L"],
    "WORKING":          ["M","L","L"],
    "SHOPPING":         ["M","H","H"],
    "GROOMING":         ["H","L","L"],
    "WAITING":          ["M","M","L"],
    "SLEEP":            ["H","L","L"],
    "MUSIC":            ["M","H","H"],
    "TELEPHONE":        ["H","M","M"],
    "HOME":             ["M","M","M"],
    "BATHROOM":         ["H","L","L"],
    "KITCHEN":          ["L","M","M"],
    "BED":              ["L","L","L"],
    "UNIVERSITY":       ["M","L","L"],
    "BAR":              ["M","H","H"]
}
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


probability_social_cue = (1/len(behavioral_patterns.keys()))*6
nr_data_points = 10000
societies = ["US", "Austria"]
data = []
data.append(["Society"]+ list(behavioral_patterns.keys())+list(mappings.keys()))
print(data)
for i in range(nr_data_points):
    true_cues = []
    temp_list = []
    while len(true_cues) != 1:
        true_cues = []
        temp_list = []
        selected = random.choice(list(behavioral_patterns.keys()))
        for cue in behavioral_patterns.keys():
            if str(cue)==str(selected):
            # if random.random()<=probability_social_cue:
                temp_list.append("1")
                true_cues.append(cue)
            else:
                temp_list.append("0")

    for society in societies:
        dp = [society]
        dp.extend(temp_list)
        sums = [0.0, 0.0, 0.0] #dist volume and movements
        for true_cue in true_cues:
            for mf_index in range(len(behavioral_patterns[true_cue])):
                mf_val_identifier = behavioral_patterns[true_cue][mf_index]
                mf_id = mappings[list(mappings.keys())[mf_index]][mf_val_identifier]
                sums[mf_index] = sums[mf_index]+np.random.normal(
                    distributions_averages[society][mf_id],
                    distributions_stdevs[society][mf_id]
                )
        for s in range(len(sums)):
            sums[s] = str(sums[s]/len(true_cues))
        dp.extend(sums)
        data.append(dp)


print(data)
with open("data/societies_norms/data_{}_{}dp_{}p_only1_dfixed.csv".format(str(societies), str(nr_data_points), str(probability_social_cue)), "w+",newline="") as file:
    write = csv.writer(file)
    write.writerows(data)