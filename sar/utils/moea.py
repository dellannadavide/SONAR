import copy
import math
import sys
import threading
import time
import warnings
from functools import partial
from multiprocessing import Pool
from psutil import cpu_count

from simpful import *

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.algorithms.moo.rnsga2 import RNSGA2
from pymoo.algorithms.moo.unsga3 import UNSGA3
from pymoo.algorithms.soo.nonconvex.de import DE
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.core.problem import Problem
from pymoo.operators.sampling.lhs import LatinHypercubeSampling
from pymoo.optimize import minimize
from pymoo.factory import get_termination
from pymoo.factory import get_sampling, get_crossover, get_mutation
from pymoo.operators.mixed_variable_operator import MixedVariableSampling, MixedVariableMutation, \
    MixedVariableCrossover


from scipy.optimize import fsolve
import numpy as np
import asyncio

import utils.constants as Constants


import skfuzzy as fuzz
import scipy.integrate as integrate

from sar.utils.skfsutils import convertFSTOSkFuzzy, getDissimilaritySKFuzzyMF

import logging
logger = logging.getLogger("nosar.sar.utils.moea")

def f(xy, *fuzzy_sets):
    """ To determine the intersection between two functions """
    x, y = xy
    fs1, fs2 = fuzzy_sets
    z = np.array([y - fs1.get_value(x), y - fs2.get_value(x)])
    return z

def scaleFrom01ToAB(x, a, b, lambd, k_SF):
    if x <= lambd:
        return (a + ((b - a) * ((lambd ** (1 - k_SF)) * (x ** k_SF))))
    else:
        return (a + ((b - a) * (1 - (((1 - lambd) ** (1 - k_SF)) * ((1 - x ** (k_SF)))))))

def scaleUniverse(sf_ling_var, a, b, lambd, k_SF): #sf_ling_var is a simpful linguistic var (not a SARFuzzyLingVar)
    sf_ling_var._universe_of_discourse = [scaleFrom01ToAB(sf_ling_var.universe_of_discourse[0], a, b, lambd, k_SF),
                                                         scaleFrom01ToAB(sf_ling_var.universe_of_discourse[1], a, b, lambd, k_SF)]

def R_QXP(x):
    """
    This function has been determined by fitting the following data, which are an approximation of the empirical relation reported in Botta 2008, Automatic Context Adaptation of Fuzzy Systems, Figure 32
    xdata = [0.0, 0.2,      0.318, 0.428, 0.52, 0.585, 0.652, 0.708, 0.76, 0.81, 0.858, 0.895, 0.94, 0.98, 1.0]
    ydata = [1.0, 0.992,    0.98, 0.96, 0.94, 0.92,     0.9, 0.88, 0.86,    0.84, 0.82, 0.80, 0.64, 0.48, 0.40]
    xdata = np.asarray(xdata)
    ydata = np.asarray(ydata)
    z = np.polyfit(xdata, ydata, 6)
    print(z)
    f = np.poly1d(z)
    y_new = f(xdata)
    plt.plot(xdata, ydata, 'o', label='data')
    plt.plot(xdata, y_new, '-', label='fit')
    plt.show()
    """
    z = np.asarray([-31.02033482, 79.91487888, -77.74059048, 35.28901165, -7.63705323, 0.57831101, 1.00004764])
    f = np.poly1d(z)
    return f(x)


def getALphaCutBoundaries(universe_boundaries, mf, alpha):
    x = np.arange(universe_boundaries[0], universe_boundaries[1]+0.00001, 0.05)
    # start = time.time()
    boundaries = fuzz.lambda_cut_boundaries(x, mf, alpha)
    # print("Time for computing alpha cut: ", time.time() - start)
    if len(boundaries)==1:
        boundaries = np.array([boundaries[0], boundaries[0]])
    if len(boundaries)==0:
        boundaries = np.array([0.0, 0.0])
    return boundaries

def fU1minusL2(partition_universe_boundaries, alpha, A1, A2):
    u_A1alpha = getALphaCutBoundaries(partition_universe_boundaries, A1, alpha)[1]
    l_A2alpha = getALphaCutBoundaries(partition_universe_boundaries, A2, alpha)[0]
    # u_A1alpha = boundaries_A1[1]
    # l_A2alpha = boundaries_A2[0]
    if u_A1alpha>l_A2alpha:
        return u_A1alpha-l_A2alpha
    return 0

def fL1minusU2(partition_universe_boundaries, alpha, A1, A2):
    l_A1alpha = getALphaCutBoundaries(partition_universe_boundaries, A1, alpha)[0]
    u_A2alpha = getALphaCutBoundaries(partition_universe_boundaries, A2, alpha)[1]
    # l_A1alpha = boundaries_A1[0]
    # u_A2alpha = boundaries_A2[1]
    if l_A1alpha>u_A2alpha:
        return l_A1alpha-u_A2alpha
    return 0

def DeltaA1A2(partition_universe_boundaries, A1, A2) -> float:
    # integral = 0
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        integral_U1minusL2 = integrate.quad(lambda alpha: fU1minusL2(partition_universe_boundaries, alpha, A1, A2), 0.0, 1.0, limit=10)
        integral_L1minusU2 = integrate.quad(lambda alpha: fL1minusU2(partition_universe_boundaries, alpha, A1, A2), 0.0, 1.0, limit=10)
        # print(integral_U1minusL2)
        # print(integral_L1minusU2)
        integral = integral_U1minusL2[0]+integral_L1minusU2[0]
        # print(integral)
    return integral

def YuanFuzzyOrderingIndex(partition_universe_boundaries, A1, A2):
    """
    :param A1: membership function 1
    :param A2: membership function 2
    :return: a real value, obtained calculating the Yuan's fuzzy ordering index
    """
    # start = time.time()
    yuan_index = 0
    num = DeltaA1A2(partition_universe_boundaries, A2, A1)
    denom = (DeltaA1A2(partition_universe_boundaries, A1, A2)+DeltaA1A2(partition_universe_boundaries, A2, A1))
    if denom>0:
        yuan_index = num/denom
    # print("Time for computing yuan: ", time.time() - start)
    return yuan_index

def getV_xp_dji(dji, y):
    x = np.arange(0, 1.05, 0.05)
    mf = fuzz.trapmf(x, [0.0, 0.5, 0.5, 1])
    if dji>1:
        mf = fuzz.trapmf(x, [0.0, 0.0, 0.0, 2/dji])
    return fuzz.interp_membership(x, mf, y)

# def mu_q_dji(x, y, dji):
#     v_xyp_dji = getV_xp_dji(dji, y)
#     rqxpxy = R_QXP(x)
#     v = min(v_xyp_dji, rqxpxy)
#     return max(0.0, min(v, 1.0))

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
    mu = 0.0
    for y in np.arange(0, 1.00000000001, 0.001):
        # print("\ty=", y)
        v_xyp_dji = getV_xp_dji(dji, y)
        rqxpxy = getR_QXP(x,y)
        # print("\t\t", v_xyp_dji, rqxpxy)
        v = min(v_xyp_dji, rqxpxy)
        mu = max(mu, v)
    return mu

# def mu_q_dji_APPROX(yuan, dji):
#     gen_range = np.arange(0, 1.05, 0.05)
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



def PHI_Q(partition_universe_boundaries, partition):
    """
    This functions computes the interpretability index defined by Botta et al. 2009
    in "Context adaptation of fuzzy systems through a multi-objective evolutionary approach"
    It uses an approximation for the mu function reported in their paper *this is by definition, since it was based on empirical data*
    :param partition:
    :return: a real value indicating the interpretability of the partition
    """
    N = len(partition)
    num = 0
    denom = 0
    for i in range(N-1):
        for j in range(i+1, N):
            dji = abs(j-i)
            # y = crossing_point_value(partition[i], partition[j])
            # mf_i = convertFSTOSkFuzzy(partition[i])
            # mf_j = convertFSTOSkFuzzy(partition[j])
            num = num + ((1/dji)*(mu_q_dji(YuanFuzzyOrderingIndex(partition_universe_boundaries, partition[i], partition[j]), dji)))
            # num = num + ((1/dji)*(mu_q_dji(YuanFuzzyOrderingIndex(mf_i, mf_j), dji)))
            denom = denom + (1/dji)
    return num/denom

def crossing_point_value(mf1, mf2):
    last_x = 0.0
    last_y = 0.0
    cp_vn = -1
    try:
        sol = fsolve(f, np.array([last_x, last_y]), args=(mf1, mf2))
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
        pass
    return cp_vn

def computePHIPenalty(FS, ling_var_to_adapt):
    # start = time.time()
    cumulative_penalty = 0
    for v in ling_var_to_adapt:  # only these because we are not modifying anyways the others, so they would't change
        partition = FS.get_fuzzy_sets(v)  # list of fuzzy sets
        partition_universe_boundaries = FS._lvs[v].get_universe_of_discourse()
        sk_partition = [convertFSTOSkFuzzy(partition_universe_boundaries, p) for p in partition]
        penalty = 1-PHI_Q(partition_universe_boundaries, sk_partition)
        cumulative_penalty = cumulative_penalty + penalty
    average_penalty = cumulative_penalty / len(ling_var_to_adapt)
    # print("Time for computing phi penalty: ", time.time() - start)
    return average_penalty

def computeAverageCoveragePenalty(FS, ling_var_to_adapt, beta=0.5, CPL=0.25, CPU=0.75):
    # start = time.time()
    cumulated_penalty = 0
    for v in ling_var_to_adapt: #only these because we are not modifying anyways the others, so they would't change
        partition = FS.get_fuzzy_sets(v)  # list of fuzzy sets
        last_x = 0.0
        last_y = 0.0
        for n in range(len(partition) - 1):
            cp_vn = crossing_point_value(partition[n], partition[n + 1])
            p_vn = 0  # compute the penalty based on the crossing point value (if beyond acceptable limits, then 0 (default), otherwise 1
            if cp_vn < CPL or cp_vn > CPU:
                p_vn = 1
            cumulated_penalty = cumulated_penalty + p_vn
    average_penalty = beta * (cumulated_penalty / len(ling_var_to_adapt))
    # coverage_penalty = 1 + (beta * cumulated_penalty)
    # return coverage_penalty
    # print("Time for computing average coverage penalty: ", time.time() - start)
    return average_penalty


def computeMSE(FS, dataset):
    sum_squared_errors = 0
    for datapoint in dataset:
        for v in datapoint["inputs"].keys():
            FS.set_variable(v, datapoint["inputs"][v])
        try:
            fs_output = FS.inference()
            for ov in fs_output.keys():
                sum_squared_errors = sum_squared_errors + ((float(fs_output[ov]) - datapoint["outputs"][ov]) ** 2)
        except:
            sum_squared_errors = sum_squared_errors + 1
    mse = (1 / len(dataset)) * sum_squared_errors
    return mse

def computeAverageDissimilarityWithCurrentController(FS, ling_var_to_adapt, base_FS):
    cumulative_dissimilarity = 0
    nr_el = 0
    # print("Computing Average Dissimilarity")
    for v in ling_var_to_adapt:  # only these because we are not modifying anyways the others, so they would't change
        # print("Variable: ", v)
        new_partition = FS.get_fuzzy_sets(v)  # list of fuzzy sets
        base_partition = base_FS.get_fuzzy_sets(v)
        base_partition_universe_boundaries = base_FS._lvs[v].get_universe_of_discourse()
        base_partition_universe = np.arange(base_partition_universe_boundaries[0], base_partition_universe_boundaries[1]+0.000001, 0.05)
        for fs_idx in range(len(new_partition)):
            new_sk_fs = convertFSTOSkFuzzy(base_partition_universe_boundaries, new_partition[fs_idx])
            base_sk_fs = convertFSTOSkFuzzy(base_partition_universe_boundaries, base_partition[fs_idx])
            # print(v, new_partition[fs_idx]._term, "Comparing the new fs")
            # print(v, new_partition[fs_idx]._term, new_sk_fs)
            # print(v, "with the base fs")
            # print(v, base_partition[fs_idx]._term, base_sk_fs)
            # print(v, "over universe")
            # print(v, new_partition[fs_idx]._term, base_partition_universe_boundaries)
            dissimilarity = getDissimilaritySKFuzzyMF(base_partition_universe, base_sk_fs, base_partition_universe, new_sk_fs)
            # print(v, new_partition[fs_idx]._term, "Dissimilarity: ", dissimilarity)
            cumulative_dissimilarity = cumulative_dissimilarity + dissimilarity
            nr_el = nr_el + 1
    average_dissimilarity = cumulative_dissimilarity / nr_el
    return average_dissimilarity


def evalSetORIGINAL(asyncTask, controllers, ling_var_to_adapt, dataset, nr_objectives):
    """ This function creates a number of threads, each of them evaluating one possible chromosome"""
    loop = asyncio.new_event_loop()  # construct a new event loop

    def run_forever_safe(loop):
        loop.run_forever()
        # for Python 3.7 and newer
        loop_tasks_all = asyncio.all_tasks(loop=loop)
        # for Python 3.6
        # loop_tasks_all = asyncio.Task.all_tasks(loop=loop)
        for task in loop_tasks_all:
            task.cancel()
        for task in loop_tasks_all:
            if not (task.done() or task.cancelled()):
                try:
                    # wait for task cancellations
                    loop.run_until_complete(task)
                except asyncio.CancelledError:
                    pass
        loop.close()

    def stop_loop(loop):
        ''' stops an event loop '''
        loop.stop()

    # print (".:) LOOP STOPPED:", loop.is_running())

    def await_sync(task):
        ''' synchronously waits for a task '''
        while not task.done():
            pass
        # print(".: AWAITED TASK DONE")
        return task.result()

    # -- closures for running and stopping the event-loop
    run_loop_forever = lambda: run_forever_safe(loop)
    close_loop_safe = lambda: loop.call_soon_threadsafe(stop_loop, loop)
    # -- make dedicated thread for running the event loop
    thread = threading.Thread(target=run_loop_forever)
    # -- add some tasks along with my particular task
    evaluationTasks = [asyncio.run_coroutine_threadsafe(asyncTask(controller, ling_var_to_adapt, dataset, nr_objectives), loop=loop)
                       for controller in controllers]
    # -- begin the thread to run the event-loop
    thread.start()
    # -- _synchronously_ wait for the result of my task
    results = [await_sync(task) for task in evaluationTasks]
    # close the loop gracefully when everything is finished
    close_loop_safe()
    thread.join()
    return results

def evalSet(fit_fun, population, ling_var_to_adapt, dataset, nr_objectives, interpretability_index, base_controller):
    start = time.time()
    evalFitness = partial(fit_fun, ling_var_to_adapt=ling_var_to_adapt, dataset=dataset, nr_objectives=nr_objectives, interpretability_index=interpretability_index, base_controller=base_controller)
    pool = Pool(cpu_count(logical=False))
    pop_fitness = pool.map(evalFitness, population)
    pool.close()
    pool.join()
    # print("Time required to evaluate population ", time.time()-start)
    return pop_fitness

def extractParamForVarFromChromosome(var_idx, optim_param, chromosome):
    C_SF = C_CP = C_CW = C_SW = C_GP = 0
    a = b = lambd = k_SF = k_CP = k_CW = k_SW = theta = k_GP = None

    prefix_len = (var_idx * optim_param["nr_param_per_var"])

    last_idx = 0
    if optim_param["scale"]:
        C_SF = chromosome[last_idx + prefix_len]
        last_idx += 1
    if optim_param["core-pos"]:
        C_CP = chromosome[last_idx + prefix_len]
        last_idx += 1
    if optim_param["core-width"]:
        C_CW = chromosome[last_idx + prefix_len]
        last_idx += 1
    if optim_param["support-width"]:
        C_SW = chromosome[last_idx + prefix_len]
        last_idx += 1
    if optim_param["gp"]:
        C_GP = chromosome[last_idx + prefix_len]
        last_idx += 1

    if optim_param["scale"]:
        a = chromosome[last_idx + prefix_len]
        b = chromosome[last_idx + 1 + prefix_len]
        lambd = chromosome[last_idx + 2 + prefix_len]
        k_SF = chromosome[last_idx + 3 + prefix_len]
        last_idx += 4
    if optim_param["core-pos"]:
        k_CP = chromosome[last_idx + prefix_len]
        last_idx += 1
    if optim_param["core-width"]:
        k_CW = chromosome[last_idx + prefix_len]
        last_idx += 1
    if optim_param["support-width"]:
        k_SW = chromosome[last_idx + prefix_len]
        last_idx += 1
    if optim_param["gp"]:
        theta = chromosome[last_idx + prefix_len]
        k_GP = chromosome[last_idx + 1 + prefix_len]
        last_idx += 2

    return C_SF, C_CP, C_CW, C_SW, C_GP, a, b, lambd, k_SF, k_CP, k_CW, k_SW, theta, k_GP




def getControllerFromChromosome(base_controller, ling_var_to_adapt, optim_param, chromosome):
    """
	Chromosome:
	for every linguistic variable, it contains
	C_SF, C_CP, C_CW, C_SW, C_GP,
	a, b, lambda, k_SF, k_CP, k_CW, k_SW, theta, k_GP
	i.e., 5+9 = 14 elements
	these elements characterize the modifications to make to all the partition characterizing that variable
	i.e., to all the fuzzy sets related to it
	"""

    new_controller = copy.deepcopy(base_controller)

    i = 0
    for v in ling_var_to_adapt:
        C_SF, C_CP, C_CW, C_SW, C_GP, a, b, lambd, k_SF, k_CP, k_CW, k_SW, theta, k_GP = extractParamForVarFromChromosome(i, optim_param, chromosome)
        if C_SF == 1:  # then I want to apply non-linear scaling
            scaleUniverse(new_controller._lvs[v], a,b,lambd,k_SF)
        lv_universe = new_controller._lvs[v]._universe_of_discourse
        partition = new_controller.get_fuzzy_sets(v)  # list of fuzzy sets
        # then for each fuzzy set I need to apply the modifications.
        for fs in partition:
            if C_SF == 1:  # then I want to apply non-linear scaling
                fs.scale(a, b, lambd, k_SF)
            if C_CP == 1:  # CORE-POSITION MODIFIER enabled
                fs.modifyCorePosition(k_CP)
            if C_CW == 1:  # core width modifier
                fs.modifyCoreWidth(k_CW)
            if C_SW == 1:  # support width modifier
                fs.modifySupportWidth(k_SW, lv_universe)
            if C_GP == 1:  # GENERALIZED POSITIVELY MODIFIER
                fs.setGeneralizedPositivelyModifierParams(theta, k_GP)
        i = i + 1
    return new_controller


def fitnessFunction(controller, ling_var_to_adapt, dataset, nr_objectives, interpretability_index, base_controller):
    result = {}
    result['mse'] = 1.0
    if nr_objectives==2:
        # result['mse'] = computeMSE(controller, dataset)
        result['mse'] = computeAverageDissimilarityWithCurrentController(controller, ling_var_to_adapt, base_controller)

    if interpretability_index==Constants.PHI_INTERPRETABILITY_INDEX:
        result['avg_phi'] = computePHIPenalty(controller, ling_var_to_adapt)
    else:
        result['avg_phi'] = computeAverageCoveragePenalty(controller, ling_var_to_adapt)
    return result

def fitnessFunction_Multi_All(base_controller, ling_var_to_adapt, dataset, optim_param, chromosomes):
    """ this function should call a multithreading function that evaluates all chromosomes"""
    controllers = []
    for chromosome in chromosomes:
        controllers.append(getControllerFromChromosome(base_controller,
                                                       ling_var_to_adapt,
                                                       optim_param,
                                                       chromosome))  # here you should be able to create all necessary info to create a bunch of descriptions that will lead to creating a bunch of fuzzy controllers that should be evaluated w.r.t. their output I guess
    results = evalSet(fitnessFunction, controllers, ling_var_to_adapt, dataset, optim_param["n_obj_f"], optim_param["interpretability_index"], base_controller)
    return results

class MyMOEAProblem(Problem):
    def __init__(self, n_var, lb_list, ub_list, base_controller, ling_var_to_adapt, dataset, optim_param):
        self.optim_param = optim_param
        if self.optim_param is None:
            self.optim_param = {
                "algo": Constants.NSGA3,
                "scale": True,
                "core-pos": True,
                "core-width": True,
                "support-width": True,
                "gp": True,
                "n_obj_f": 2
            }
        self.n_obj = self.optim_param["n_obj_f"]
        super().__init__(n_var=n_var,  # number of design variables
                         n_obj=self.n_obj,  # number of objectives
                         n_constr=0,  # number of constraints
                         xl=np.array(lb_list),  # lower bounds of the design variables
                         xu=np.array(ub_list),  # upper bounds of the design variables
                         elementwise_evaluation=False)
        self.base_controller = base_controller
        self.ling_var_to_adapt = ling_var_to_adapt
        self.dataset = dataset

    def set_dataset(self, dataset):
        self.dataset = dataset

    def _evaluate(self, chromosomes, out, *args, **kwargs):
        results = fitnessFunction_Multi_All(self.base_controller,
                                            self.ling_var_to_adapt,
                                            self.dataset,
                                            self.optim_param,
                                            chromosomes)  # computes the fitness function for all chromosomes.

        if self.optim_param["n_obj_f"]==2:
            f1 = np.array([result['mse'] for result in results])
            f2 = np.array([result['avg_phi'] for result in results])
            out["F"] = np.column_stack([f1, f2]).astype(np.float64)
        else:
            f2 = np.array([result['avg_phi'] for result in results])
            out["F"] = np.column_stack([f2]).astype(np.float64)


def getContextualizedFS(FS, ling_var_to_adapt, dataset, optim_param):
    # first determine the boundaries of the variables in the dataset
    ds_min_vals = {}
    ds_max_vals = {}
    for dp in dataset:
        for v in dp["inputs"].keys():
            if v in ds_min_vals.keys():
                if dp["inputs"][v] < ds_min_vals[v]:
                    ds_min_vals[v] = dp["inputs"][v]
                if dp["inputs"][v] > ds_max_vals[v]:
                    ds_max_vals[v] = dp["inputs"][v]
            else:
                ds_min_vals[v] = dp["inputs"][v]
                ds_max_vals[v] = dp["inputs"][v]
        for v in dp["outputs"].keys():
            if v in ds_min_vals.keys():
                if dp["outputs"][v] < ds_min_vals[v]:
                    ds_min_vals[v] = dp["outputs"][v]
                if dp["outputs"][v] > ds_max_vals[v]:
                    ds_max_vals[v] = dp["outputs"][v]
            else:
                ds_min_vals[v] = dp["outputs"][v]
                ds_max_vals[v] = dp["outputs"][v]
    # then determine the number of variables
    n_var = len(ling_var_to_adapt)
    # print("number of linguistic variables: ", n_var)
    # print(ling_var_to_adapt)

    # define the chromosome
    """ Chromosome: 
    for every variable it has
    C_SF, C_CP, C_CW, C_SW, C_GP,
    a, b, lambda, k_SF, k_CP, k_CW, k_SW, theta, k_GP
    """
    mask = []
    lb_list = []
    ub_list = []
    alpha = 0.15
    for v in ling_var_to_adapt:
        mask_conditions = []
        mask_params = []
        lb_cond = []
        lb_param = []
        ub_cond = []
        ub_param = []
        if optim_param["scale"]:
            mask_conditions.append("int")
            lb_cond.append(0)
            ub_cond.append(1)
            mask_params.extend(["real", "real", "real", "real"])
            D_v = ds_max_vals[v] - ds_min_vals[v]
            lb_a = ds_min_vals[v] - (alpha * D_v)
            ub_a = ds_min_vals[v] + (alpha * D_v)
            lb_b = ds_max_vals[v] - (alpha * D_v)
            ub_b = ds_max_vals[v] + (alpha * D_v)
            lb_param.extend([lb_a, lb_b, 0, 0.4])
            ub_param.extend([ub_a, ub_b, 1, 2])
        if optim_param["core-pos"]:
            mask_conditions.append("int")
            lb_cond.append(0)
            ub_cond.append(1)
            mask_params.append("real")
            lb_param.append(-0.9)
            ub_param.append(0.9)
        if optim_param["core-width"]:
            mask_conditions.append("int")
            lb_cond.append(0)
            ub_cond.append(1)
            mask_params.append("real")
            lb_param.append(-1)
            ub_param.append(0.25)
        if optim_param["support-width"]:
            mask_conditions.append("int")
            lb_cond.append(0)
            ub_cond.append(1)
            mask_params.append("real")
            lb_param.append(0.667)
            ub_param.append(2)
        if optim_param["gp"]:
            mask_conditions.append("int")
            lb_cond.append(0)
            ub_cond.append(1)
            mask_params.extend(["real", "real"])
            lb_param.extend([0, 0.75])
            ub_param.extend([1, 4])

        mask.extend(mask_conditions+mask_params)
        lb_list.extend(lb_cond+lb_param)
        ub_list.extend(ub_cond+ub_param)
    # alpha = 0.15
    # for v in ling_var_to_adapt:
    #     D_v = ds_max_vals[v] - ds_min_vals[v]
    #     lb_a = ds_min_vals[v] - (alpha * D_v)
    #     ub_a = ds_min_vals[v] + (alpha * D_v)
    #     lb_b = ds_max_vals[v] - (alpha * D_v)
    #     ub_b = ds_max_vals[v] + (alpha * D_v)
    #     lb_list.extend([0, 0, 0, 0, 0,
    #                     lb_a, lb_b,
    #                     0, 0.4, -0.9, -1, 0.667, 0, 0.75])
    #     ub_list.extend([1, 1, 1, 1, 1,
    #                     ub_a, ub_b,
    #                     1, 2, 0.9, 0.25, 2, 1, 4])

    # print("length of chromosomes:", len(mask))
    # print("mask chromosome: ", str(mask))

    # define the optimization problem
    sampling = MixedVariableSampling(mask, {
        "real": get_sampling("real_random"),
        "int": get_sampling("int_random")
    })

    crossover = MixedVariableCrossover(mask, {
        "real": get_crossover("real_sbx", prob=1.0, eta=3.0),
        "int": get_crossover("int_sbx", prob=1.0, eta=3.0)
    })

    mutation = MixedVariableMutation(mask, {
        "real": get_mutation("real_pm", eta=3.0),
        "int": get_mutation("int_pm", eta=3.0)
    })

    problem = MyMOEAProblem(len(mask), lb_list, ub_list, FS, ling_var_to_adapt, dataset, optim_param=optim_param)
    ref_points = np.array([[0.0]*optim_param["n_obj_f"]])


    termination = get_termination("n_gen", optim_param["n_gen"])

    algo = None
    if optim_param["algo"] == Constants.NSGA2:
        algo = NSGA2(pop_size=optim_param["pop_size"],
                     sampling=sampling,
                     crossover=crossover,
                     mutation=mutation)
    if optim_param["algo"] == Constants.RNSGA2:
        algo = RNSGA2(
            ref_points=ref_points,
            pop_size=optim_param["pop_size"],
            sampling=sampling,
            crossover=crossover,
            mutation=mutation
        )
    if optim_param["algo"] == Constants.NSGA3:
        algo = NSGA3(pop_size=optim_param["pop_size"],
                     ref_dirs=ref_points,
                     sampling=sampling,
                     crossover=crossover,
                     mutation=mutation
                     )
    if optim_param["algo"] == Constants.UNSGA3:
        algo = UNSGA3(ref_points, pop_size=optim_param["pop_size"],
                      sampling=sampling,
                      crossover=crossover,
                      mutation=mutation
                      )
    if optim_param["n_obj_f"]==1:
        if optim_param["algo"] == Constants.GA:
            algo = GA(
                pop_size=optim_param["pop_size"],
                sampling=sampling,
                crossover=crossover,
                mutation=mutation,
                eliminate_duplicates=True)
        if optim_param["algo"] == Constants.DE:
            algo = DE(
                pop_size=optim_param["pop_size"],
                sampling=LatinHypercubeSampling(iterations=150, criterion="maxmin"),
                variant="DE/rand/1/bin",
                CR=0.9,
                F=0.8,
                dither="vector",
                jitter=False,
                mutation=mutation
            )

    if not algo is None:
        # print(":.................................")
        # print(algo)
        # print(optim_param)
        res = minimize(problem,
                       algo,
                       termination,
                       seed=1,
                       save_history=False,
                       verbose=True)
        logger.info("Best solution found: \nBest_Chromosome = %s\nOptimal E = %s" % (res.X, res.F))
        if optim_param["n_obj_f"]==2:
            return getControllerFromChromosome(FS, ling_var_to_adapt, optim_param, (res.X)[0].tolist())
        return getControllerFromChromosome(FS, ling_var_to_adapt, optim_param, res.X.tolist())
    else:
        logger.error("No algorithm specified, returning the original Fuzzy System")
    return FS
