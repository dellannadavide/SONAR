import plot_likert
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

scl = ['Strongly disagree', 'Somewhat disagree', 'Neither agree nor disagree', 'Somewhat agree', 'Strongly agree']

data = pd.read_excel("lickertafter25.xlsx", sheet_name="personality")
data = pd.read_excel("lickertafter25.xlsx", sheet_name="usus_us")
data = pd.read_excel("lickertafter25.xlsx", sheet_name="usus_ue")

a = plot_likert.plot_likert(data, plot_scale=scl, figsize=(25, 30))


plt.show()

