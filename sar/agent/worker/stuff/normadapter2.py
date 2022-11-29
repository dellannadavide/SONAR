import copy

from spade.behaviour import PeriodicBehaviour, OneShotBehaviour

from sar.agent.workeragent import WorkerAgent
from simpful import *

from utils import utils
import utils.constants as Constants

from datetime import timedelta, datetime



class NormAdapter2(WorkerAgent):

    class PerformAdaptation(OneShotBehaviour):
        def __init__(self, data, averaged_knowledge):
            super().__init__()
            self.data = data
            self.averaged_knowledge = averaged_knowledge

        def adaptRuleBase(self, fuzzy_social_system, dp):

            rulebase = copy.deepcopy(fuzzy_social_system.getRuleBase())
            social_int = dp[Constants.TOPIC_SOCIAL_INTERPR]
            lvs = rulebase.getLVSFromRulesContainingHighValuesOf(social_int) #returns a dictionary rule: list of linguistic variables (strings) in rule
            print("\tData point is: ", str(dp))
            print("\tSocial interpretation is "+str(social_int))
            print("\tRules (and associated ling. var) containing '", str(social_int), "IS high' are ", str(lvs))

            adapted_lingVar = []
            for r in lvs.keys(): #for all rules
                for lv in lvs[r]: #for each linguistic variable (string) in the dictionary
                    if (str(lv).strip() in Constants.DYNAMIC_LV) and (not lv == social_int) and (str(lv) in dp):
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
                            print("\tterm is ", str(term))
                            curr_mfs = fuzzy_set.getMF() #fuzzy_set is a SARFuzzySet. getMF() returns its attribute "param", which is a dictionary of parameters (e.g., {"a": float}
                            curr_cl = float(curr_mfs["b"])
                            curr_cu = float(curr_mfs["c"])
                            curr_mid_value = (curr_cu + curr_cl)/2.0 #todo assuming for now it is trapezoid
                            data_value = float(dp[lv]) #todo aassuming they are always numerical

                            print("\tdata value of "+str(lv)+" "+str(fuzzy_set.term)+": "+str(data_value))
                            print("\tcurr value of "+str(lv)+" "+str(fuzzy_set.term)+": "+str(curr_mid_value))
                            print(curr_mfs)

                            #compute the error between the mid value in the fuzzy set and the value in the collected knowledge
                            error = curr_mid_value-data_value
                            print("\terror:"+str(error))
                            #perform inference with the self.agent.FS to determine the change
                            self.agent.FS.set_variable(self.agent.error_name, error)
                            fs_output = self.agent.FS.Mamdani_inference()
                            change = float(fs_output[self.agent.change_name])
                            print("\testimated change:"+str(change))


                            # once I computed the error and the consequent change for the particular fuzzy set,
                            # then I want to apply the changes to all sets in the partition

                            for fs in partition: #fs is a DynamicTrapezoidFuzzySet
                                print(fs)
                                c_mfs = fs.get_params() #c_mfs is actually a TUPLE of all parameters of the fuzzyset
                                print("\tcurrent mfs:"+str(c_mfs))
                                new_mfs = fs.modifyCorePosition(change) #new_mfs should be a dictionary, and the function should DIRECTLY MODIFY THE MEMBERSHIP FUNCTION
                                print("\tnew mfs:"+str(fs.get_params()))
                                print(new_mfs)
                                rulebase.updateMFParams(fs._term, new_mfs) #this should create a new trapezoidfuzzyset and update it
                            adapted_lingVar.append(str(lv))
            if len(adapted_lingVar)>0:
                new_fuzzy_system = rulebase.createFuzzySystem()
                rulebase.setFuzzySystem(new_fuzzy_system)
                fuzzy_social_system.updateRuleBase(rulebase)

        async def run(self):
            self.agent.adapting = True

            # self.agent.fsi.fuzzyRuleBase.fs.produce_figure()

            """
            I first perform adaptation of the core position of the FuzzySets based on the averaged knowledge collected
            """
            print("Adaptation of the core positions of the fuzzy sets...")
            for social_int in self.averaged_knowledge.keys():
                print(social_int)
                dp = self.averaged_knowledge[social_int]
                print("social interpreter")
                self.adaptRuleBase(self.agent.fsi, dp)
                for fsq in self.agent.fsq:
                    print("social qualifier "+str(fsq))
                    self.adaptRuleBase(self.agent.fsq[fsq], dp)

            # self.agent.fsi.fuzzyRuleBase.fs.produce_figure()
            contextualize = False
            if contextualize:
                """ 
                Then I adjust the core width and the support width via MOEA (I call this contextualization) in order to maximize interpretability
                """
                print("Adaptation of the core and support of the fuzzy sets via MOEA")
                print("social interpreter")
                self.agent.fsi.contextualize(self.data, self.agent.optim_param)
                for fsq in self.agent.fsq:
                    print("social qualifier "+str(fsq))
                    self.agent.fsq[fsq].contextualize(self.data, self.agent.optim_param)

                # self.agent.fsi.fuzzyRuleBase.fs.produce_figure()

            print("Adaptation completed.")
            self.agent.adapting = False



    class AdaptNorms(PeriodicBehaviour):
        def __init__(self, period, start_at):
            super().__init__(period, start_at)
            self.timeout_data_source = period
            print("this is the behavior to startr")

        async def run(self):
            print("I hould be running the behavior of norma adapt")
            print("collected knowledge")
            print(self.agent.collected_knowledge)
            print(self.agent.adapting)
            """ Here, this is the actual procedure that will revise the norms.
            What it has to do is the following:
            1. check if the self.agent.collected_knowledge is not empty (i.e., if there is something useful to use for norm adaptation)
            2. for every data point collected, revise the membership functions of the rules.
            This needs to be done for every rule basein the system
            (i.e.,both for the social interpreter and for the social qualifiers etc.)
            """
            if (not self.agent.adapting) and (len(self.agent.collected_knowledge)>self.agent.min_nr_datapoints_for_adaptation):
                print("Adapting the rules in all fuzzy rule bases...")

                print("collected knowledge")
                print(self.agent.collected_knowledge)
                data = copy.deepcopy(self.agent.collected_knowledge)

                averaged_knowledge = {}
                nr_datapoints = {}
                for dp in self.agent.collected_knowledge:
                    social_int = dp[Constants.TOPIC_SOCIAL_INTERPR]
                    if not social_int in averaged_knowledge:
                        averaged_knowledge[social_int] = dp.copy() #dp should be a dictionary
                        for v in averaged_knowledge[social_int]:
                            if not (v==Constants.TOPIC_SOCIAL_INTERPR):
                                averaged_knowledge[social_int][v] = float(averaged_knowledge[social_int][v])
                        nr_datapoints[social_int] = 1
                    else:
                        for var in dp:
                            if not (var==Constants.TOPIC_SOCIAL_INTERPR):
                                if var in averaged_knowledge[social_int]:
                                    averaged_knowledge[social_int][var] = averaged_knowledge[social_int][var]+float(dp[var])
                                else:
                                    averaged_knowledge[social_int][var] = float(dp[var])
                        nr_datapoints[social_int] = nr_datapoints[social_int]+1

                for social_int in averaged_knowledge:
                    for var in averaged_knowledge[social_int]:
                        if not var == Constants.TOPIC_SOCIAL_INTERPR:
                            averaged_knowledge[social_int][var] = averaged_knowledge[social_int][var]/nr_datapoints[social_int]
                #now in averaged_knowledge I should have all collected knowledge but averaged per social interpretation
                # print("Averaged knoeldge")
                # print(averaged_knowledge)

                # for dp in self.agent.collected_knowledge:
                b = self.agent.PerformAdaptation(data, averaged_knowledge)
                self.agent.add_behaviour(b)

                self.agent.collected_knowledge = []
                # print("Adaptation completed.")





    async def setup(self):
        await super().setup()
        print("starting up norm adapter")
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
        self.min_nr_datapoints_for_adaptation = 5
        self.optim_param = {
            "algo": Constants.NSGA3,
            "pop_size": 10,
            "n_gen": 3,
            "scale": False,
            "core-pos": False,
            "core-width": True,
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

        print("setting up the behavior to startr")
        start_at = datetime.now() + timedelta(seconds=5)
        b = self.AdaptNorms(period=6, start_at=start_at)
        self.add_behaviour(b)


    async def do_work(self, work_info):
        print("!!!!!!!!!!!!!!!!!!!!! TO MAKE SURE THAT THE DICTIONARY WORK_INFO IS READ PROPERLY !!!!!!!!!!!!!!!!!!!!!!!")
        """ work_info is the message from the data collector with all the info
        it is a string which represents a list, where element 0 is the topic of element 1, and element 2 is the topic of element 2, etc."""
        print("received message from data collector")
        print(work_info)
        work_info_list = utils.splitStringToList(work_info)
        nr_pairs = int(len(work_info_list)/2) #n.b. it is expected to be always even
        data_point = {}
        done = 0
        for i in range(nr_pairs):
            topic = work_info_list[done+i]
            value = work_info_list[done+i+1]

            if not topic==Constants.TOPIC_SOCIAL_INTERPR:
                value = float(value)

            data_point[topic] = value
            done = done+1

        self.collected_knowledge.append(data_point)




