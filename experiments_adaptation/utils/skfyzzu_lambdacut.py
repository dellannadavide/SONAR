import math
from random import random

import numpy as np
import skfuzzy as fuzz
import matplotlib.pyplot as plt

import scipy.integrate as integrate
from scipy.optimize import fsolve, curve_fit
from mas.utils.moea import YuanFuzzyOrderingIndex


# def linearScaleFromABToA1B1(x, a, b, a1, b1):
#     xin01 = (x-a)/(b-a)
#     xinA1B1 = a1+((b1-a1)*xin01)
#     return xinA1B1
#
# print(linearScaleFromABToA1B1(5, 5, 10, 0, 15))
# print(linearScaleFromABToA1B1(10, 5, 10, 0, 15))
# print(linearScaleFromABToA1B1(7.5, 5, 10, 0, 15))
# print(linearScaleFromABToA1B1(5.1, 5, 10, 0, 15))
# print(linearScaleFromABToA1B1(9, 5, 10, 0, 15))
# exit()

plt.figure(figsize=(8, 3))

# xdata = [0.0, 0.02, 0.04, 0.06, 0.2, 0.318, 0.428, 0.52, 0.585, 0.652, 0.708, 0.76, 0.81, 0.858, 0.895, 0.94, 0.98, 1.0]
# # ydata = [1.0, 1.0, 1.0, 1.0, 0.992, 0.98, 0.96, 0.94, 0.92, 0.9, 0.88, 0.86, 0.84, 0.82, 0.80, 0.78, 0.76, 0.75]
# ydata = [1.0, 0.999, 0.998, 0.997, 0.992, 0.98, 0.96, 0.94, 0.92, 0.9, 0.88, 0.86, 0.84, 0.82, 0.80, 0.64, 0.48, 0.40]
#
#
# xdata = [0.0, 0.2,      0.318, 0.428, 0.52, 0.585, 0.652, 0.708, 0.76, 0.81, 0.858, 0.895, 0.94, 0.98, 1.0]
# ydata = [1.0, 0.992,    0.98, 0.96, 0.94, 0.92,     0.9, 0.88, 0.86,    0.84, 0.82, 0.80, 0.64, 0.48, 0.40]
# xdata = np.asarray(xdata)
# ydata = np.asarray(ydata)
# z = np.polyfit(xdata, ydata, 6)
# print(z)
# f = np.poly1d(z)
# y_new = f(xdata)
# plt.plot(xdata, ydata, 'o', label='data')
# plt.plot(xdata, y_new, '-', label='fit')
# plt.show()
# exit()

def getV_xp_dji(dji, y):
    x = np.arange(0, 1.005, 0.01)
    mf = getV_xp_dji_fun(dji)
    return fuzz.interp_membership(x, mf, y)

def getV_xp_dji_fun(dji):
    x = np.arange(0, 1.005, 0.01)
    mf = fuzz.trapmf(x, [0.0, 0.5, 0.5, 1.0])
    if dji > 1:
        mf = fuzz.trapmf(x, [0.0, 0.0, 0.0, 2 / dji])
    return mf

def R_QXP(val):
  """ This function has been determined by fitting the following data, which are an approximation of the empirical relation reported in Botta 2008, Automatic Context Adaptation of Fuzzy Systems, Figure 32

  xdata = [0.0, 0.02, 0.04, 0.06, 0.2, 0.318, 0.428, 0.52, 0.585, 0.652, 0.708, 0.76, 0.81, 0.858, 0.895, 0.94, 0.98, 1.0]
  ydata = [1.0, 1.0, 1.0, 1.0, 0.992, 0.98, 0.96, 0.94, 0.92, 0.9, 0.88, 0.86, 0.84, 0.82, 0.80, 0.78, 0.76, 0.75]
  def cos_func(x, D, E):
    y = D*np.cos(E*x)
    return y
  parameters, covariance = curve_fit(cos_func, xdata, ydata)
  fit_D = parameters[0]
  fit_E = parameters[1]
  fit_cosine = cos_func(xdata, fit_D, fit_E)
  plt.plot(xdata, ydata, 'o', label='data')
  plt.plot(xdata, fit_cosine, '-', label='fit')
  """
  # fit_D = 1.0040176000168557
  # fit_E = 0.7204988202696069
  # return min(1.0, fit_D*np.cos(fit_E*val))
  #
  # z = np.asarray([-1.11060250e+08,  8.71489477e+08, - 2.99898845e+09,  5.80972505e+09,
  #  - 6.53534228e+09,  3.23001893e+09,  2.11105593e+09, - 5.47840488e+09,
  #  5.30122149e+09, - 3.22184964e+09,  1.34635931e+09, - 3.94162540e+08,
  #  7.98665114e+07, - 1.07997780e+07,  9.13889859e+05, - 4.37875533e+04,
  #  1.03770160e+03, - 9.10412636e+00,  9.99999997e-01])
  z = np.asarray([3.64852632e+03, -1.72006341e+04, 3.42682101e+04, -3.75850715e+04,
    2.47689899e+04, -1.00426639e+04, 2.46356571e+03, -3.45077631e+02,
    2.42099488e+01, -6.55567108e-01,  1.00158774e+00])
  z = np.asarray([2.53459486e+02, -1.02220973e+03, 1.64974010e+03, -1.36652553e+03,
   6.17087664e+02, -1.48005929e+02, 1.64682311e+01, -6.25997588e-01,
   1.00263934e+00])
  z = np.asarray([-31.02033482,  79.91487888, -77.74059048,  35.28901165,  -7.63705323,
   0.57831101,   1.00004764])
  f = np.poly1d(z)
  # return min(1.0, f(val))
  return f(val)

def getR_QXP(x, y):
    fy = R_QXP(y)
    # print(" \t\t\tx: ", x, "y: ", y, "fy: ", fy)
    # if fy==x:
    eps = 0.005
    if x>fy-eps and x<fy+eps:
        return 1
    else:
        return 0

def mu_q_dji(x, dji):
    m = 0.0
    for y in np.arange(0, 1.00000000001, 0.001):
        # print("\ty=", y)
        v_xyp_dji = getV_xp_dji(dji, y)
        rqxpxy = getR_QXP(x,y)
        # print("\t\t", v_xyp_dji, rqxpxy)
        v = min(v_xyp_dji, rqxpxy)
        if v>m:
            m = v
    return m

# plt.figure(figsize=(8, 3))
# # plt.xlim(0.8, 1.0)
# dji1 = []
# dji2 = []
# dji3 = []
# dji4 = []
#
# aran = np.arange(0.0, 1.01, 0.01)
# for x in aran:
#     print("x=",x)
#     dji1.append(mu_q_dji(x, 1))
#     dji2.append(mu_q_dji(x, 2))
#     dji3.append(mu_q_dji(x, 3))
#     dji4.append(mu_q_dji(x, 4))
# plt.plot(aran, dji1)
# plt.plot(aran, dji2)
# plt.plot(aran, dji3)
# plt.plot(aran, dji4)
#
# plt.show()
#
# exit()

#
# def mu_q_dji_APPROX(yuan, dji):
#     gen_range = np.arange(0, 1.005, 0.01)
#     _theta_1 = 1.001
#     _k_GP_1 = 9
#     if dji == 1:
#         mf = fuzz.trapmf(gen_range, [0.0, 0.94, 0.95, 1.25])
#         A_x = fuzz.interp_membership(gen_range, mf, yuan)
#         if A_x < _theta_1:
#             A_x = (_theta_1 ** (1 - _k_GP_1)) * (A_x ** _k_GP_1)
#         else:
#             A_x = 1 - (((1 - _theta_1) ** (1 - _k_GP_1)) * ((1 - A_x) ** _k_GP_1))
#         try:
#             A_x = float(A_x)
#         except:
#             A_x = A_x.real
#         return min(1, max(0.0, A_x))
#     else:
#         if yuan==1:
#             return 1
#         _theta_dji = 1.01
#         _k_GP_dji = 10
#         mf = fuzz.trapmf(gen_range, [min(0.95,((0.475*dji)-0.808333)), 1.0, 1.0, 1.2])
#         A_x = fuzz.interp_membership(gen_range, mf, yuan)
#         try:
#             if A_x < _theta_dji:
#                 A_x = (_theta_dji ** (1 - _k_GP_dji)) * (A_x ** _k_GP_dji)
#             else:
#                 A_x = 1 - (((1 - _theta_dji) ** (1 - _k_GP_dji)) * ((1 - A_x) ** _k_GP_dji))
#         except:
#             A_x = 0.0
#         try:
#             A_x = float(A_x)
#         except:
#             A_x = A_x.real
#         return min(1, max(0.0, A_x))
#
# def PHI_Q(partition):
#     """
#     This functions computes the interpretability index defined by Botta et al. 2009
#     in "Context adaptation of fuzzy systems through a multi-objective evolutionary approach"
#     However it uses an approximation for the resulting mu, because I honetly couldn't get one to work as described
#     :param partition:
#     :return: a real value indicating the interpretability of the partition
#     """
#     N = len(partition)
#     num = 0
#     denom = 0
#     for i in range(N-1):
#         for j in range(i+1, N):
#             dji = abs(j-i)
#             # num = num + ((1/dji)*(mu_q_dji(YuanFuzzyOrderingIndex(partition[i], partition[j]), y, dji)))
#             yuan = YuanFuzzyOrderingIndex(partition[i], partition[j])
#             mu = mu_q_dji_APPROX(yuan, dji)
#             print(i,"-",j, ": ", "yuan:", yuan, "mu: ", mu)
#             num = num + ((1/dji)*mu)
#             denom = denom + (1/dji)
#     return num/denom

generic_range = np.arange(0, 1.000001, 0.05)


""" Original variables """
# low_distance = fuzz.trapmf(generic_range,  [0, 0, 0, 0.5])
# mid_distance = fuzz.trapmf(generic_range,  [0, 0.5, 0.5, 1])
# high_distance = fuzz.trapmf(generic_range,  [0.5, 1, 1, 1])

# US
range_dist = np.arange(0, 4.000001, 0.05)
range_vol = np.arange(0, 100.000001, 0.05)
range_mov = np.arange(0, 1.000001, 0.05)

low_distance_us = fuzz.gaussmf(range_dist,  0.5, 0.15)
mid_distance_us = fuzz.gaussmf(range_dist,  1, 0.3)
high_distance_us = fuzz.gaussmf(range_dist,  3, 0.5)
low_volume_us = fuzz.gaussmf(range_vol,  30, 10)
mid_volume_us = fuzz.gaussmf(range_vol,  60, 10)
high_volume_us = fuzz.gaussmf(range_vol,  90, 10)
low_mov_us = fuzz.gaussmf(range_mov,  0.1, 0.1)
mid_mov_us = fuzz.gaussmf(range_mov,  0.4, 0.1)
high_mov_us = fuzz.gaussmf(range_mov,  0.7, 0.1)

low_distance_a = fuzz.gaussmf(range_dist,  0.46, 0.15)
mid_distance_a = fuzz.gaussmf(range_dist,  0.92, 0.3)
high_distance_a = fuzz.gaussmf(range_dist,  2.5, 0.5)
low_volume_a = fuzz.gaussmf(range_vol,  30, 10)
mid_volume_a = fuzz.gaussmf(range_vol,  60, 10)
high_volume_a = fuzz.gaussmf(range_vol,  90, 10)
low_mov_a = fuzz.gaussmf(range_mov,  0.2, 0.1)
mid_mov_a = fuzz.gaussmf(range_mov,  0.6, 0.1)
high_mov_a = fuzz.gaussmf(range_mov,  0.8, 0.1)

#us 5-10-50
low_distance_1 =fuzz.trapmf(range_dist, [0.097372727,	0.097372727,	0.097372727,	0.402627273]	)
mid_distance_1 =fuzz.trapmf(range_dist, [0.194745453,	0.5,	0.5,	0.805254547]	)
high_distance_1 =fuzz.trapmf(range_dist, [0.597372727,	0.902627273,	0.902627273,	0.902627273]	)

low_distance_1 =fuzz.trapmf(range_dist, [0.143738919,	0.143738919,	3.252112203,	3.723362553])
mid_distance_1 =fuzz.trapmf(range_dist, [0.143738919,	0.143738919,	4.475372301,	4.475372301	])
high_distance_1 =fuzz.trapmf(range_dist, [0.895748667,	1.909400722,	4.475372301,	4.475372301])

low_volume_1 = fuzz.trapmf(range_vol, [59.79513964,	59.79513964,	80.32297403,	80.32297403]	)
mid_volume_1 = fuzz.trapmf(range_vol, [59.79513964,	59.79513964,	80.32297403,	80.32297403]	)
high_volume_1 = fuzz.trapmf(range_vol, [59.79513964,	59.79513964,	80.32297403,	80.32297403]	)
low_mov_1 = fuzz.trapmf(range_mov, [0.022516645,	0.046838482,	0.089440172,	0.153657727]	)
mid_mov_1 = fuzz.trapmf(range_mov, [0.080491707,	0.192838285,	0.278041665,	0.342773871]	)
high_mov_1 =     fuzz.trapmf(range_mov, [0.269607851,	0.357632592,	0.400234282,	0.400748933])

#austria
#correct info = Ture

# correct info = True, contextualize = True, min_nr_dp = 10, after 1k datapoints (_16)
low_distance_1_a =fuzz.trapmf(range_dist,  [0.213138969,	0.376142923,	0.441768084,	0.551248366	        ])
mid_distance_1_a =fuzz.trapmf(range_dist,  [0.385923464,	0.787993194,	0.963287547,	1.251101039	        ])
high_distance_1_a =fuzz.trapmf(range_dist, [2.080875756,	2.214860859,	2.405463674,	2.512595406	        ])
low_volume_1_a = fuzz.trapmf(range_vol,    [-5.717691702,	-5.717691702,	85.41920794,	85.41920794		    ])
mid_volume_1_a = fuzz.trapmf(range_vol,    [33.89740484,		34.30340202,		75.87686967,	80.0698445	])
high_volume_1_a = fuzz.trapmf(range_vol,   [-0.516274446,	0.697433726,		90.41836122,	100.19383		])
low_mov_1_a = fuzz.trapmf(range_mov,       [-0.081202341,	0.273395319,		0.367834611,	0.410262781	    ])
mid_mov_1_a = fuzz.trapmf(range_mov,       [0.315081273,		0.491466826,		0.636091977,	0.730117771	])
high_mov_1_a =     fuzz.trapmf(range_mov,  [0.391265731,		0.716643337,		0.840860587,	0.85832328  ])

# correct info = True, contextualize = False, min_nr_dp = 10, after 1k datapoints (_0)
low_distance_1_a =fuzz.trapmf(range_dist,  [0.086675307,	0.367377329,	0.498951241,	0.677712029	])
mid_distance_1_a =fuzz.trapmf(range_dist,  [0.175898215,	0.75075009,	1.059497298,	1.461126288	])
high_distance_1_a =fuzz.trapmf(range_dist, [1.433592596,	2.148003971,	2.612935768,	3.159878566	])
low_volume_1_a = fuzz.trapmf(range_vol,    [2.716028357,	3.191899751,	46.45894215,	50.76175981	])
mid_volume_1_a = fuzz.trapmf(range_vol,    [33.89740484,	34.30408946,	75.87133284,	80.0698445	])
high_volume_1_a = fuzz.trapmf(range_vol,   [51.1791373,	51.66459559,	95.80423674,	100.19383	])
low_mov_1_a = fuzz.trapmf(range_mov,       [-0.081202341,	0.124735178,	0.217858037,	0.3235512	])
mid_mov_1_a = fuzz.trapmf(range_mov,       [0.315081273,	0.535524357,	0.636953092,	0.730117771	])
high_mov_1_a =     fuzz.trapmf(range_mov,  [0.473670965,	0.698338482,	0.796907485,	0.936240084])

# correct info = True, contextualize = True, min_nr_dp = 10, after 8k datapoints (EXPECTED TO BE _24)

# correct info = True, contextualize = False, min_nr_dp = 10, after 8k datapoints (_8)
low_distance_1_a =fuzz.trapmf(range_dist,  [-0.050195122,	0.384940146,	0.516976903,	0.717093383	])
mid_distance_1_a =fuzz.trapmf(range_dist,  [0.066718176	,	0.836887887,	1.139171573,	1.321035095	])
high_distance_1_a =fuzz.trapmf(range_dist, [1.015100129	,	2.317311439,	2.60643965,	3.159878566	    ])
low_volume_1_a = fuzz.trapmf(range_vol,    [-3.963446985,	36.37182531,	41.31856868,	45.77269302	])
mid_volume_1_a = fuzz.trapmf(range_vol,    [25.20060706	,	72.46847056,	76.80016478,	82.66887484	])
high_volume_1_a = fuzz.trapmf(range_vol,   [48.03908378	,	94.83166983,	100.5705018,	105.7385552	])
low_mov_1_a = fuzz.trapmf(range_mov,       [-0.090713389,	0.139353187,	0.224072071,	0.319720116	])
mid_mov_1_a = fuzz.trapmf(range_mov,       [0.249646938	,	0.545036546,	0.647123445,	0.705952924	])
high_mov_1_a =     fuzz.trapmf(range_mov,  [0.473670965	,	0.737843196,	0.826697916,	0.935809781 ])

#correct info = False
# correct info = False, contextualize = True, min_nr_dp = 10, after 1k datapoints (_17)
low_distance_1_a =fuzz.trapmf(range_dist,  [0.198291118		,0.198291118	,0.669066745	,0.669066745	])
mid_distance_1_a =fuzz.trapmf(range_dist,  [0.156624954		,0.77483626	,1.089592132	,2.693599919	])
high_distance_1_a =fuzz.trapmf(range_dist, [0.157166604		,1.00777303	,1.646924477	,3.364940138	])
low_volume_1_a = fuzz.trapmf(range_vol,    [2.716028357		,43.76562942	,45.66510029	,50.76175981	])
mid_volume_1_a = fuzz.trapmf(range_vol,    [13.79986789		,89.80777471	,91.8213803	,100.19383	])
high_volume_1_a = fuzz.trapmf(range_vol,   [0.87935758		,0.87935758	,103.3335693	,103.3335693	])
low_mov_1_a = fuzz.trapmf(range_mov,       [-0.081202341	,0.294695558	,0.485254591	,0.589363897	])
mid_mov_1_a = fuzz.trapmf(range_mov,       [-0.081202341	,0.338232613	,0.576668499	,0.896887125	])
high_mov_1_a =     fuzz.trapmf(range_mov,  [0.593104632		,0.618008881	,0.650015723	,0.660265028])
# correct info = False, contextualize = False, min_nr_dp = 10, after 1k datapoints (_1)
low_distance_1_a =fuzz.trapmf(range_dist,  [0.086675307	, 	0.873224141	, 	2.270420337	, 3.4062115	])
mid_distance_1_a =fuzz.trapmf(range_dist,  [0.155296066	, 	0.821536929	, 	2.08724737	, 3.032389109	])
high_distance_1_a =fuzz.trapmf(range_dist, [0.148638305	, 	0.918279756	, 	2.254831277	, 3.159878566	])
low_volume_1_a = fuzz.trapmf(range_vol,    [-5.717691702, 	-4.851424932, 	74.00747906	, 81.85084589	])
mid_volume_1_a = fuzz.trapmf(range_vol,    [8.209697092	, 	9.102258656	, 	85.02549201	, 92.42672188	])
high_volume_1_a = fuzz.trapmf(range_vol,   [25.63293691	, 	26.40158796	, 	96.37404692	, 103.3335693	])
low_mov_1_a = fuzz.trapmf(range_mov,       [-0.070824223, 	0.336997794	, 	0.534132781	, 0.936240084	])
mid_mov_1_a = fuzz.trapmf(range_mov,       [-0.024737456, 	0.408972778	, 	0.641183958	, 0.907578152	])
high_mov_1_a =     fuzz.trapmf(range_mov,  [0.18241491	, 	0.548539932	, 	0.76407758	, 0.981103187])
# correct info = False, contextualize = True, min_nr_dp = 10, after 8k datapoints (_25)
# correct info = False, contextualize = False, min_nr_dp = 10, after 8k datapoints (_9)
low_distance_1_a =fuzz.trapmf(range_dist,  [0.023777286		, 1.081821918	, 	1.312205586	, 3.023505954	])
mid_distance_1_a =fuzz.trapmf(range_dist,  [-0.012930435	, 0.860106659	, 	1.069023923	, 2.916673945	])
high_distance_1_a =fuzz.trapmf(range_dist, [0.332989274		, 1.333452118	, 	1.551257548	, 3.16853632	])
low_volume_1_a = fuzz.trapmf(range_vol,    [-5.717691702	, -4.802798457, 	78.4419876	, 86.72619263	])
mid_volume_1_a = fuzz.trapmf(range_vol,    [5.045078045		, 5.895589982	, 	67.9188551	, 74.76906269	])
high_volume_1_a = fuzz.trapmf(range_vol,   [19.35474401		, 20.21497278	, 	97.8868265	, 105.7385552	])
low_mov_1_a = fuzz.trapmf(range_mov,       [-0.136233014	, 0.352325731	, 	0.555313259	, 0.812137947	])
mid_mov_1_a = fuzz.trapmf(range_mov,       [-0.029849143	, 0.416744096	, 	0.619626182	, 0.880219031	])
high_mov_1_a =     fuzz.trapmf(range_mov,  [0.010006998		, 0.509400246	, 	0.709983293	, 0.935809781])

# _3, i.e., _1 but with min certainty 0.2
low_distance_1_a =fuzz.trapmf(range_dist,  [0.214637873	, 	0.388317583	, 0.521729832	, 0.717892665		])
mid_distance_1_a =fuzz.trapmf(range_dist,  [0.127002404	, 	0.774750081	, 1.157554823	, 1.461126288		])
high_distance_1_a =fuzz.trapmf(range_dist, [0.5			, 	0.6557612	, 0.783460692	, 1		])
low_volume_1_a = fuzz.trapmf(range_vol,    [2.716028357	, 	3.1856519	, 40.0375336	, 43.81998346		])
mid_volume_1_a = fuzz.trapmf(range_vol,    [13.79986789	, 	14.51189544	, 74.21405141	, 80.0698445		])
high_volume_1_a = fuzz.trapmf(range_vol,   [0.5			, 	0.504946373	, 0.955215269	, 1		])
low_mov_1_a = fuzz.trapmf(range_mov,       [-0.081202341, 	0.172319824	, 0.301716455	, 0.513397964		])
mid_mov_1_a = fuzz.trapmf(range_mov,       [-0.002768123, 	0.413729226	, 0.574823427	, 0.767667827		])
high_mov_1_a =     fuzz.trapmf(range_mov,  [0.5			, 	0.755125372	, 0.874676302	, 1])

# _11, I.E., _9 but with min certainty 0.2
low_distance_1_a =fuzz.trapmf(range_dist,  [0.02808467		, 0.282500626	, 0.525207475	, 0.69582755	])
mid_distance_1_a =fuzz.trapmf(range_dist,  [0.066718176		, 0.783168909	, 1.036488963	, 1.152447313	])
high_distance_1_a =fuzz.trapmf(range_dist, [0.5				, 0.685756389	, 0.86750127	, 1	])
low_volume_1_a = fuzz.trapmf(range_vol,    [1.563531058		, 1.97737632	, 40.10221489	, 43.90064208	])
mid_volume_1_a = fuzz.trapmf(range_vol,    [9.57126019		, 10.16979141	, 75.85448442	, 82.66887484	])
high_volume_1_a = fuzz.trapmf(range_vol,   [0.5				, 0.504946229	, 0.955215851	, 1	])
low_mov_1_a = fuzz.trapmf(range_mov,       [-0.136233014	, 0.202400864	, 0.287491037	, 0.354701179	])
mid_mov_1_a = fuzz.trapmf(range_mov,       [-0.027133816	, 0.416035717	, 0.554578237	, 0.705393727	])
high_mov_1_a =     fuzz.trapmf(range_mov,  [0.5				, 0.776352092	, 0.863958308	, 1])


# like _0, but with normalized changes
low_distance_1_a =fuzz.trapmf(range_dist,  [0.086675307	, 0.413891117	, 0.472083527, 	0.677712029	])
mid_distance_1_a =fuzz.trapmf(range_dist,  [0.175898215	, 0.86444415	, 1.00369138, 	1.461126288	])
high_distance_1_a =fuzz.trapmf(range_dist, [1.433592596	, 2.334322634	, 2.505222429, 	3.159878566	])
low_volume_1_a = fuzz.trapmf(range_vol,    [2.716028357	, 26.36004123	, 38.92159449, 	50.76175981	])
mid_volume_1_a = fuzz.trapmf(range_vol,    [33.89740484	, 53.1266712	, 65.08894526, 	80.0698445	])
high_volume_1_a = fuzz.trapmf(range_vol,   [51.1791373	, 76.28898618	, 89.10923578, 	100.19383	])
low_mov_1_a = fuzz.trapmf(range_mov,       [-0.081202341, 	0.059411834, 	0.197494294, 	0.3235512	])
mid_mov_1_a = fuzz.trapmf(range_mov,       [0.315081273	, 0.486717399, 	0.63252195	, 0.730117771	])
high_mov_1_a =     fuzz.trapmf(range_mov,  [0.473670965	, 0.62721338, 	0.785338068, 	0.936240084])


plt.figure(figsize=(12, 8))
plt.subplot(321)
plt.plot(range_dist, low_distance_us, 'k--')
plt.plot(range_dist, mid_distance_us, 'k--')
plt.plot(range_dist, high_distance_us, 'k--')
plt.plot(range_dist, low_distance_1)
plt.plot(range_dist, mid_distance_1)
plt.plot(range_dist, high_distance_1)
plt.subplot(322)
plt.plot(range_dist, low_distance_a, 'k--')
plt.plot(range_dist, mid_distance_a, 'k--')
plt.plot(range_dist, high_distance_a, 'k--')
plt.plot(range_dist, low_distance_1_a)
plt.plot(range_dist, mid_distance_1_a)
plt.plot(range_dist, high_distance_1_a)
plt.subplot(323)
plt.plot(range_vol, low_volume_us, 'k--')
plt.plot(range_vol, mid_volume_us, 'k--')
plt.plot(range_vol, high_volume_us, 'k--')
plt.plot(range_vol, low_volume_1)
plt.plot(range_vol, mid_volume_1)
plt.plot(range_vol, high_volume_1)
plt.subplot(324)
plt.plot(range_vol, low_volume_a, 'k--')
plt.plot(range_vol, mid_volume_a, 'k--')
plt.plot(range_vol, high_volume_a, 'k--')
plt.plot(range_vol, low_volume_1_a)
plt.plot(range_vol, mid_volume_1_a)
plt.plot(range_vol, high_volume_1_a)
plt.subplot(325)
plt.plot(range_mov, low_mov_us, 'k--')
plt.plot(range_mov, mid_mov_us, 'k--')
plt.plot(range_mov, high_mov_us, 'k--')
plt.plot(range_mov, low_mov_1)
plt.plot(range_mov, mid_mov_1)
plt.plot(range_mov, high_mov_1)
plt.subplot(326)
plt.plot(range_mov, low_mov_a, 'k--')
plt.plot(range_mov, mid_mov_a, 'k--')
plt.plot(range_mov, high_mov_a, 'k--')
plt.plot(range_mov, low_mov_1_a)
plt.plot(range_mov, mid_mov_1_a)
plt.plot(range_mov, high_mov_1_a)

# low_distance_new_V1 = fuzz.trapmf(generic_range,  [-0.065949382, 0.071772021, 0.114878281, 0.565949382])
# mid_distance_new_V1 = fuzz.trapmf(generic_range,  [-0.131898763, 0.151176442, 0.23738896, 1.131898763])
# high_distance_new_V1 = fuzz.trapmf(generic_range,  [0.434050618, 0.579404421, 0.62251068, 1.065949382])



#
# plt.plot(generic_range, low_distance_new_V1, 'k')
# plt.plot(generic_range, mid_distance_new_V1, 'k')
# plt.plot(generic_range, high_distance_new_V1, 'k')

plt.show()

exit()

plt.figure(figsize=(8, 3))
low_distance_new_V2 = fuzz.trapmf(generic_range, [0,	0.071775038, 0.112554717, 0.5])
mid_distance_new_V2 = fuzz.trapmf(generic_range,  [0,	0.149804947,	0.231364306, 1])
high_distance_new_V2 = fuzz.trapmf(generic_range,  [0.5, 0.578029909, 0.618809589, 1])

plt.plot(generic_range, low_distance, 'k--')
plt.plot(generic_range, mid_distance, 'k--')
plt.plot(generic_range, high_distance, 'k--')
plt.plot(generic_range, low_distance_new_V2, 'k')
plt.plot(generic_range, mid_distance_new_V2, 'k')
plt.plot(generic_range, high_distance_new_V2, 'k')

plt.show()
# exit()
#
# distances = [0.095699341, 0.185474561, 0.118997233, 0.179339013, 0.233951187, 0.129014294, 0.098996224, 0.177271055, 0.20297606, 0.200890885, 0.188603826, 0.29614285, 0.204363169, 0.201165039, 0.181544017, 0.20842906, 0.049815282, 0.181570896, 0.149408158, 0.23862916, 0.163426592, 0.129513861, 0.197815129, 0.243493332, 0.172296494, 0.14568949, 0.166757906, 0.186274139, 0.233925595, 0.139217787, 0.219924959, 0.236213438, 0.194542069, 0.195792675, 0.08848209, 0.193481438, 0.169266962, 0.123547663, 0.217461104, 0.224915126, 0.109599267, 0.117567472, 0.109609925, 0.084655781, 0.209972284, 0.204394218, 0.175184501, 0.167406507, 0.300134911, 0.224197825, 0.199745379, 0.130754807, 0.197330212, 0.13602251, 0.199967429, 0.199904878, 0.098907312, 0.210569445, 0.079629103, 0.156760974, 0.131097696, 0.190614644, 0.193180511, 0.119089094, 0.164602956, 0.13358793, 0.06937321, 0.17402693, 0.199652229, 0.121495902, 0.159134302, 0.086676849, 0.140405648, 0.118063643, 0.102678686, 0.239406185, 0.207364329, 0.134153629, 0.233412397, 0.066291765, 0.096426488, 0.179267801, 0.212278858, 0.098651166, 0.134852086, 0.232388015, 0.158157809, 0.213074581, 0.202231037, 0.215367912, 0.269159162, 0.210606785, 0.207846831, 0.166936167, 0.270574708, 0.157963816, 0.200187978, 0.173563176, 0.167992216, 0.177167276, 0.189517191, 0.112627809, 0.131282804, 0.097225389, 0.12436354, 0.114690265, 0.141270231, 0.17610821, 0.111568812, 0.193733176, 0.250605173, 0.151313785, 0.174483578, 0.021430715, 0.221603865, 0.139286663, 0.048591718, 0.108138621, 0.13617477, 0.176328853, 0.176909894, 0.150897619, 0.132489366, 0.219515885, 0.169142716, 0.093623757, 0.17462811, 0.165257229, 0.111747032, 0.182877186, 0.204215581, 0.246602608, 0.175519702, 0.095764091, 0.248728329, 0.16292992, 0.102265382, 0.127462249, 0.229096034, 0.14011806, 0.202824776, 0.20055956, 0.14350361, 0.177155888, 0.223182877, 0.245332337, 0.229842495, 0.161872615, 0.207921928, 0.061275069, 0.164326879, 0.146603044, 0.148071375, 0.243466844, 0.131357907, 0.294245476, 0.199199107, 0.160149658, 0.173606779, 0.129891558, 0.146434025, 0.171588947, 0.168535026, 0.140660939, 0.100374375, 0.199962081, 0.171809649, 0.227372377, 0.109692961, 0.216729047, 0.264554489, 0.271132863, 0.115193876, 0.180889232, 0.156312057, 0.193469191, 0.197705648, 0.191895864, 0.159670965, 0.029400817, 0.099108753, 0.116520266, 0.200131255, 0.141910765, 0.266488274, 0.142486601, 0.129377984, 0.161312373, 0.171837999, 0.215249221, 0.250709882, 0.16306502, 0.200884667, 0.125048169, 0.260168917, 0.197813678, 0.18662635, 0.183592718, 0.24157661, 0.119736989, 0.15029619, 0.114366381, 0.192905254, 0.078059824, 0.120734464, 0.070889047, 0.133114044, 0.153986779, 0.165032644, 0.16319904, 0.250598262, 0.259437863, 0.254825459, 0.149123529, 0.107350188, 0.135555269, 0.18014424, 0.184076852, 0.073737575, 0.156005692, 0.195124685, 0.129452619, 0.120430055, 0.104670061, 0.075085703, 0.125507373, 0.172242006, 0.153701928, 0.246771169, 0.144413418, 0.250720702, 0.240119466, 0.227145017, 0.072871454, 0.188301486, 0.11859269, 0.138583161, 0.199639035, 0.286263306, 0.092934319, 0.162893385, 0.109947759, 0.243449297, 0.080397315, 0.179738062, 0.190130208, 0.187697529, 0.295351027, 0.267958549, 0.207499007, 0.173893554, 0.229440284, 0.166161199, 0.203519267, 0.20167308, 0.06855448, 0.184768764, 0.219152506, 0.159079803, 0.190003666, 0.148001895, 0.111653426, 0.232198553, 0.14976072, 0.135528245, 0.106336943, 0.201684038, 0.267964035, 0.150257007, 0.169678112, 0.169766625, 0.170840745, 0.103635132, 0.16335309, 0.155223722, 0.215232661, 0.182032572, 0.084087334, 0.214544662, 0.154629031, 0.255689636, 0.019760267, 0.159796648, 0.156625074, 0.209509802, 0.19655451, 0.169094282, 0.196404416, 0.117530638, 0.181940929, 0.179109683, 0.252417155, 0.252564254, 0.157832542, 0.215637514, 0.204098006, 0.156349372, 0.210950201, 0.12598579, 0.133044306, 0.196943661, 0.166313018, 0.137521629, 0.149836847, 0.266860296, 0.230908445, 0.120140702, 0.136837317, 0.199528891, 0.124432122, 0.146754777, 0.143337448, 0.054036245, 0.070639553, 0.20437247, 0.139863564, 0.113867947, 0.272257374, 0.161632273, 0.208351799, 0.15320799, 0.171807547, 0.188075097, 0.201876702, 0.084650927, 0.188266334, 0.176408429, 0.168015141, 0.204769156, 0.194543949, 0.116487467, 0.12959346, 0.179955253, 0.049195004, 0.175543143, 0.093852244, 0.0754487, 0.127157438, 0.140930823, 0.110849606, 0.298887912, 0.189150986, 0.225198653, 0.211877086, 0.111195749, 0.128037191, 0.135244923, 0.118975087, 0.069946073, 0.197128505, 0.16120542, 0.305973759, 0.196894776, 0.174104513, 0.147870765, 0.176831833, 0.143243259, 0.238831836, 0.254740154, 0.192709992, 0.185849705, 0.220396061, 0.22717764, 0.172720816, 0.130984106, 0.182685079, 0.096607573, 0.108953779, 0.172831224, 0.131749462, 0.177773284, 0.16128717, 0.164810259, 0.193067922, 0.218468999, 0.196507569, 0.158929784, 0.21271625, 0.261442485, 0.118789306, 0.154353728, 0.184255233, 0.180321846, 0.196659236, 0.035103476, 0.158864381, 0.249858795, 0.266264266, 0.12331787, 0.193647435, 0.250875804, 0.188169324, 0.201121284, 0.139277604, 0.070182056, 0.180823434, 0.175247329, 0.107990417, 0.232877616, 0.228633422, 0.236409518, 0.222298161, 0.178961497, 0.221437223, 0.132544, 0.217367873, 0.25783853, 0.256493355, 0.084221405, 0.1909946, 0.145062616, 0.113018062, 0.131209769, 0.038949838, 0.256033348, 0.168182532, 0.198208494, 0.076329567, 0.190228238, 0.117661408, 0.24369785, 0.140641836, 0.099183163, 0.107319157, 0.098128228, 0.106227455, 0.140295818, 0.217954101, 0.166012063, 0.153632554, 0.148414382, 0.225033904, 0.141146226, 0.10586205, 0.240203965, 0.178050552, 0.071959627, 0.151588073, 0.21617831, 0.158881397, 0.141472519, 0.260604087, 0.192413427, 0.156699556, 0.193783027, 0.214501404, 0.182756603, 0.227885169, 0.241370828, 0.1077756, 0.205716319, 0.222716531, 0.175893695, 0.140164791, 0.169143875, 0.146357311, 0.132319856, 0.148877579, 0.148957652, 0.16798987, 0.247851215, 0.13134302, 0.21286664, 0.132172235, 0.083531672, 0.168587437, 0.110609009, 0.045189512, 0.163381189, 0.088368244, 0.108349049, 0.047420277, 0.131691615, 0.096132992, 0.199485924, 0.06872611, 0.197063602, 0.210795766, 0.137084941, 0.227948001, 0.191685974, 0.1971363, 0.122028228, 0.138166484, 0.199612698, 0.123636341, 0.138334906, 0.194740555, 0.090785188, 0.010461545, 0.237156043, 0.13012835, 0.193191173, 0.132447069, 0.137470573, 0.209145985, 0.180504592, 0.164365944, 0.156498566, 0.19123296, 0.146142058, 0.256792921, 0.056097829, 0.11729893, 0.158576743, 0.17179049, 0.161934746, 0.146284699, 0.146119719, 0.129623073, 0.167143062, 0.144287694, 0.098113467, 0.125705288, 0.184711189, 0.137309316, 0.048025593, 0.181345789, 0.160223524, 0.199695887, 0.22123282, 0.131300545, 0.206687064, 0.244272213, 0.083063996, 0.162987098, 0.204872553, 0.236627345, 0.219169506, 0.226833351, 0.254125747, 0.116164262, 0.189179804, 0.17707235, 0.097616552, 0.124504266, 0.266754076, 0.156798133, 0.181845523, 0.152181037, 0.202285736, 0.18214557, 0.099715166, 0.120331015, 0.043773979, 0.198005727, 0.190537648, 0.15598267, 0.107346929, 0.09983456, 0.181204188, 0.181923506, 0.153226901, 0.162389234, 0.118900511, 0.218129611, 0.234876202, 0.188981259, 0.263399022, 0.230936154, 0.073503359, 0.220164474, 0.207303366, 0.160166576, 0.200756406, 0.078478653, 0.062359001, 0.139469283, 0.166751699, 0.08332154, 0.293788647, 0.066471846, 0.143137425, 0.208878217, 0.195317341, 0.144020611, 0.232330091, 0.196804561, 0.138711069, 0.110113234, 0.163789927, 0.159661434, 0.013587821, 0.349113146, 0.085119716, 0.243202047, 0.120338795, 0.190664369, 0.129958176, 0.091850203, 0.17319544, 0.131560715, 0.174149925, 0.195441926, 0.18367244, 0.249004934, 0.153268571, 0.131052596, 0.145278011, 0.234464144, 0.196134081, 0.156322706, 0.183796716, 0.194400514, 0.113008188, 0.264396661, 0.27549231, 0.16471318, 0.051737205, 0.180974085, 0.109170571, 0.195595623, 0.172967545, 0.208322469, 0.167469117, 0.21456021, 0.190258399, 0.196714459, 0.158824863, 0.200449433]
# mv_new = []
# mv_old = []
# for d in distances:
#     mv_new.append(fuzz.interp_membership(generic_range, mid_distance_new, d))
#     mv_old.append(fuzz.interp_membership(generic_range, mid_distance, d))
#
# print(mv_old)
# print(mv_new)
# exit()

def f(xy, *fuzzy_sets):
    """ To determine the intersection between two functions """
    x, y = xy
    fs1, fs2 = fuzzy_sets
    z = np.array([y - fs1.get_value(x), y - fs2.get_value(x)])
    return z

def f_skfuzzy(xy, *fuzzy_sets):
    generic_range = np.arange(0, 1.00000000001, 0.01)
    x, y = xy
    fs1, fs2 = fuzzy_sets
    z = np.array([y - fuzz.interp_membership(generic_range, fs1, x), y - fuzz.interp_membership(generic_range, fs2, x)])
    return z

def mfa1(val):
    x = np.arange(0, 1.00000000001, 0.05)
    return fuzz.interp_membership(x, A1, val)
def mfa2(val):
    x = np.arange(0, 1.00000000001, 0.05)
    return fuzz.interp_membership(x, A2, val)

def crossing_point_value(mf1, mf2):
    last_x = 0.0
    last_y = 0.0
    cp_vn = -1
    try:
        sol = fsolve(f, np.array([last_x, last_y]), args=(mf1, mf2))
        print(sol)
        cp_vn = float(sol[1])
        """ This is just a trick to help the solver finding the intersection point at the next iteration
                    We know we are moving forward in the domain of discourse, so I move forward the initial estimation
                    if there was an intersection, then I give as a starting estimation the end of the current first fuzzy set,
                    ortherwise I give as a starting estimation the end of the second.
        NOTE: INDEED THIS IS A SORT OF HEURISTIC TO KNOW WHERE TO PUT (INSTEAD OF SEARCH) THE INTERSECTION POINT"""
        # if cp_vn > 0.0:
        #     last_x = mf1._funpointer._d  # todo  this is hardcoded assuming trapezoid
        # else:
        #     last_x = mf2._funpointer._d
        # last_y = sol[1]
    except:
        print("lol")
        pass
    return cp_vn

def PHI_Q(partition):
    """
    This functions computes the interpretability index defined by Botta et al. 2009
    in "Context adaptation of fuzzy systems through a multi-objective evolutionary approach"
    :param partition:
    :return: a real value indicating the interpretability of the partition
    """
    N = len(partition)
    num = 0
    denom = 0
    for i in range(N - 1):
        for j in range(i + 1, N):
            dji = abs(j-i)
            # y = crossing_point_value(partition[i], partition[j])
            yuan = YuanFuzzyOrderingIndex(partition[i], partition[j])
            mu_yuan = mu_q_dji(yuan, dji)
            print("(", i, ",", j, ")", yuan, mu_yuan)
            num = num + ((1/dji)*(mu_yuan))
            denom = denom + (1/dji)
    return num/denom
#
# A1b = fuzz.trapmf(generic_range, [0.0, 0.33,0.33, 0.66])
# A2b = fuzz.trapmf(generic_range, [0.33, 0.66,0.66, 0.99])

plt.figure(figsize=(6, 2))
A1 = fuzz.trapmf(generic_range, [0.0, 0.0, 0.05, 0.2])
A2 = fuzz.trapmf(generic_range, [0.05, 0.2, 0.3, 0.45])
A3 = fuzz.trapmf(generic_range, [0.3, 0.45, 0.55, 0.7])
A4 = fuzz.trapmf(generic_range, [0.55, 0.7, 0.8, 0.95])
A5 = fuzz.trapmf(generic_range, [0.8, 0.95, 1.0, 1.0])
plt.plot(generic_range, A1)
plt.plot(generic_range, A2)
plt.plot(generic_range, A3)
plt.plot(generic_range, A4)
plt.plot(generic_range, A5)
plt.show()
partition = [A1, A2, A3, A4, A5]
print(PHI_Q(partition))


partitionv1 = [low_distance_new_V1, mid_distance_new_V1, high_distance_new_V1]
partitionv2 = [low_distance_new_V2, mid_distance_new_V2, high_distance_new_V2]
print(PHI_Q(partitionv1))
print(PHI_Q(partitionv2))
exit()

cut_range = np.arange(0.0, 1.005, 0.01)

mfv = []
for i in cut_range:
    mfv.append(mu_q_dji_APPROX(i, 1))
plt.plot(cut_range, np.array(mfv), 'k')
mfv = []
for i in cut_range:
    mfv.append(mu_q_dji_APPROX(i, 2))
plt.plot(cut_range, np.array(mfv), 'k')
mfv = []
for i in cut_range:
    mfv.append(mu_q_dji_APPROX(i, 3))
plt.plot(cut_range, np.array(mfv), 'k')
mfv = []
for i in cut_range:
    mfv.append(mu_q_dji_APPROX(i, 4))
plt.plot(cut_range, np.array(mfv), 'k')

plt.show()

exit()

def mu_q_dji_APPROX(yuan, dji):
    gen_range = np.arange(0, 1.005, 0.01)
    _theta_1 = 1.01
    _k_GP_1 = 7
    if dji == 1:
        mf = fuzz.trapmf(gen_range, [0.0, 0.95, 0.95, 1.2])
        A_x = fuzz.interp_membership(gen_range, mf, yuan)
        if A_x < _theta_1:
            A_x = (_theta_1 ** (1 - _k_GP_1)) * (A_x ** _k_GP_1)
        else:
            A_x = 1 - (((1 - _theta_1) ** (1 - _k_GP_1)) * ((1 - A_x) ** _k_GP_1))
        try:
            A_x = float(A_x)
        except:
            A_x = A_x.real
        return min(1, max(0.0, A_x))
    else:
        _theta_dji = 1.01
        _k_GP_dji = 10
        mf = fuzz.trapmf(gen_range, [min(0.95,((0.475*dji)-0.808333)), 1.0, 1.0, 1.2])
        A_x = fuzz.interp_membership(gen_range, mf, yuan)
        try:
            if A_x < _theta_dji:
                A_x = (_theta_dji ** (1 - _k_GP_dji)) * (A_x ** _k_GP_dji)
            else:
                A_x = 1 - (((1 - _theta_dji) ** (1 - _k_GP_dji)) * ((1 - A_x) ** _k_GP_dji))
        except:
            A_x = 0.0
        try:
            A_x = float(A_x)
        except:
            A_x = A_x.real
        return min(1, max(0.0, A_x))



# Display and compare defuzzification results against membership function
plt.figure(figsize=(8, 5))

cut_range = np.arange(0.8, 1.005, 0.01)
cut_range = generic_range

mfv = []
for i in cut_range:
    mfv.append(mu_q_dji_APPROX(i, 1))
plt.plot(cut_range, np.array(mfv), 'k')
mfv = []
for i in cut_range:
    mfv.append(mu_q_dji_APPROX(i, 2))
plt.plot(cut_range, np.array(mfv), 'k')
mfv = []
for i in cut_range:
    mfv.append(mu_q_dji_APPROX(i, 3))
plt.plot(cut_range, np.array(mfv), 'k')
mfv = []
for i in cut_range:
    mfv.append(mu_q_dji_APPROX(i, 4))
plt.plot(cut_range, np.array(mfv), 'k')


plt.show()

exit()



def createNumpyRelMatrixFromData(data_cp, data_yuan):
    rel_matr = []
    for x in range(len(data_cp)):
        row = []
        for y in range(len(data_yuan)):
            row.append(min(data_cp[x], data_yuan[y]))
        rel_matr.append(row)
    return np.array(rel_matr)

# def R_QXP2(yuan, crossing):
#     crossing_point_value_data = [2.246663578009097e-36, 1.0, 0.13159588829662996, 1.0, 0.5, 0.37700799475187513, 0.5, 5.2706227954994316e-36, 1.0,
#      1.0, 0.5, 0.0, 1.0, 0.5587288714557492, 0.6761512072694331, 1.0, 0.18000063822066995, 1.0, 1.0, 0.993152854724899,
#      0.8203371238149199, 0.0, 2.049079508025179e-39, 0.247151296114683, 1.0, 0.48086767269324304,
#      2.3748659306456527e-37, 4.515367675096112e-36, 0.8609922253925926, 0.5, 0.8567267386517835, 1.0, 1.0,
#      0.47990851537739715, 0.5, 0.34889806059897205, 0.653924330951589, 1.1044136767960023e-36, 0.5, 1.0, 0.0, 1.0, 0.5,
#      1.0, 1.0, 0.5, 7.439593543758868e-37, 0.9930663156381095, 0.7434054856739433, 0.6978142559279038]
#     yuan_data = [0.3134154457523532, 0.6205581357168545, 0.9937706407054583, 0.4924466687933362, 0.7196216038041566,
#      0.9283859467805972, 0.2613033498073289, 0.563549218830921, 0.6238369276798604, 0.1357486784538107, 1.0,
#      0.37407358729296786, 0.17780271223448202, 0.7864126583737491, 0.6144561095348328, 0.990956260379931,
#      0.7049321323035856, 0.3594585739568385, 0.7104719571251265, 0.7200866599420492, 0.7513392960459615, 1.0,
#      0.9805786581534508, 0.5289207312302304, 0.868276648264347, 1.0, 0.20282152756884236, 0.26859947443750914,
#      0.8029494424941472, 0.7624798276933284, 0.5154552914872119, 0.2015290276839075, 0.9246749587777074,
#      0.8882724242554829, 0.9521498300399678, 0.8139933371463337, 0.233904045907351, 0.6790915937691151,
#      0.7411494410166545, 1.0, 0.5535512378787001, 0.6860178858585932, 0.46837718896260777, 0.053653702624054334,
#      0.898323121026916, 0.49383731931894614, 0.8185179945872668, 0.8226234821622226]
#
#     crossing_point_value_data = [2.246663578009097e-36, 1.0, 0.13159588829662996, 1.0, 0.5, 0.37700799475187513, 0.5,
#                                  5.2706227954994316e-36, 1.0,
#                                  1.0, 0.5, 0.0, 1.0, 0.5587288714557492, 0.6761512072694331, 1.0, 0.18000063822066995,
#                                  1.0, 1.0, 0.993152854724899,
#                                  0.8203371238149199, 0.0, 2.049079508025179e-39, 0.247151296114683, 1.0,
#                                  0.48086767269324304,
#                                  4.515367675096112e-36, 0.8609922253925926, 0.5, 0.8567267386517835, 1.0, 1.0,
#                                  0.47990851537739715, 0.5, 0.34889806059897205, 0.653924330951589,
#                                  1.1044136767960023e-36, 0.5, 1.0, 0.0, 1.0, 0.5,
#                                  1.0, 1.0, 0.5, 0.9930663156381095, 0.7434054856739433, 0.6978142559279038]
#     yuan_data = [0.3134154457523532, 0.6205581357168545, 0.9937706407054583, 0.4924466687933362, 0.7196216038041566,
#                  0.9283859467805972, 0.2613033498073289, 0.563549218830921, 0.6238369276798604, 0.1357486784538107, 1.0,
#                  0.37407358729296786, 0.17780271223448202, 0.7864126583737491, 0.6144561095348328, 0.990956260379931,
#                  0.7049321323035856, 0.3594585739568385, 0.7104719571251265, 0.7200866599420492, 0.7513392960459615,
#                  1.0,
#                  0.9805786581534508, 0.5289207312302304, 0.868276648264347, 1.0, 0.20282152756884236,
#                  0.26859947443750914,
#                  0.8029494424941472, 0.7624798276933284, 0.5154552914872119, 0.2015290276839075, 0.9246749587777074,
#                  0.8882724242554829, 0.9521498300399678, 0.8139933371463337, 0.233904045907351, 0.6790915937691151,
#                  0.7411494410166545, 1.0, 0.5535512378787001, 0.6860178858585932, 0.46837718896260777,
#                  0.053653702624054334,
#                  0.898323121026916, 0.49383731931894614, 0.8185179945872668, 0.8226234821622226]
#
#
#     if (yuan < min(yuan_data)) or yuan > max(yuan_data):
#         return 0
#
#     # rel_matr = createNumpyRelMatrixFromData(crossing_point_value_data, yuan_data)
#     rel_matr = fuzz.cartprod(np.array(crossing_point_value_data), np.array(yuan_data))
#
#     index_yuan_value = closest(yuan_data, yuan)[1]
#     index_cp_value = closest(crossing_point_value_data, crossing)[1]
#     return rel_matr[index_cp_value][index_yuan_value]

def fU1minusL2(alpha, A1, A2):
    x = np.arange(0, 1.00000000001, 0.001)
    u_A1alpha = fuzz.lambda_cut_boundaries(x, A1, alpha)[1]
    l_A2alpha = fuzz.lambda_cut_boundaries(x, A2, alpha)[0]
    if u_A1alpha>l_A2alpha:
        return u_A1alpha-l_A2alpha
    return 0

def fL1minusU2(alpha, A1, A2):
    x = np.arange(0, 1.00000000001, 0.001)
    l_A1alpha = fuzz.lambda_cut_boundaries(x, A1, alpha)[0]
    u_A2alpha = fuzz.lambda_cut_boundaries(x, A2, alpha)[1]
    if l_A1alpha>u_A2alpha:
        return l_A1alpha-u_A2alpha
    return 0

def DeltaA1A2(A1, A2) -> float:
    integral_U1minusL2 = integrate.quad(lambda alpha: fU1minusL2(alpha, A1, A2), 0.0, 1.0)
    integral_L1minusU2 = integrate.quad(lambda alpha: fL1minusU2(alpha, A1, A2), 0.0, 1.0)
    # print(integral_U1minusL2)
    # print(integral_L1minusU2)
    integral = integral_U1minusL2[0]+integral_L1minusU2[0]
    # print(integral)
    return integral

def YuanFuzzyOrderingIndex(A1, A2):
    """
    :param A1: membership function 1
    :param A2: membership function 2
    :return: a real value, obtained calculating the Yuan's fuzzy ordering index
    """
    return DeltaA1A2(A2, A1)/(DeltaA1A2(A1, A2)+DeltaA1A2(A2, A1))



def mu_q_dji(x, y, dji):
    # v_xyp_dji = getV_xp_dji(dji, y)
    # rqxpxy = R_QXP(x)
    v = fuzz.fuzzy_min(y, getV_xp_dji_fun(dji), x, R_QXP2)
    return max(0.0, min(v, 1.0))

# print(mu_q_dji(0.8, 0.5, 1))
# exit()




#
# # y = crossing_point_value(mfa1, mfa2)
# # print(y)
# #
#
# # x = np.arange(0.0, 1.05, 0.1)
# R_Q_list = []
# rqq = []
# for v in x:
#     R_Q_list.append([v, R_QXP(v)])
#     rqq.append(R_QXP(v))
# R_Q_2dnparray = np.array(R_Q_list)
#
# val = []
# for i in np.arange(0.0, 1.0, 0.01):
#     yuan = YuanFuzzyOrderingIndex(A1, A2)
#     yuan = i
#     rel = R_QXP(yuan)
#     # print(rel)
#     xp = getV_xp_dji(1, 0.5)
#     xp = getV_xp_dji(1, i)
#     # print(yuan)
#     # print(rel)
#     # print(xp)
#     # xxx = fuzz.fuzzy_div(yuan, getV_xp_dji_fun(1), rel, R_Q_2dnparray)
#     xxx = fuzz.relation_min(getV_xp_dji_fun(1), R_Q_2dnparray)
#     # xxx = fuzz.fu(yuan, rel)
#     print(xxx)
#
#     val.append(np.fmax(0, np.fmin(xxx[0], rel)))
#     # val.append(max(0, min(xxx[0][0], rel)))
# plt.plot(val)
# plt.show()
# exit()
#
#
# V_list = []
# vv = []
# for v in x:
#     V_list.append([v, getV_xp_dji(1, v)])
#     vv.append(getV_xp_dji(1, v))
# V_2dnparray = np.array(V_list)
# print(V_2dnparray)
# print(".")
# R_Q_list = []
# rqq = []
# for v in x:
#     R_Q_list.append([v, R_QXP(v)])
#     rqq.append(R_QXP(v))
# R_Q_2dnparray = np.array(R_Q_list)
#
# print(R_Q_2dnparray)
# print(".")
#
# plt.plot(vv)
# plt.plot(rqq)
#
#
# mamin = fuzz.relation_product(A1, np.array(rqq))
# print(mamin)
# # mamin = fuzz.maxmin_composition(V_2dnparray, R_Q_2dnparray.T)
# plt.plot(mamin)
#
# for i in x:
#     try:
#         print(i, fuzz.defuzz(x, mamin[x == i], 'centroid'))
#     except:
#         print("no")
#         pass


def closest(lst, K):
    min_idx = min(range(len(lst)), key=lambda i: abs(lst[i] - K))
    return lst[min_idx], min_idx

def generateRelationshipData():
    import random

    generic_range = np.arange(0, 1.005, 0.01)

    # v_xp1 = fuzz.trimf(cross_univ, [0, 0.5, 1])
    data_relat_cp = []
    data_relat_yuan = []
    for i in range(50):
        print(i)
        t1_c = random.uniform(0.0, 1.0)
        t1_d = random.uniform(t1_c, 1.0)
        t1_b = random.uniform(0.0, t1_c)
        t1_a = random.uniform(0.0, t1_b)
        t1 = fuzz.trapmf(generic_range, [t1_a, t1_b, t1_c, t1_d])
        t2_b = random.uniform(0.0, 1.0)
        t2_c = random.uniform(t2_b, 1.0)
        t2_d = random.uniform(t2_c, 1.0)
        t2_a = random.uniform(0.0, t2_b)
        t2 = fuzz.trapmf(generic_range, [t2_a, t2_b, t2_c, t2_d])

        # print("t1: ", t1)
        # print("t2: ", t2)
        # plt.plot(generic_range, t1)
        # plt.plot(generic_range, t2)
        # plt.show()
        try:
            sol_cp = fsolve(f_skfuzzy, np.array([0.5, 0.5]), args=(t1, t2))
            data_relat_cp.append(sol_cp[1])

            yuan = YuanFuzzyOrderingIndex(t1, t2)
            data_relat_yuan.append(yuan)
        except:
            pass
    print(data_relat_cp)
    print(data_relat_yuan)

    rel_matr = createNumpyRelMatrixFromData(data_relat_cp, data_relat_yuan)
    print(rel_matr)
    plt.plot(rel_matr)
    plt.show()


# crossing_point_value_data = [2.246663578009097e-36, 1.0, 0.13159588829662996, 1.0, 0.5, 0.37700799475187513, 0.5, 5.2706227954994316e-36, 1.0,
#      1.0, 0.5, 0.0, 1.0, 0.5587288714557492, 0.6761512072694331, 1.0, 0.18000063822066995, 1.0, 1.0, 0.993152854724899,
#      0.8203371238149199, 0.0, 2.049079508025179e-39, 0.247151296114683, 1.0, 0.48086767269324304,
#       4.515367675096112e-36, 0.8609922253925926, 0.5, 0.8567267386517835, 1.0, 1.0,
#      0.47990851537739715, 0.5, 0.34889806059897205, 0.653924330951589, 1.1044136767960023e-36, 0.5, 1.0, 0.0, 1.0, 0.5,
#      1.0, 1.0, 0.5, 0.9930663156381095, 0.7434054856739433, 0.6978142559279038]
# print(len(crossing_point_value_data))
# yuan_data = [0.3134154457523532, 0.6205581357168545, 0.9937706407054583, 0.4924466687933362, 0.7196216038041566,
#  0.9283859467805972, 0.2613033498073289, 0.563549218830921, 0.6238369276798604, 0.1357486784538107, 1.0,
#  0.37407358729296786, 0.17780271223448202, 0.7864126583737491, 0.6144561095348328, 0.990956260379931,
#  0.7049321323035856, 0.3594585739568385, 0.7104719571251265, 0.7200866599420492, 0.7513392960459615, 1.0,
#  0.9805786581534508, 0.5289207312302304, 0.868276648264347, 1.0, 0.20282152756884236, 0.26859947443750914,
#  0.8029494424941472, 0.7624798276933284, 0.5154552914872119, 0.2015290276839075, 0.9246749587777074,
#  0.8882724242554829, 0.9521498300399678, 0.8139933371463337, 0.233904045907351, 0.6790915937691151,
#  0.7411494410166545, 1.0, 0.5535512378787001, 0.6860178858585932, 0.46837718896260777, 0.053653702624054334,
#  0.898323121026916, 0.49383731931894614, 0.8185179945872668, 0.8226234821622226]
# print(len(yuan_data))
# cr = fuzz.cartprod(np.array(crossing_point_value_data), np.array(yuan_data))
# print(cr)
# plt.plot(cr)
# plt.show()
#
# exit()
cross_univ = np.arange(0.0, 1.04, 0.05)
mem_univ = np.arange(0.0, 1.04, 0.05)
yuan_univ = np.arange(0.0, 1.04, 0.05)


def mu_q_dji(yuan, dji):
    m_x = []
    for cp in cross_univ:
        v_xp = getV_xp_dji(dji, cp)
        r_xy = R_QXP2(yuan, cp)
        min_val = min(v_xp, r_xy)
        print(min_val)
        m_x.append(min_val)
        print("x: ", yuan, "y: ", cp, "v_xp:", v_xp, "r_xy:", r_xy, "min: ", min_val)
    max_val = max(m_x)
    return max_val

mf_q = []
for yu in yuan_univ:
    mf_q.append(mu_q_dji(yu, 1))
plt.plot(yuan_univ, mf_q)
plt.show()
exit()

print("---")
dji = 1
final_m = []
for x in yuan_univ:
    m_x = []
    for y in cross_univ:
        v_xp = getV_xp_dji(dji, y)
        r_xy = R_QXP2(x, y)
        min_val = min(v_xp, r_xy)
        m_x.append(min_val)
        print("x: ", x, "y: ", y, "v_xp:", v_xp, "r_xy:", r_xy, "min: ", min_val)
    m_xnp = np.array(m_x)
    max_val = np.max(m_xnp)
    print("max: ", max_val)
    final_m.append(max_val)
print(np.array(final_m))
plt.plot(yuan_univ, np.array(final_m))
plt.show()
exit()
# pll = []
# for y in yuan_univ:
#     try:
#         # expr = getV_xp_dji(1,y)/(R_QXP(y)*1.28)
#         # expr = 1-(getV_xp_dji(2,y)*4.8/(R_QXP(y)*1.28))
#         # expr = 1-(getV_xp_dji(2,y)*10.24/(R_QXP(y)*1.28))
#         # print(y, expr)
#         expr = min(getV_xp_dji(1, 0), R_QXP(y)*0)
#         pll.append(max(0, min(expr,1))) #sup
#     except:
#         pll.append(0)

vxx = [getV_xp_dji(1, c) for c in cross_univ]
rxx = [R_QXP(y) for y in yuan_univ]
mins=[]
for r in range(len(rxx)):
    rxxmult = vxx[r]/rxx[r]
    print(rxxmult)
    print(vxx[r])
    mins.append(min(vxx[r], rxxmult))
plt.plot(yuan_univ, mins)
plt.show()

exit()
# Membership functions
plt.plot(cross_univ, v_xp1)
plt.plot(cross_univ, [R_QXP(y) for y in cross_univ])
R_Q_list = [[y, R_QXP(y)] for y in cross_univ]
R_Q_2dnparray = np.array(R_Q_list)
print("empirical relation")
print(R_Q_2dnparray)
print("...")
# plt.plot([R_QXP(y) for y in cross_univ])
# Fuzzy relation
# R2 = fuzz.relation_product(v_xp1, R_Q_2dnparray)
R2 = fuzz.dsw_div(cross_univ, v_xp1, cross_univ, [R_QXP(getV_xp_dji(1,y)) for y in cross_univ],20)
print(R2)
# plt.plot(R2)

l = []
xs = []
for x in cross_univ:
    try:
        l.append(fuzz.defuzz(yuan_univ, R2[cross_univ == x], 'centroid'))
        xs.append(x)
    except:
        pass
plt.plot(xs, l)
# Combine fuzzy relations into aggregate relation
# R_combined = np.fmax(R1, np.fmax(R2, R3))

# R_star = fuzz.maxmin_composition(t_hot, t_hot)

plt.show()
