import copy

from spade.behaviour import PeriodicBehaviour, OneShotBehaviour

from sar.agent.workeragent import WorkerAgent
from simpful import *

from sar.utils.fsutils import linearScaleUniverseToA1B1
from utils import utils
import utils.constants as Constants

from datetime import timedelta, datetime
import numpy as np


class NormAdapter2SIM(WorkerAgent):

    class AdaptNorms(OneShotBehaviour):
        def __init__(self):
            super().__init__()

        def adaptRuleBase(self, fuzzy_social_system, dp):

            rulebase = copy.deepcopy(fuzzy_social_system.getRuleBase())
            social_int = dp[Constants.TOPIC_SOCIAL_INTERPR]
            lvs = rulebase.getLVSFromRulesContainingHighValuesOf(social_int) #returns a dictionary rule: list of linguistic variables (strings) in rule
            # print("\tData point is: ", str(dp))
            # print("\tSocial interpretation is "+str(social_int))
            # print("\tRules (and associated ling. var) containing '", str(social_int), "IS high' are ", str(lvs))

            adapted_lingVar = []
            for r in lvs.keys(): #for all rules
                for lv in lvs[r]: #for each linguistic variable (string) in the dictionary
                    if (str(lv).strip() in Constants.DYNAMIC_LV) and (not lv == social_int) and (str(lv) in dp.keys()):
                        current_fuzzy_ling_var = rulebase.ling_vars_dict[lv] #retrieve the fuzzy linguistic variable (e.g., DIST) N.B. I am retrieving a SARFuzzyLingVar
                        partition = current_fuzzy_ling_var.fuzzy_sets #partition a list of DynamicTrapezoidFuzzySet

                        fuzzy_set = None #retrieve the fuzzy_set (e.g., mid_dist if the rule contains mid_dist)
                        term = None
                        for fs in partition: #for each dynamic trapezoid fuzzy set in the partition
                            if (lv + " IS " + str(fs._term)) in r: #if it's term is in the rule associated with the linguistic variable
                                fuzzy_set = rulebase.fuzzy_sets_dict[fs._term] #I retrieve the SARFuzzySet with the same term in the rule base
                                term = lv + " IS " + str(fs._term)
                                break #I stop immediately once I find it because I assume only one fs per variable in a rule

                        if (not term is None) and (not lv in adapted_lingVar):
                            # print("\tterm is ", str(term))
                            data_mean_value = float(dp[lv][0])  # todo aassuming they are always numerical
                            data_stdev_value = float(dp[lv][1])  # todo aassuming they are always numerical
                            data_max_value = float(dp[lv][2])
                            data_min_value = float(dp[lv][3])

                            # data_width = 2*data_stdev_value # width of interval [mu-stdev, mu+stdev] = (mu+stedv)-(mu-stdev) = 2stdev
                            data_width = data_stdev_value # we chose to aim at a with of the trapezoid large as 1 stdev
                            # print("\tdata mean value of "+str(lv)+" "+str(fuzzy_set.term)+": "+str(data_mean_value))
                            # print("\tdata stdev value of "+str(lv)+" "+str(fuzzy_set.term)+": "+str(data_stdev_value))

                            """ I want to first scale the universe and all variables, if necessary """
                            curr_uni = current_fuzzy_ling_var.ling_var._universe_of_discourse
                            new_universe = linearScaleUniverseToA1B1(current_fuzzy_ling_var.ling_var, data_min_value, data_max_value)
                            current_fuzzy_ling_var.universe_of_discourse = new_universe
                            for fs in partition:
                                new_mfs = fs.scaleLinear(curr_uni[0], curr_uni[1], data_min_value, data_max_value)
                                rulebase.updateMFParams(fs._term, new_mfs)

                            curr_mfs = fuzzy_set.getMF()  # fuzzy_set is a SARFuzzySet. getMF() returns its attribute "param", which is a dictionary of parameters (e.g., {"a": float}
                            curr_cl = float(curr_mfs["b"])
                            curr_cu = float(curr_mfs["c"])
                            curr_mid_value = (curr_cu + curr_cl) / 2.0  # todo assuming for now it is trapezoid
                            curr_width = (curr_cu - curr_cl)

                            # print("\tcurr cor pos of "+str(lv)+" "+str(fuzzy_set.term)+": "+str(curr_mid_value))
                            # print("\tcurr width of " + str(lv) + " " + str(fuzzy_set.term) + ": " + str(curr_width))
                            # print(curr_mfs)

                            #compute the error between the mid value in the fuzzy set and the value in the collected knowledge
                            error_core_position = curr_mid_value-data_mean_value
                            # print("\terror core pos:"+str(error_core_position))
                            #perform inference with the self.agent.FS to determine the change
                            self.agent.FS.set_variable(self.agent.error_name, error_core_position)
                            fs_output = self.agent.FS.Mamdani_inference()
                            change_core_position = float(fs_output[self.agent.change_name])
                            # print("\testimated change for core position:"+str(change_core_position))

                            # compute the error between the mid value in the fuzzy set and the value in the collected knowledge
                            error_core_width = curr_width - data_width
                            # print("\terror core width:" + str(error_core_width))
                            # perform inference with the self.agent.FS to determine the change
                            self.agent.FS.set_variable(self.agent.error_name, error_core_width)
                            fs_output = self.agent.FS.Mamdani_inference()
                            change_core_with = float(fs_output[self.agent.change_name])
                            # print("\testimated change for core position:" + str(change_core_with))


                            # once I computed the error and the consequent change for the particular fuzzy set,
                            # then I want to apply the changes to all sets in the partition

                            for fs in partition: #fs is a DynamicTrapezoidFuzzySet
                                # print(fs)
                                """ First applying core-position modifier """
                                c_mfs = fs.get_params() #c_mfs is actually a TUPLE of all parameters of the fuzzyset
                                # print("\tcurrent mfs:"+str(c_mfs))
                                new_mfs = fs.modifyCorePosition(change_core_position) #new_mfs should be a dictionary, and the function should DIRECTLY MODIFY THE MEMBERSHIP FUNCTION
                                # print("\tnew mfs:"+str(fs.get_params()))
                                # print(new_mfs)
                                rulebase.updateMFParams(fs._term, new_mfs) #this should create a new trapezoidfuzzyset and update it
                                """ Then applying core-width modifier """
                                c_mfs = fs.get_params()  # c_mfs is actually a TUPLE of all parameters of the fuzzyset
                                # print("\tcurrent mfs:" + str(c_mfs))
                                new_mfs = fs.modifyCoreWidth(
                                    change_core_with)  # new_mfs should be a dictionary, and the function should DIRECTLY MODIFY THE MEMBERSHIP FUNCTION
                                # print("\tnew mfs:" + str(fs.get_params()))
                                # print(new_mfs)
                                rulebase.updateMFParams(fs._term,
                                                        new_mfs)  # this should create a new trapezoidfuzzyset and update it
                            adapted_lingVar.append(str(lv))
            if len(adapted_lingVar)>0:
                new_fuzzy_system = rulebase.createFuzzySystem()
                rulebase.setFuzzySystem(new_fuzzy_system)
                fuzzy_social_system.updateRuleBase(rulebase)

        async def run(self):
            # print("I hould be running the behavior of norma adapt")
            # print("collected knowledge")
            # print(self.agent.collected_knowledge)
            # print(self.agent.adapting)
            """ Here, this is the actual procedure that will revise the norms.
            What it has to do is the following:
            1. check if the self.agent.collected_knowledge is not empty (i.e., if there is something useful to use for norm adaptation)
            2. for every data point collected, revise the membership functions of the rules.
            This needs to be done for every rule basein the system
            (i.e.,both for the social interpreter and for the social qualifiers etc.)
            """
            if (not self.agent.adapting): # and (len(self.agent.collected_knowledge)>self.agent.min_nr_datapoints_for_adaptation):
                # print("Adapting the rules in all fuzzy rule bases...")

                # print("collected knowledge")
                # print(self.agent.collected_knowledge)
                data = copy.deepcopy(self.agent.collected_knowledge)

                aggr_knowledge = {}
                for social_interpretation in Constants.SOCIAL_INTERPRETATIONS:
                    if len(self.agent.collected_knowledge_per_social_int[social_interpretation])>self.agent.min_nr_datapoints_for_adaptation:
                        # print("LEngth of collected knowledge for ", social_interpretation, ": ", str(len(self.agent.collected_knowledge_per_social_int[social_interpretation])))
                        # print(self.agent.collected_knowledge_per_social_int[social_interpretation])
                        for dp in self.agent.collected_knowledge_per_social_int[social_interpretation]:
                            # print("data point")
                            # print(dp)
                            social_int = dp[Constants.TOPIC_SOCIAL_INTERPR]
                            # print(social_int)
                            # print("aggr knowledge")
                            # print(aggr_knowledge)
                            if not social_int in aggr_knowledge.keys():
                                aggr_knowledge[social_int] = {} #dp should be a dictionary
                                for v in dp.keys():
                                    if not (v==Constants.TOPIC_SOCIAL_INTERPR):
                                        aggr_knowledge[social_int][v] = [float(dp[v])]
                                    else:
                                        aggr_knowledge[social_int][v] = dp[v]
                            else: #social int is already in aggr knowledge
                                for var in dp.keys():
                                    # print(var)
                                    if not (var==Constants.TOPIC_SOCIAL_INTERPR):
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
                        if not var == Constants.TOPIC_SOCIAL_INTERPR:
                            a = np.array([aggr_knowledge[social_int][var]])
                            avg = np.mean(a)
                            stdev = np.std(a)
                            data_max = np.max(a)
                            data_min = np.min(a)

                            if var in self.agent.variables_maxmin:
                                global_max = max(data_max, self.agent.variables_maxmin[var]["max"])
                                data_max = global_max
                                self.agent.variables_maxmin[var]["max"] = global_max
                                global_min = min(data_min, self.agent.variables_maxmin[var]["min"])
                                data_min = global_min
                                self.agent.variables_maxmin[var]["min"] = global_min
                            else:
                                self.agent.variables_maxmin[var] = {}
                                self.agent.variables_maxmin[var]["max"] = data_max
                                self.agent.variables_maxmin[var]["min"] = data_min

                            # print("Avg and Stdev of ", var, "for ", social_int, avg, stdev)
                            aggr_knowledge[social_int][var] = [avg, stdev, data_max, data_min]
                #now in averaged_knowledge I should have all collected knowledge but averaged per social interpretation
                # print("Averaged knoeldge")
                # print(averaged_knowledge)

                # for dp in self.agent.collected_knowledge:
                if len(aggr_knowledge)>0:
                    self.agent.adapting = True

                    # self.agent.fsi.fuzzyRuleBase.fs.produce_figure()

                    """
                    I first perform adaptation of the core position of the FuzzySets based on the averaged knowledge collected
                    """
                    # print("Adaptation of the core positions of the fuzzy sets...")
                    for social_int in aggr_knowledge.keys():
                        # print(social_int)
                        dp = aggr_knowledge[social_int]
                        # print("social interpreter")
                        self.adaptRuleBase(self.agent.fsi, dp)
                        for fsq in self.agent.fsq:
                            # print("social qualifier " + str(fsq))
                            self.adaptRuleBase(self.agent.fsq[fsq], dp)

                    # self.agent.fsi.fuzzyRuleBase.fs.produce_figure()
                    contextualize = True
                    if contextualize:
                        """ 
                        Then I adjust the core width and the support width via MOEA (I call this contextualization) in order to maximize interpretability
                        """
                        # print("Adaptation of the core and support of the fuzzy sets via MOEA")
                        # print("social interpreter")
                        self.agent.fsi.contextualize(data, self.agent.optim_param)
                        for fsq in self.agent.fsq:
                            # print("social qualifier " + str(fsq))
                            self.agent.fsq[fsq].contextualize(data, self.agent.optim_param)

                        # self.agent.fsi.fuzzyRuleBase.fs.produce_figure()

                    # print("Adaptation completed.")
                    self.agent.adapting = False

                    # self.agent.collected_knowledge = []
                    # print("Adaptation completed.")


    async def setup(self):
        await super().setup()
        # print("starting up norm adapter")
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
            change = self.terms[len(self.terms)-1-t_idx]
            rules.append("IF ("+self.error_name+" IS "+error+") THEN ("+self.change_name+" IS "+change+")")
        self.FS.add_rules(rules)

        self.collected_knowledge = []
        self.collected_knowledge_per_social_int = {}
        self.variables_maxmin = {}
        for social_inter in Constants.SOCIAL_INTERPRETATIONS:
            self.collected_knowledge_per_social_int[social_inter] = []

        self.min_nr_datapoints_for_adaptation = 5
        self.optim_param = {
            "algo": Constants.GA,
            "pop_size": 5,
            "n_gen": 10,
            "scale": False,
            "core-pos": False,
            "core-width": False,
            "support-width": True,
            "gp": False,
            "n_obj_f": 1
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

    def collectDataPointFromMessage(self, message):
        work_info_list = utils.splitStringToList(message)
        nr_pairs = int(len(work_info_list) / 2)  # n.b. it is expected to be always even
        data_point = {}
        done = 0
        for i in range(nr_pairs):
            topic = work_info_list[done + i]
            value = work_info_list[done + i + 1]

            if not topic == Constants.TOPIC_SOCIAL_INTERPR:
                value = float(value)

            data_point[topic] = value
            done = done + 1
        self.collected_knowledge.append(data_point)

        social_int = data_point[Constants.TOPIC_SOCIAL_INTERPR]
        self.collected_knowledge_per_social_int[social_int].append(data_point)


    async def do_work(self, work_info):
        print("!!!!!!!!!!!!!!!!!!!!! TO MAKE SURE THAT THE DICTIONARY WORK_INFO IS READ PROPERLY !!!!!!!!!!!!!!!!!!!!!!!")
        """ work_info is the message from the data collector with all the info
        it is a string which represents a list, where element 0 is the topic of element 1, and element 2 is the topic of element 2, etc."""
        print("received message from data collector")
        print(work_info)
        self.collectDataPointFromMessage(work_info)





