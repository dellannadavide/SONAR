import copy

from spade.behaviour import PeriodicBehaviour, OneShotBehaviour

from mas.agent.workeragent import WorkerAgent
from simpful import *

from utils import utils
import utils.constants as Constants

from datetime import timedelta, datetime

import math

from simpful import *

import sys
import os

# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))
# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)
# adding the parent directory to
# the sys.path.
sys.path.append(parent)

from mas.utils.fsutils import linearScaleUniverseToA1B1, getDissimilarity
from utils import utils
import numpy as np
import utils.constants as Constants

import logging
logger = logging.getLogger("nosar.mas.agent.worker.normadapter")

class NormAdapter(WorkerAgent):

    class PerformAdaptation(OneShotBehaviour):
        def __init__(self, data, aggr_knowledge, var_maxmin):
            super().__init__()
            self.data = data
            self.aggr_knowledge = aggr_knowledge
            self.var_maxmin = var_maxmin

        def tooDifferent(self, universe_boundaries, new_mf_param, curr_mf_param, ling_var):
            dissimilarity = getDissimilarity(universe_boundaries, new_mf_param, curr_mf_param)
            if (not ling_var in self.agent.curr_adaptation) or self.agent.curr_adaptation[ling_var] == 0:
                self.agent.curr_adaptation[ling_var] = 0
                return False
            logging.info("-------Revision of {} {} : {} {}".format(ling_var, self.agent.curr_adaptation[ling_var], dissimilarity,
                  self.getMaxDissimilarityForCurrentAdaptation(self.agent.curr_adaptation[ling_var])))
            return dissimilarity > self.getMaxDissimilarityForCurrentAdaptation(
                self.agent.curr_adaptation[ling_var])  # if it is bigger return true, i.e., it is tooDifferent

        def getMaxDissimilarityForCurrentAdaptation(self, curr_adaptation):
            return (2 ** (-(curr_adaptation / (math.log(2) / self.agent.lamb))))

        def adaptRuleBase(self, fuzzy_social_system, dp, data, curr_adaptation):
            rulebase = copy.deepcopy(fuzzy_social_system.getRuleBase())
            social_int = dp[Constants.TOPIC_SOCIAL_INTERPR]
            lvs = rulebase.getLVSFromRulesContainingHighValuesOf(
                social_int)  # returns a dictionary rule: list of linguistic variables (strings) in rule
            # print("\tData point is: ", str(dp))
            logging.info("\tSocial interpretation is " + str(social_int))
            logging.info("\tRules (and associated ling. var) containing '{} IS high (or similar)' are {}".format(str(social_int),
                  str(lvs)))

            adapted_lingVar = []
            for r in lvs.keys():  # for all rules
                for lv in lvs[r]:  # for each linguistic variable (string) in the dictionary
                    if (str(lv).strip() in Constants.DYNAMIC_LV) and (not lv == social_int) and (str(lv) in dp.keys()):
                        current_fuzzy_ling_var = rulebase.ling_vars_dict[
                            lv]  # retrieve the fuzzy linguistic variable (e.g., DIST) N.B. I am retrieving a SARFuzzyLingVar
                        partition = current_fuzzy_ling_var.fuzzy_sets  # partition a list of DynamicTrapezoidFuzzySet

                        fuzzy_set = None  # retrieve the fuzzy_set (e.g., mid_dist if the rule contains mid_dist)
                        term = None
                        trap_fs = None
                        for fs in partition:  # for each dynamic trapezoid fuzzy set in the partition
                            if (lv + " IS " + str(
                                    fs._term)) in r:  # if it's term is in the rule associated with the linguistic variable
                                trap_fs = fs
                                fuzzy_set = rulebase.fuzzy_sets_dict[
                                    fs._term]  # I retrieve the SARFuzzySet with the same term in the rule base
                                term = lv + " IS " + str(fs._term)
                                break  # I stop immediately once I find it because I assume only one fs per variable in a rule

                        if (not term is None) and (not lv in adapted_lingVar):
                            # print("\tterm is ", str(term))
                            data_mean_value = float(dp[lv][0])  # todo aassuming they are always numerical
                            data_stdev_value = float(dp[lv][1])  # todo aassuming they are always numerical
                            data_max_value = float(dp[lv][2])
                            data_min_value = float(dp[lv][3])

                            # data_width = 2*data_stdev_value # width of interval [mu-stdev, mu+stdev] = (mu+stedv)-(mu-stdev) = 2stdev
                            data_width = data_stdev_value  # we chose to aim at a with of the trapezoid large as 1 stdev
                            logging.info("\tdata mean value of " + str(lv) + " " + str(fuzzy_set.term) + ": " + str(
                                data_mean_value))
                            logging.info("\tdata stdev value of " + str(lv) + " " + str(fuzzy_set.term) + ": " + str(
                                data_stdev_value))
                            logging.info(
                                "\tdata min value of " + str(lv) + " " + str(fuzzy_set.term) + ": " + str(
                                    data_min_value))
                            logging.info("\tdata max value of " + str(lv) + " " + str(fuzzy_set.term) + ": " + str(
                                data_max_value))

                            if data_stdev_value>0 and data_min_value!=data_max_value:
                                """ I want to first scale the universe and all variables, if necessary """
                                curr_uni = current_fuzzy_ling_var.ling_var._universe_of_discourse
                                logging.info("\tcurrent universe of " + str(current_fuzzy_ling_var) + ": " + str(curr_uni))
                                new_universe = linearScaleUniverseToA1B1(current_fuzzy_ling_var.ling_var,
                                                                         self.var_maxmin[lv]["min"],
                                                                         self.var_maxmin[lv]["max"])
                                current_fuzzy_ling_var.universe_of_discourse = new_universe
                                logging.info("\tnew universe of " + str(current_fuzzy_ling_var) + ": " + str(
                                    current_fuzzy_ling_var.universe_of_discourse))
                                # for fs in partition:
                                #     new_mfs = fs.scaleLinear(curr_uni[0], curr_uni[1], data_min_value, data_max_value)
                                #     rulebase.updateMFParams(fs._term, new_mfs)
                                new_mf = trap_fs.updateSupportBoundaries(data_min_value, data_max_value)
                                rulebase.updateMFParams(trap_fs._term, new_mf)

                                curr_mfs = fuzzy_set.getMF()  # fuzzy_set is a SARFuzzySet. getMF() returns its attribute "param", which is a dictionary of parameters (e.g., {"a": float}
                                curr_sl = float(curr_mfs["a"])
                                curr_cl = float(curr_mfs["b"])
                                curr_cu = float(curr_mfs["c"])
                                curr_su = float(curr_mfs["d"])
                                curr_mid_value = (curr_cu + curr_cl) / 2.0  # todo assuming for now it is trapezoid
                                curr_width = (curr_cu - curr_cl)

                                logging.info(
                                    "\tcurr cor pos of " + str(lv) + " " + str(fuzzy_set.term) + ": " + str(curr_mid_value))
                                logging.info("\tcurr width of " + str(lv) + " " + str(fuzzy_set.term) + ": " + str(curr_width))
                                logging.info(curr_mfs)

                                # compute the error between the mid value in the fuzzy set and the value in the collected knowledge
                                error_core_position = curr_mid_value - data_mean_value
                                logging.info("\terror core pos:" + str(error_core_position))
                                if error_core_position >= 0:  # then change will be <0 -> we are moving left, so we want to compute the ratio w.r.t. the left part
                                    den = (curr_cl - curr_sl) if (curr_cl - curr_sl) > 0 else 1.0
                                    error_core_position = min(1.0, error_core_position / den)
                                    # error_core_position = min(1.0, error_core_position)
                                else:
                                    den = (curr_su - curr_cu) if (curr_su - curr_cu) > 0 else 1.0
                                    error_core_position = max(-1.0, error_core_position / den)
                                    # error_core_position = max(-1.0, error_core_position)
                                logging.info("\tNORMALIZED error core pos:" + str(error_core_position))
                                # perform inference with the self.FS to determine the change
                                # self.FS.set_variable(self.error_name, error_core_position)
                                # fs_output = self.FS.Mamdani_inference()
                                # change_core_position = float(fs_output[self.change_name])
                                change_core_position = -1 * error_core_position
                                # """ instead of using an inference system I just take the inverse of the error """
                                # change_core_position = error_core_position*-1
                                logging.info("\tcomputed K_CP, change param for core position:" + str(change_core_position))

                                # compute the error between the mid value in the fuzzy set and the value in the collected knowledge
                                error_core_width = curr_width - data_width
                                logging.info("\terror core width:" + str(error_core_width))

                                # if k_CW < 0:
                                #     self._funpointer._b = b + (w * (a - b) * k_CW)
                                #     self._funpointer._c = c + (w * (d - c) * k_CW)
                                # else:
                                #     self._funpointer._b = b + ((a - b) * k_CW)
                                #     self._funpointer._c = c + ((d - c) * k_CW)

                                if error_core_width >= 0:  # the change will be then <0
                                    # i want to compute error_ratio, i.e. error/den
                                    denom = (curr_cl - curr_sl + curr_su - curr_cu)
                                    w = (curr_cu - curr_cl) / denom if denom > 0 else 0
                                    den_b = (w * (curr_cl - curr_sl)) if w * (curr_cl - curr_sl) > 0 else 1.0
                                    error_ratio_b = error_core_width / den_b
                                    den_c = (w * (curr_su - curr_cu)) if w * (curr_su - curr_cu) > 0 else 1.0
                                    error_ratio_c = error_core_width / den_c
                                    error_core_width = min(1.0, error_ratio_b, error_ratio_c)
                                else:
                                    den_b = (curr_cl - curr_sl) if (curr_cl - curr_sl) > 0 else 1.0
                                    den_c = (curr_su - curr_cu) if (curr_su - curr_cu) > 0 else 1.0
                                    error_ratio_b = error_core_width / den_b
                                    error_ratio_c = error_core_width / den_c
                                    error_core_width = max(-1.0, error_ratio_b, error_ratio_c)
                                logging.info("\tNORMALIZED error core width:" + str(error_core_width))
                                # perform inference with the self.FS to determine the change
                                # self.FS.set_variable(self.error_name, error_core_width)
                                # fs_output = self.FS.Mamdani_inference()
                                # change_core_with = float(fs_output[self.change_name])
                                change_core_with = -1 * error_core_width
                                # """ instead of using an inference system I just take the inverse of the error """
                                # change_core_with = error_core_width * -1
                                logging.info("\tcomputed K_CW, change param for core width:" + str(change_core_with))

                                # once I computed the error and the consequent change for the particular fuzzy set,
                                # then I want to apply the changes to all sets in the partition

                                for fs in partition:  # fs is a DynamicTrapezoidFuzzySet
                                    logging.info(fs)
                                    curr_params_dict = fs.get_params_dict()
                                    """ First applying core-position modifier """
                                    c_mfs = fs.get_params()  # c_mfs is actually a TUPLE of all parameters of the fuzzyset
                                    logging.info("\tcurrent mfs:" + str(c_mfs))
                                    new_mfs = fs.modifyCorePosition(
                                        change_core_position)  # new_mfs should be a dictionary, and the function should DIRECTLY MODIFY THE MEMBERSHIP FUNCTION
                                    logging.info("\tnew mfs:" + str(fs.get_params()))
                                    logging.info(new_mfs)
                                    rulebase.updateMFParams(fs._term,
                                                            new_mfs)  # this should create a new trapezoidfuzzyset and update it
                                    """ Then applying core-width modifier """
                                    c_mfs = fs.get_params()  # c_mfs is actually a TUPLE of all parameters of the fuzzyset
                                    logging.info("\tcurrent mfs:" + str(c_mfs))
                                    new_mfs = fs.modifyCoreWidth(
                                        change_core_with)  # new_mfs should be a dictionary, and the function should DIRECTLY MODIFY THE MEMBERSHIP FUNCTION
                                    logging.info("\tnew mfs:" + str(fs.get_params()))
                                    logging.info(new_mfs)
                                    rulebase.updateMFParams(fs._term,
                                                            new_mfs)  # this should create a new trapezoidfuzzyset and update it

                                    if self.agent.optim_param["consider_past_experience"]:
                                        if self.tooDifferent(new_universe, new_mfs, curr_params_dict, str(lv)):
                                            # if it is too different I revert
                                            fs.set_params_dict(curr_params_dict)
                                            rulebase.updateMFParams(fs._term, curr_params_dict)
                                            logging.info("\ttoo different, correct the to  mfs:" + str(curr_params_dict))
                                adapted_lingVar.append(str(lv))
            if len(adapted_lingVar) > 0:
                for lv in adapted_lingVar:
                    if (not lv in self.agent.curr_adaptation):
                        self.agent.curr_adaptation[lv] = 0
                    self.agent.curr_adaptation[lv] = self.agent.curr_adaptation[lv] + 1
                self.agent.curr_adaptation_all = self.agent.curr_adaptation_all + 1
                new_fuzzy_system = rulebase.createFuzzySystem()
                rulebase.setFuzzySystem(new_fuzzy_system)
                fuzzy_social_system.updateRuleBase(rulebase)

            if self.agent.optim_param["contextualize"]:
                """ 
                Then I adjust the core width and the support width via MOEA (I call this contextualization) in order to maximize interpretability
                """
                if (self.agent.curr_adaptation_all % self.agent.optim_param["min_nr_adaptations_for_contextualizing"]) == 0:
                    fuzzy_social_system.contextualize(data, self.agent.optim_param)

        async def run(self):
            self.agent.adapting = True
            """
                                I first perform adaptation of the core position of the FuzzySets based on the averaged knowledge collected
                                """
            logging.info("Adaptation of the fuzzy sets...")
            for social_int in self.aggr_knowledge.keys():
                logging.info(social_int)
                dp = self.aggr_knowledge[social_int]
                # print("social interpreter")
                # self.adaptRuleBase(self.agent.fsi, dp, self.data, self.agent.curr_adaptation)
                for fsq in self.agent.fsq:
                    logging.info("social qualifier " + str(fsq))
                    self.adaptRuleBase(self.agent.fsq[fsq], dp, self.data, self.agent.curr_adaptation)

            self.agent.adapting = False

    class AdaptNorms(PeriodicBehaviour):
        def __init__(self, period, start_at):
            super().__init__(period, start_at)
            self.timeout_data_source = period
            logging.info("this is the behavior to startr")

        async def run(self):
            logging.info("I hould be running the behavior of norma adapt")
            logging.info("collected knowledge")
            logging.info(self.agent.collected_knowledge)
            logging.info(self.agent.adapting)
            """ Here, this is the actual procedure that will revise the norms.
            What it has to do is the following:
            1. check if the self.agent.collected_knowledge is not empty (i.e., if there is something useful to use for norm adaptation)
            2. for every data point collected, revise the membership functions of the rules.
            This needs to be done for every rule basein the system
            (i.e.,both for the social interpreter and for the social qualifiers etc.)
            """
            if (
            not self.agent.adapting):  # and (len(self.agent.collected_knowledge)>self.agent.min_nr_datapoints_for_adaptation):
                # print("Adapting the rules in all fuzzy rule bases...")

                # print("collected knowledge")
                # print(self.agent.collected_knowledge)
                data = copy.deepcopy(self.agent.collected_knowledge)

                aggr_knowledge = {}
                for social_interpretation in Constants.SOCIAL_INTERPRETATIONS:
                    if (len(self.agent.collected_knowledge_per_social_int[
                                social_interpretation]) % self.agent.min_nr_datapoints_for_adaptation) == 0:
                        # print("LEngth of collected knowledge for ", social_interpretation, ": ",
                        #       str(len(self.agent.collected_knowledge_per_social_int[social_interpretation])))
                        # print(self.agent.collected_knowledge_per_social_int[social_interpretation])
                        for dp in self.agent.collected_knowledge_per_social_int[social_interpretation]:
                            # print("data point")
                            # print(dp)
                            social_int = dp[Constants.TOPIC_SOCIAL_INTERPR]
                            # print(social_int)
                            # print("aggr knowledge")
                            # print(aggr_knowledge)
                            if not social_int in aggr_knowledge.keys():
                                aggr_knowledge[social_int] = {}  # dp should be a dictionary
                                for v in dp.keys():
                                    if not (v == Constants.TOPIC_SOCIAL_INTERPR):
                                        aggr_knowledge[social_int][v] = [float(dp[v])]
                                    else:
                                        aggr_knowledge[social_int][v] = dp[v]
                            else:  # social int is already in aggr knowledge
                                for var in dp.keys():
                                    # print(var)
                                    if not (var == Constants.TOPIC_SOCIAL_INTERPR):
                                        # print(aggr_knowledge[social_int].keys())
                                        if var in aggr_knowledge[social_int].keys():
                                            aggr_knowledge[social_int][var].append(float(dp[var]))
                                        else:
                                            aggr_knowledge[social_int][var] = [float(dp[var])]
                            # print("aggr knowledge")
                            # print(aggr_knowledge)
                        self.agent.collected_knowledge_per_social_int[social_interpretation] = []

                for social_int in aggr_knowledge:
                    for var in aggr_knowledge[social_int]:
                        # if not var == Constants.TOPIC_SOCIAL_INTERPR:
                        if var in Constants.DYNAMIC_LV:
                            a = np.array([aggr_knowledge[social_int][var]])
                            avg = np.mean(a)
                            stdev = np.std(a)
                            data_max = np.max(a)
                            data_min = np.min(a)

                            if social_int in self.agent.variables_maxmin:
                                if var in self.agent.variables_maxmin[social_int]:
                                    global_max = max(data_max, self.agent.variables_maxmin[social_int][var]["max"])
                                    data_max = global_max
                                    self.agent.variables_maxmin[social_int]["max"] = global_max
                                    global_min = min(data_min, self.agent.variables_maxmin[social_int][var]["min"])
                                    data_min = global_min
                                    self.agent.variables_maxmin[social_int][var]["min"] = global_min
                                else:
                                    self.agent.variables_maxmin[social_int][var] = {}
                                    self.agent.variables_maxmin[social_int][var]["max"] = data_max
                                    self.agent.variables_maxmin[social_int][var]["min"] = data_min
                            else:
                                self.agent.variables_maxmin[social_int] = {}
                                self.agent.variables_maxmin[social_int][var] = {}
                                self.agent.variables_maxmin[social_int][var]["max"] = data_max
                                self.agent.variables_maxmin[social_int][var]["min"] = data_min

                            if var in self.agent.var_maxmin:
                                self.agent.var_maxmin[var]["max"] = max(self.agent.var_maxmin[var]["max"],
                                                                  self.agent.variables_maxmin[social_int][var]["max"])
                                self.agent.var_maxmin[var]["min"] = min(self.agent.var_maxmin[var]["min"],
                                                                  self.agent.variables_maxmin[social_int][var]["min"])
                            else:
                                self.agent.var_maxmin[var] = {}
                                self.agent.var_maxmin[var]["max"] = self.agent.variables_maxmin[social_int][var]["max"]
                                self.agent.var_maxmin[var]["min"] = self.agent.variables_maxmin[social_int][var]["min"]

                            logging.info("Avg and Stdev (and min and max) of {} for {}: {}, {} ({}, {})".format(var, social_int, avg, stdev, data_min,
                                  data_max))
                            aggr_knowledge[social_int][var] = [avg, stdev, data_max, data_min]
                # now in averaged_knowledge I should have all collected knowledge but averaged per social interpretation
                # print("aggr knoeldge")
                # print(aggr_knowledge)

                # for dp in self.agent.collected_knowledge:
                if len(aggr_knowledge) > 0:
                    b = self.agent.PerformAdaptation(data, aggr_knowledge, copy.deepcopy(self.agent.var_maxmin))
                    self.agent.add_behaviour(b)


    async def setup(self):
        await super().setup()
        logging.info("starting up norm adapter")

        self.curr_adaptation = {}
        self.curr_adaptation_all = 0
        self.lamb = 0.001

        self.FS = FuzzySystem()

        self.terms = ["neg_very_large", "neg_large", "neg", "neglig", "pos", "pos_large", "pos_very_large"]
        self.error_name = "error"
        self.change_name = "change"

        TLV = AutoTriangle(len(self.terms), terms=self.terms, universe_of_discourse=[-1, 1])
        TLV2 = AutoTriangle(len(self.terms), terms=self.terms, universe_of_discourse=[-1, 1])
        self.FS.add_linguistic_variable(self.error_name, TLV)
        self.FS.add_linguistic_variable(self.change_name, TLV2)
        rules = []
        for t_idx in range(len(self.terms)):
            error = self.terms[t_idx]
            change = self.terms[len(self.terms) - 1 - t_idx]
            rules.append(
                "IF (" + self.error_name + " IS " + error + ") THEN (" + self.change_name + " IS " + change + ")")
        self.FS.add_rules(rules)

        self.collected_knowledge = []
        self.collected_knowledge_per_social_int = {}
        self.variables_maxmin = {}
        self.var_maxmin = {}
        for social_inter in Constants.SOCIAL_INTERPRETATIONS:
            self.collected_knowledge_per_social_int[social_inter] = []

        self.min_nr_datapoints_for_adaptation = 3
        self.optim_param = {
            "algo": Constants.NSGA3,
            "pop_size": 20,
            "n_gen": 100,
            "scale": False,
            "core-pos": False,
            "core-width": False,
            "support-width": True,
            "gp": False,
            "n_obj_f": 2,
            "interpretability_index": Constants.PHI_INTERPRETABILITY_INDEX,
            "consider_past_experience": True,
            "contextualize": False,
            "min_nr_adaptations_for_contextualizing": 10
        }

        nr_var_descriptors = 0
        if self.optim_param["scale"]:
            nr_var_descriptors += 5
        if self.optim_param["core-pos"]:
            nr_var_descriptors += 2
        if self.optim_param["core-width"]:
            nr_var_descriptors += 2
        if self.optim_param["support-width"]:
            nr_var_descriptors += 2
        if self.optim_param["gp"]:
            nr_var_descriptors += 3
        self.optim_param["nr_param_per_var"] = nr_var_descriptors

        self.adapting = False

        # if not params is None:
        #     self.optim_param["algo"] = params["genetic_algo"]
        #     self.optim_param["pop_size"] = params["pop_size"]
        #     self.optim_param["n_gen"] = params["ga_nr_gen"]
        #     self.optim_param["interpretability_index"] = params["interpretability_index"]
        #     self.min_nr_datapoints_for_adaptation = params["min_nr_datapoints"]
        #     self.optim_param["contextualize"] = params["contextualize"]
        #     self.optim_param["min_nr_adaptations_for_contextualizing"] = params[
        #         "min_nr_adaptations_for_contextualizing"]
        #     self.optim_param["consider_past_experience"] = params["consider_past_experience"]
        #     if self.optim_param["consider_past_experience"]:
        #         self.optim_param["n_obj_f"] = 2
        #         self.optim_param["algo"] = Constants.NSGA3

        logging.info("setting up the behavior to startr")
        start_at = datetime.now() + timedelta(seconds=5)
        b = self.AdaptNorms(period=6, start_at=start_at)
        self.add_behaviour(b)


    async def do_work(self, work_info_dict):
        """ message is the message from the data collector with all the info
        it is a string which represents a list, where element 0 is the topic of element 1, and element 2 is the topic of element 2, etc."""
        logging.info("NORMADAPTER received message from data coll: {}".format(work_info_dict))
        # work_info_list = utils.splitStringToList(message)
        # nr_pairs = int(len(work_info_list) / 2)  # n.b. it is expected to be always even
        # data_point = {}
        # done = 0
        # for i in range(nr_pairs):
        #     topic = work_info_list[done + i]
        #     value = work_info_list[done + i + 1]
        #
        #     if not (topic == Constants.TOPIC_SOCIAL_INTERPR):
        #         value = float(value)
        #
        #     data_point[topic] = value
        #     done = done + 1
        self.collected_knowledge.append(work_info_dict)

        social_int = work_info_dict[Constants.TOPIC_SOCIAL_INTERPR]
        self.collected_knowledge_per_social_int[social_int].append(work_info_dict)

        logging.info("NORMADAPTER, kowledge:")
        logging.info(self.collected_knowledge)
        logging.info(self.collected_knowledge_per_social_int)








