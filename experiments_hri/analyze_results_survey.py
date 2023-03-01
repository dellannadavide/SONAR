import plot_likert

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# from autorank import autorank, plot_stats, create_report, latex_table

from scipy.stats import wilcoxon
import math

scl = {'Strongly disagree': 1,
       'Somewhat disagree': 2,
       'Neither agree nor disagree': 3,
       'Somewhat agree': 4,
       'Strongly agree': 5
       }

# data = pd.read_excel("25_participants.xlsx", sheet_name="personality")
# data = pd.read_excel("25_participants.xlsx", sheet_name="personality_beforeafter")
# data = pd.read_excel("25_participants.xlsx", sheet_name="usus_us")
# data = pd.read_excel("25_participants.xlsx", sheet_name="usus_us_beforeafter")
# data = pd.read_excel("25_participants.xlsx", sheet_name="usus_ue")
data = pd.read_excel("25_participants.xlsx", sheet_name="usus_ue_beforeafter")
# data = pd.read_excel("25_participants.xlsx", sheet_name="usus_soc")

""" for plotting the lickert data """
a = plot_likert.plot_likert(data, plot_scale=scl.keys(), figsize=(25, 30))
plt.show()

# exit()

""" ref. Pages 224 (bottom part) and 225 from Pallant, J. (2007). SPSS Survival Manual: for effect size interpretation
also here: https://stats.stackexchange.com/questions/133077/effect-size-to-wilcoxon-signed-rank-test """
print("question", "median_BA", "median_SO", "SONAR - baseline", "w-alternative", "w-stat", "w-pval", "w-zstat", "significance", "effect size", "effect size interpretation", sep="\t")
to_compare = None
i = 0
for column in data:
    if i % 2 == 0:
        if not (to_compare is None):
            # print(to_compare)
            col_names = to_compare.columns
            diff = list(to_compare[col_names[1]] - to_compare[col_names[0]]) #1 is sonar, 0 is baseline
            # print(diff)
            for a in ["two-sided", "greater", "less"]:
                res = wilcoxon(diff,  method = 'approx', alternative=a)
                effect_size = math.fabs(res.zstatistic / math.sqrt(len(diff) * 2))
                effect_size_inter = ""
                if effect_size < 0.2:
                    effect_size_inter = "none"
                elif effect_size < 0.5:
                    effect_size_inter = "small"
                elif effect_size < 0.8:
                    effect_size_inter = "intermediate"
                else:
                    effect_size_inter = "large"

                sign = ""
                if res.pvalue<=0.01:
                    sign="**"
                elif res.pvalue<=0.05:
                    sign = "*"
                else:
                    sign = ""
                print(col_names[1].lower().replace(" so", ""), to_compare.median()[col_names[0]], to_compare.median()[col_names[1]], diff, a, res.statistic, res.pvalue, res.zstatistic, sign, effect_size, effect_size_inter, sep="\t")

            # result = autorank(to_compare, alpha=0.05, verbose=False)
            # print(result)
        # print()
        i = 0
        to_compare = pd.DataFrame()

    # print(column)
    # print(data[column].values)
    to_compare[column] = [(scl[x] if x in scl.keys() else 3) for x in data[column].values]
    i += 1

# print()
#for the last one
if not (to_compare is None):
    # print(to_compare)
    col_names = to_compare.columns
    diff = list(to_compare[col_names[1]] - to_compare[col_names[0]])
    # print(diff)
    for a in ["two-sided", "greater", "less"]:
        res = wilcoxon(diff,  method = 'approx', alternative=a)
        effect_size = math.fabs(res.zstatistic / math.sqrt(len(diff) * 2))
        effect_size_inter = ""
        if effect_size < 0.2:
            effect_size_inter = "none"
        elif effect_size < 0.5:
            effect_size_inter = "small"
        elif effect_size < 0.8:
            effect_size_inter = "intermediate"
        else:
            effect_size_inter = "large"
        sign = ""
        if res.pvalue <= 0.01:
            sign = "**"
        elif res.pvalue <= 0.05:
            sign = "*"
        else:
            sign = ""
        # print(a, res.statistic, res.pvalue, res.zstatistic, sign, "(", effect_size, ",",
        #       effect_size_inter, ")")
        print(col_names[1].lower().replace(" so", ""), to_compare.median()[col_names[0]], to_compare.median()[col_names[1]], diff, a, res.statistic, res.pvalue, res.zstatistic, sign, effect_size,
              effect_size_inter, sep="\t")
    # result = autorank(to_compare, alpha=0.05, verbose=False)
    # print(result)