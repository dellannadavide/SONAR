import math

import pandas as pd

def findClosestFS(fs_df, corr_val):
    closest = str(fs_df["Label"][0])
    closest_dist = 99999
    for fs_index in fs_df.index:
        dist = abs(corr_val-float(fs_df["b"][fs_index]))
        if dist<closest_dist:
            closest = str(fs_df["Label"][fs_index])
            closest_dist = dist
    return closest


si_rules = "data/societies_norms/cues-to-diamonds-fs-all.xlsx"

fs_df = pd.read_excel(si_rules, engine='openpyxl', sheet_name="FuzzySets")

societies_dfs = {
    "Austria": pd.read_excel(si_rules, engine='openpyxl', sheet_name="Austria"),
    "US": pd.read_excel(si_rules, engine='openpyxl', sheet_name="US")
}

for society_df_k in societies_dfs.keys():
    print(society_df_k)
    s_df = societies_dfs[society_df_k]
    social_interpretations = s_df.columns[1:].tolist()
    for row_index in s_df.index:
        social_cue = s_df["Cue"][row_index]
        for social_int in social_interpretations:
            corr_val = float(s_df[social_int][row_index])
            if not math.isnan(corr_val):
                fuzzy_set = findClosestFS(fs_df, corr_val)
                rule = "IF ({social_cue} IS high) THEN ({social_int} IS {fuzzy_set})".format(social_cue=social_cue,
                                                                                social_int=social_int,
                                                                                fuzzy_set=fuzzy_set)
                print(rule)
