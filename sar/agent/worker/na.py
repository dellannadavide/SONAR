import numpy as np
import math
import random
from math import *
import scipy.integrate as integrate
import matplotlib.pyplot as plt
import pandas as pd
import skfuzzy as fuzz

import copy


import asyncio
import threading


import time

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
from pymoo.visualization.scatter import Scatter

fitnessFunctionDescription = {
    'fuzzyDescription': {
        'inputs': {
            'distance': {
                'S': list(np.arange(0, 2, 0.02)),
                'M': {'VC': [0, 0, 0.5], 'C': [0, 0.5, 1], 'M': [0.5, 1, 1.5], 'F': [1, 1.5, 2], 'VF': [1.5, 2, 2]}
            },
            'angle': {
                'S': list(np.arange(-3.14, 3.14, 0.0628)),
                'M': {'BN': [-3.14, -3.14, -1.57], 'N': [-3.14, -1.57, 0], 'Z': [-1.57, 0, 1.57], 'P': [0, 1.57, 3.14],
                      'BP': [1.57, 3.14, 3.14]}
            }
        },
        'outputs': {
            'omegaR': {
                'S': list(np.arange(0, 30, 0.3)),
                'rules': {
                    'VC': {'BN': 'VSR', 'N': 'SR', 'Z': 'VSR', 'P': 'BR', 'BP': 'VBR'},
                    'C': {'BN': 'VSR', 'N': 'SR', 'Z': 'SR', 'P': 'BR', 'BP': 'VBR'},
                    'M': {'BN': 'VSR', 'N': 'SR', 'Z': 'MBR', 'P': 'BR', 'BP': 'VBR'},
                    'F': {'BN': 'VSR', 'N': 'SR', 'Z': 'BR', 'P': 'BR', 'BP': 'VBR'},
                    'VF': {'BN': 'VSR', 'N': 'SR', 'Z': 'VBR', 'P': 'BR', 'BP': 'VBR'}
                },
                'mode': 'centroid',
                'M': {'VSR': [0, 0, 7.5], 'SR': [0, 7.5, 15], 'MBR': [7.5, 15, 22.5], 'BR': [15, 22.5, 30],
                      'VBR': [22.5, 30, 30]}
            },
            'omegaL': {
                'S': list(np.arange(0, 30, 0.3)),
                'rules': {
                    'VC': {'BN': 'VBL', 'N': 'BL', 'Z': 'VSL', 'P': 'SL', 'BP': 'VSL'},
                    'C': {'BN': 'VBL', 'N': 'BL', 'Z': 'SL', 'P': 'SL', 'BP': 'VSL'},
                    'M': {'BN': 'VBL', 'N': 'BL', 'Z': 'MBL', 'P': 'SL', 'BP': 'VSL'},
                    'F': {'BN': 'VBL', 'N': 'BL', 'Z': 'BL', 'P': 'SL', 'BP': 'VSL'},
                    'VF': {'BN': 'VBL', 'N': 'BL', 'Z': 'VBL', 'P': 'SL', 'BP': 'VSL'}
                },
                'mode': 'centroid',
                'M': {'VSL': [0, 0, 7.5], 'SL': [0, 7.5, 15], 'MBL': [7.5, 15, 22.5], 'BL': [15, 22.5, 30],
                      'VBL': [22.5, 30, 30]}
            }
        }
    },

    'robotState0': {
        'x': 0,
        'y': 0,
        'theta': -3.14 / 4
    },

    'path': [
        [0, 0, 0],  # X, Y, orientation
        [10, 0, 0],
        [30, 20, 0],
    ],

    'robotParams': {
        'r': 0.0925,
        'b': 0.37,
        'm': 9,
        'I': 0.16245,
        # 'motorParams': None,
        'motorParams': {
            'J': 0.01,
            'B': 0.1,

            'Kt': 0.01,
            'Ke': 0.01,
            'K': 0.01,

            'Ra': 0.1,
            'La': 0.01
        }
    },

    'controllerParams': {
        'omega_ri': 0, 'vri': 2.0, 'lowVelocityLimit': 0.2,
        'highVelocityLimit': 2.0, 'lowOmegaLimit': -0.75, 'highOmegaLimit': 0.75
    },
}

# ----------------------------------------
# upgraded from https://stackoverflow.com/questions/49330905/how-to-run-a-coroutine-and-wait-it-result-from-a-sync-func-when-the-loop-is-runn
# ----------------------------------------

def evalSet(asyncTask, values):
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
    evaluationTasks = [asyncio.run_coroutine_threadsafe(asyncTask(value), loop=loop) for value in values]
    # -- begin the thread to run the event-loop
    thread.start()
    # -- _synchronously_ wait for the result of my task
    results = [await_sync(task) for task in evaluationTasks]
    # close the loop gracefully when everything is finished
    close_loop_safe()
    thread.join()
    return results


# ----------------------------------------

def update_controllerDescription(baseControllerDescription, Chromosome):
    result = {**baseControllerDescription}

    """         this function shoould get the base controller
        and apply all the transormations based on the chromosome 
        and return a controller description that can be translated in a controller (or maybe directly a controller?)"""

    """ Chromosome: 
    for every linguistic variable, it contains
    C_SF, C_CP, C_CW, C_SW, C_GP,
    a, b, lambda, k_SF, k_CP, k_CW, k_SW, theta, k_GP
    i.e., 5+9 = 14 elements
    these elements characterize the modifications to make to all the partition characterizing that variable 
    i.e., to all the fuzzy sets related to it
    """
    nr_var_descriptors = 14

    for i in range(nr_ling_var):
        #here first I need to get the info about the partition related to the linguisticc variable (i.e., the fuzzy sets),
        for f in variable_fuzzysets:
            # then for each fuzzy set I need to apply the modifications.
            # to do so, I need to get the info about that set
            #in particular the four parameters characterizing the membership function
            cl = TOADD
            cu = TOADD
            sl = TOADD
            su = TOADD

            C_SF = Chromosome[0+(i*nr_var_descriptors)]
            C_CP = Chromosome[1+(i*nr_var_descriptors)]
            C_CW = Chromosome[2+(i*nr_var_descriptors)]
            C_SW = Chromosome[3+(i*nr_var_descriptors)]
            C_GP = Chromosome[4+(i*nr_var_descriptors)]
            a = Chromosome[5+(i*nr_var_descriptors)]
            b = Chromosome[6+(i*nr_var_descriptors)]
            lambd = Chromosome[7+(i*nr_var_descriptors)]
            k_SF = Chromosome[8+(i*nr_var_descriptors)]
            k_CP = Chromosome[9+(i*nr_var_descriptors)]
            k_CW = Chromosome[10+(i*nr_var_descriptors)]
            k_SW = Chromosome[11+(i*nr_var_descriptors)]
            theta = Chromosome[12+(i*nr_var_descriptors)]
            k_GP = Chromosome[13+(i*nr_var_descriptors)]

            if C_SF==1: #then I want to apply non-linear scaling
                #I'm ingoring it for now
                pass
            if C_CP==1: #CORE-POSITION MODIFIER enabled
                if k_CP<0:
                    cl = cl - ((sl - cl) * k_CP)
                    cu = cu - ((sl - cl) * k_CP)
                else:
                    cl = cl + ((su - cu) * k_CP)
                    cu = cu + ((su - cu) * k_CP)

            if C_CW==1: #core width modifier
                w=(cu-cl)/(cl-sl+su-cu)
                if k_CW<0:
                    cl = cl + (w * (sl - cl) * k_CW)
                    cu = cu + (w * (su - cu) * k_CW)
                else:
                    cl = cl + ((sl - cl) * k_CW)
                    cu = cu + ((su - cu) * k_CW)

            if C_SW==1: #support width modifier
                sm=(sl+su)/2
                sl = sm + (k_SW * (sl - sm))
                cl = sm + (k_SW * (cl - sm))
                cu = sm + (k_SW * (cu - sm))
                su = sm + (k_SW * (su - sm))

            if C_GP==1: #GENERALIZED POSITIVELY MODIFIER
                #I'm ingoring it for now
                pass



    return result

import aiohttp
import asyncio
#
# url = 'https://.............'# use your url here.
async def fitnessFunction(controller):
    """
    this function is the actual one that should contain the fitness
    :param controller:
    :return: should return a dictionary (or a json)
    """
    """
    if i understand correctly, I need to return 
    a dictionary which is the result for a certain chromosome, 
    that as a minimum contains an element for each fitness function.
    
    This function basically should
    1. create the controller from the controller description        
    2. compute the outputs of the controller (which should be, I think, a value for every possible social interpretation DIAMONDS? 
    I think this needs to depend on the particular conroller? but then should we run one genetic algo epr controller and have different interpretations every time? 
    or do we expect that the controllers will be consistent in their interpetations? mmm
    WHATEVER FOR NOW LET'S GO AHEAD WITH THE SOCIAL INTERPRETER) 
    3. use the output of the controller to determine function 1 (the mse w.r.t. data set, i.e., given the input then ocmpute the mse of the output)
    4. determine function 2 (the interpretability of the fuzzy rules) via the interepretability index 
    "measured by the average of the values of the index Phi_y computed for all input and output PARTITIONS of the frbs"
    
    Function 1 should be the MSE w.r.t. data set, i.e., for every data point which should contain a value of the input of the controllers (an accuracy measure)
    i.e., (sum for j from 1 to M of (F(xj)-yj)^2)/2M, with F(xj) the output of the contextualized FRBS when xj is the input 
    Function 2 is 
    1+ beta *sum_forv in variables, sum for n in number of fuzzy sets in the universe of the variablev, of p_v,n
    p_v,n = 1 if cp_v,n lower than CPL or if cp_v.n > CPU, 0 otherwise
    cp_v,n = value of membership at the crossing point between the n-th fuzzy set in the v-th universe and its rightmost adjacent.
    to obtain cp_v,n devi fare il seguente:
    from scipy.optimize import fsolve
    import numpy as np
    def f(xy, *data):
        x, y = xy
        fs1, fs2 = data
        z = np.array([y - fs1.get_value(x), y - fs2.get_value(x)])
        return z
    
    print(fsolve(f, [0.0, 0.0], args=(O1, O2)))
    where O1 and O2 are the two fuzzy sets to compare (N.B. MF_object from simpful), and all the rest you can leave as is.
    the fsolve will return the first point of intersection, i.e. a pair [x,y] with x the x value of intersecction and y the membership value
    
    [CPl, CP_U] IS THE INTERVAL OF ACCEPTABLE VALUES FOR THE CROSSING POINTS (e.g., 0.25 and 0.75, chosen to guarantee a minimum level of coverage and distinguishability as suggested by de Oliveira
    beta>=0 and <=1 is a tunable design parameter which controls the influence of the penalties with respect to the accuracy, 
    """

    return None

    # #async with aiohttp.ClientSession() as session:
    # async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
    #     response = await session.post(url, json=value, headers = {'content-type': 'application/x-json'})
    #     json_body = await response.json()
    # return json_body

def fitnessFunction_Multi_All(Chromosomes):
    """ this function should call a multithreading function that evaluates all chromosomes"""
    controllers = []
    for chromosome in Chromosomes:
        controllers.append(getControllerFromChromosome(base_controller, chromosome)) #here you should be able to create all necessary info to create a bunch of descriptions that will lead to creating a bunch of fuzzy controllers that should be evaluated w.r.t. their output I guess
    results = evalSet(fitnessFunction, controllers)
    return results


start_time = time.time()

class MyProblem(Problem):
    def __init__(self, n_var):
        super().__init__(n_var=n_var, # number of design variables
                         n_obj=2, # number of objectives
                         n_constr=0, # number of constraints
                         # lower bounds of the design variables
                         xl=np.array([0]*n_var),
                         # upper bounds of the design variables
                         xu=np.array([1]*n_var),
                         DAVIDE THESE BOUNDS ARE NOT CORRECT, THEY DEPEND ON THE PARAMETERS
                         elementwise_evaluation=False)

    def _evaluate(self, Chromosomes, out, *args, **kwargs):
        """
        This function will be called for every chromosome, and it will fill the dictionary out.
        out["F"] should contain the function values, while out["G"] should contain the values of contraints if more than one
        :param Chromosome:
        :param out:
        :param args:
        :param kwargs:
        :return:
        """
        results = fitnessFunction_Multi_All(Chromosomes) #computes the fitness function for all chromosomes.
        f1 = np.array([result['mse'] for result in results])
        f2 = np.array([result['avg_phi'] for result in results])
        out["F"] = [f1, f2]

n_var = TODEFINE# the number of linguistic variables in the rule base
""" Chromosome: 
for every variable it has
C_SF, C_CP, C_CW, C_SW, C_GP,
a, b, lambda, k_SF, k_CP, k_CW, k_SW, theta, k_GP
"""
mask = ["int", "int", "int", "int", "int",
        "real", "real", "real", "real", "real", "real", "real", "real", "real"]*n_var
from pymoo.factory import get_sampling, get_crossover, get_mutation
from pymoo.operators.mixed_variable_operator import MixedVariableSampling, MixedVariableMutation, MixedVariableCrossover

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

problem = MyProblem()

ref_points = np.array([[1.0]])

algorithmNSGA2 = NSGA2(pop_size=50,
                       sampling=sampling,
                       crossover=crossover,
                       mutation=mutation)

algorithmGA = GA(
    pop_size=50,
    sampling=sampling,
    crossover=crossover,
    mutation=mutation,
    eliminate_duplicates=True)

algorithmRNSGA2 = RNSGA2(
    ref_points=ref_points,
    pop_size=50,
   sampling=sampling,
   crossover=crossover,
   mutation=mutation
    )

algorithmNSGA3 = NSGA3(pop_size=50,
                  ref_dirs=ref_points,
                    sampling = sampling,
                    crossover = crossover,
                    mutation = mutation
)

algorithmUNSGA3 = UNSGA3(ref_points, pop_size=50,
                  sampling = sampling,
             crossover = crossover,
                         mutation = mutation
)

algorithmDE = DE(
    pop_size=50,
    sampling=LatinHypercubeSampling(iterations=150, criterion="maxmin"),
    variant="DE/rand/1/bin",
    CR=0.9,
    F=0.8,
    dither="vector",
    jitter=False,
   sampling=sampling,
   crossover=crossover,
   mutation=mutation
)


termination = get_termination("n_gen", 150)

resNSGA2 = minimize(problem,
               algorithmNSGA2,
               termination,
               seed=1,
               save_history=True,
               verbose=True)

resGA = minimize(problem,
               algorithmGA,
               termination,
               seed=1,
               save_history=True,
               verbose=True)

resRNSGA2 = minimize(problem,
               algorithmRNSGA2,
               termination,
               seed=1,
               save_history=True,
               verbose=True)
resNSGA3 = minimize(problem,
               algorithmNSGA3,
               termination,
               seed=1,
               save_history=True,
               verbose=True)
resUNSGA3 = minimize(problem,
               algorithmUNSGA3,
               termination,
               seed=1,
               save_history=True,
               verbose=True)
resDE = minimize(problem,
               algorithmDE,
               termination,
               seed=1,
               save_history=True,
               verbose=True)

print("Best solution found: \nBest_Chromosome = %s\nOptimal E = %s" % (resNSGA2.X, resNSGA2.F))
print("Best solution found: \nBest_Chromosome = %s\nOptimal E = %s" % (resGA.X, resGA.F))
print("Best solution found: \nBest_Chromosome = %s\nOptimal E = %s" % (resRNSGA2.X, resRNSGA2.F))
print("Best solution found: \nBest_Chromosome = %s\nOptimal E = %s" % (resNSGA3.X, resNSGA3.F))
print("Best solution found: \nBest_Chromosome = %s\nOptimal E = %s" % (resUNSGA3.X, resUNSGA3.F))
print("Best solution found: \nBest_Chromosome = %s\nOptimal E = %s" % (resDE.X, resDE.F))


print("Time required in second = %s" % (time.time() - start_time))
# Best_Chromosome = resNSGA3.X





def Fuzzy_control(Chromosome, omega_ri, vri, lowVelocityLimit, highVelocityLimit, lowOmegaLimit, highOmegaLimit):
    inputsDistance = {'VC': [0, 0, Chromosome[0]],
                      'C': [Chromosome[2] - Chromosome[1], Chromosome[2], Chromosome[2] + Chromosome[3]],
                      'M': [Chromosome[5] - Chromosome[4], Chromosome[5], Chromosome[5] + Chromosome[6]],
                      'F': [Chromosome[8] - Chromosome[7], Chromosome[8], Chromosome[8] + Chromosome[9]],
                      'VF': [2 - Chromosome[10], 2, 2]}
    inputsSpaceDistance = np.array(fitnessFunctionDescription['fuzzyDescription']['inputs']['distance']['S'])
    inputsAngle = {'BN': [-3.14, -3.14, -3.14 + Chromosome[11]],
                   'N': [Chromosome[13] - Chromosome[12], Chromosome[13], Chromosome[13] + Chromosome[14]],
                   'Z': [Chromosome[16] - Chromosome[15], Chromosome[16], Chromosome[16] + Chromosome[17]],
                   'P': [Chromosome[19] - Chromosome[18], Chromosome[19], Chromosome[19] + Chromosome[20]],
                   'BP': [3.14 - Chromosome[21], 3.14, 3.14]}
    inputsSpaceAngle = np.array(fitnessFunctionDescription['fuzzyDescription']['inputs']['angle']['S'])
    outputsOmegaR = {'VSR': [0, 0, Chromosome[22]],
                     'SR': [Chromosome[24] - Chromosome[23], Chromosome[24], Chromosome[24] + Chromosome[25]],
                     'MBR': [Chromosome[27] - Chromosome[26], Chromosome[27], Chromosome[27] + Chromosome[28]],
                     'BR': [Chromosome[30] - Chromosome[29], Chromosome[30], Chromosome[30] + Chromosome[31]],
                     'VBR': [30 - Chromosome[32], 30, 30]}
    outputSpaceOmegaR = np.array(fitnessFunctionDescription['fuzzyDescription']['outputs']['omegaR']['S'])
    outputsOmegaL = {'VSL': [0, 0, Chromosome[33]],
                     'SL': [Chromosome[35] - Chromosome[34], Chromosome[35], Chromosome[35] + Chromosome[36]],
                     'MBL': [Chromosome[38] - Chromosome[37], Chromosome[38], Chromosome[38] + Chromosome[39]],
                     'BL': [Chromosome[41] - Chromosome[40], Chromosome[41], Chromosome[41] + Chromosome[42]],
                     'VBL': [30 - Chromosome[43], 30, 30]}
    outputSpaceOmegaL = np.array(fitnessFunctionDescription['fuzzyDescription']['outputs']['omegaL']['S'])
    outputRulesOmegaR = {
        'VC': {'BN': 'VSR', 'N': 'SR', 'Z': 'VSR', 'P': 'BR', 'BP': 'VBR'},
        'C': {'BN': 'VSR', 'N': 'SR', 'Z': 'SR', 'P': 'BR', 'BP': 'VBR'},
        'M': {'BN': 'VSR', 'N': 'SR', 'Z': 'MBR', 'P': 'BR', 'BP': 'VBR'},
        'F': {'BN': 'VSR', 'N': 'SR', 'Z': 'BR', 'P': 'BR', 'BP': 'VBR'},
        'VF': {'BN': 'VSR', 'N': 'SR', 'Z': 'VBR', 'P': 'BR', 'BP': 'VBR'}
    }
    outputRulesOmegaL = {
        'VC': {'BN': 'VBL', 'N': 'BL', 'Z': 'VSL', 'P': 'SL', 'BP': 'VSL'},
        'C': {'BN': 'VBL', 'N': 'BL', 'Z': 'SL', 'P': 'SL', 'BP': 'VSL'},
        'M': {'BN': 'VBL', 'N': 'BL', 'Z': 'MBL', 'P': 'SL', 'BP': 'VSL'},
        'F': {'BN': 'VBL', 'N': 'BL', 'Z': 'BL', 'P': 'SL', 'BP': 'VSL'},
        'VF': {'BN': 'VBL', 'N': 'BL', 'Z': 'VBL', 'P': 'SL', 'BP': 'VSL'}
    }

    def createFuzzyfier(space, categories, trimf=fuzz.trimf, membership=fuzz.interp_membership):
        fuzzyInput = {}
        for key, value in categories.items():
            fuzzyInput[key] = trimf(space, value)

        def result(variable):
            output = {}
            for key, value in fuzzyInput.items():
                output[key] = membership(space, value, variable)
            if output[key] == 0:
                output[key] = 1e-5
            else:
                output[key] = output[key]
            return output

        return result

    def createInferenceSystem(inputAfuzzyfier, inputBfuzzyfier, outputSpace, outputDict, rulesDict, trimf=fuzz.trimf):
        fuzzyResults = {}
        for keyA, outerValue in rulesDict.items():
            if not (keyA in fuzzyResults):
                fuzzyResults[keyA] = {}
            for keyB, innerValue in outerValue.items():
                fuzzyResults[keyA][keyB] = trimf(outputSpace,
                                                 outputDict[innerValue])  # innerValue==outputDict[keyA][keyB]

        def result(valueA, valueB):
            fuzzyVariableA = inputAfuzzyfier(valueA)
            fuzzyVariableB = inputBfuzzyfier(valueB)
            fuzzyResult = None
            for keyA, outerValue in rulesDict.items():
                for keyB, resultValue in outerValue.items():
                    currentResult = np.fmin(fuzzyResults[keyA][keyB],
                                            np.fmin(fuzzyVariableA[keyA], fuzzyVariableB[keyB]))
                    if fuzzyResult is None:
                        fuzzyResult = currentResult
                    else:
                        fuzzyResult = np.fmax(currentResult, fuzzyResult)
            return fuzzyResult

        return result

    def createDefuzzyfier(outputSpace, *defuzzArgs, defuzz=fuzz.defuzz, **defuzzKwargs):
        def result(value):
            return defuzz(outputSpace, value, *defuzzArgs, **defuzzKwargs)

        return result

    def createFullFuzzySystem(inferenceSystem, defuzzyfier):
        def system(inputA, inputB):
            return defuzzyfier(inferenceSystem(inputA, inputB))

        return system

    inputsDistanceFuzzyfier = createFuzzyfier(inputsSpaceDistance, inputsDistance)
    inputsAngleFuzzyfier = createFuzzyfier(inputsSpaceAngle, inputsAngle)

    inferenceSystem_R = createInferenceSystem(inputsDistanceFuzzyfier, inputsAngleFuzzyfier, outputSpaceOmegaR,
                                              outputsOmegaR, outputRulesOmegaR)
    outputDefuzzyfier_R = createDefuzzyfier(outputSpaceOmegaL, mode='centroid')

    inferenceSystem_L = createInferenceSystem(inputsDistanceFuzzyfier, inputsAngleFuzzyfier, outputSpaceOmegaL,
                                              outputsOmegaL, outputRulesOmegaL)
    outputDefuzzyfier_L = createDefuzzyfier(outputSpaceOmegaL, mode='centroid')

    fullSystem_R = createFullFuzzySystem(inferenceSystem_R, outputDefuzzyfier_R)
    fullSystem_L = createFullFuzzySystem(inferenceSystem_L, outputDefuzzyfier_L)

    def controller(t, currentState, destinationState):
        currentX = currentState[0]
        currentY = currentState[1]
        currentTheta = currentState[2]

        destinationX = destinationState[0]
        destinationY = destinationState[1]

        cosTheta = cos(currentTheta)
        sinTheta = sin(currentTheta)

        deltaX = destinationX - currentX
        deltaY = destinationY - currentY
        theta_destination = atan2(deltaY, deltaX)
        THETA_ERROR = theta_destination - currentTheta
        DISTANCE_ERROR = sqrt(deltaX * deltaX + deltaY * deltaY)

        if (THETA_ERROR > pi):
            THETA_ERROR -= 2 * pi
        if (THETA_ERROR < -pi):
            THETA_ERROR += 2 * pi

        omega_R = fullSystem_R(DISTANCE_ERROR, THETA_ERROR)
        omega_L = fullSystem_L(DISTANCE_ERROR, THETA_ERROR)

        velocity = fitnessFunctionDescription['robotParams']['r'] * (omega_R + omega_L) / 2
        omega = fitnessFunctionDescription['robotParams']['r'] * (omega_R - omega_L) / \
                fitnessFunctionDescription['robotParams']['b']

        if velocity > highVelocityLimit:
            velocity = highVelocityLimit
        if (velocity < lowVelocityLimit):
            velocity = lowVelocityLimit
        if omega > highOmegaLimit:
            omega = highOmegaLimit
        if (omega < lowOmegaLimit):
            omega = lowOmegaLimit

        return velocity, omega

    return controller


def controllerUsingGenes_FLC(pathForSimulation):
    t0 = 0
    t_bound = 40
    max_step = 0.05
    state0 = None
    if robot == robotWithDynamic:
        state0 = np.array(
            [robotState0['x'], robotState0['y'], robotState0['theta'], 0, 0, 0, 0, 0, 0, 0])  # x0=0, y0=0, theta
    else:
        state0 = np.array([robotState0['x'], robotState0['y'], robotState0['theta'], 0, 0, 0])  # x0=0, y0=0,theta

    solverfunc = simpleCompute(
        compute, state0=state0,
        t0=t0, t_bound=t_bound, max_step=max_step)

    # --------------------for Fuzzy and GA_FLC-------------------------------------------------
    def controllerForGenes_Fuzzy(chromosome_Fuzzy):
        def transformGeneIntoControllerParams(chromosome_Fuzzy):
            controllerParams_Fuzzy = {'Chromosome': chromosome_Fuzzy,
                                      'omega_ri': fitnessFunctionDescription['controllerParams']['omega_ri'],
                                      'vri': fitnessFunctionDescription['controllerParams']['vri'],
                                      'lowVelocityLimit': fitnessFunctionDescription['controllerParams'][
                                          'lowVelocityLimit'],
                                      'highVelocityLimit': fitnessFunctionDescription['controllerParams'][
                                          'highVelocityLimit'],
                                      'lowOmegaLimit': fitnessFunctionDescription['controllerParams']['lowOmegaLimit'],
                                      'highOmegaLimit': fitnessFunctionDescription['controllerParams'][
                                          'highOmegaLimit']}
            return controllerParams_Fuzzy

        createController_Fuzzy = Fuzzy_control

        def createRobot():
            controllerParams_Fuzzy = transformGeneIntoControllerParams(chromosome_Fuzzy)
            robot = robotModelCreator(createController_Fuzzy, pathForSimulation, **controllerParams_Fuzzy)
            return robot

        def runSimulation(robot):
            robotStates = solverfunc(robot)
            velocitys = []
            omegas = []
            timeStep = []
            x_axis = []
            y_axis = []
            s = []
            E = []
            for currentState in robotStates:  # readout all states from current moving robot
                velocity = currentState['dy'][3]
                velocitys.append(velocity)
                omega = currentState['dy'][4]
                omegas.append(omega)
                time = currentState['time']
                timeStep.append(time)
                x = currentState['y'][0]
                x_axis.append(x)
                y = currentState['y'][1]
                y_axis.append(y)
                s_step = currentState['y'][3]
                s.append(s_step)
                E_step = currentState['TotalEnergy']
                E.append(E_step)
            return velocitys, omegas, timeStep, x_axis, y_axis, s, E

        robot = createRobot()
        velocitys, omegas, timeStep, x_axis, y_axis, s, E = runSimulation(robot)

        return velocitys, omegas, timeStep, x_axis, y_axis, s, E

    return controllerForGenes_Fuzzy