import copy

from spade.behaviour import PeriodicBehaviour

from sar.agent.workeragent import WorkerAgent
from simpful import *

from utils import utils
import utils.constants as Constants

from datetime import timedelta, datetime



class NormAdapter(WorkerAgent):

    class AdaptNorms(PeriodicBehaviour):
        def __init__(self, period, start_at):
            super().__init__(period, start_at)
            self.timeout_data_source = period

        async def run(self):
            """ Here, this is the actual procedure that will revise the norms.
            What it has to do is the following:
            1. check if the self.agent.collected_knowledge is not empty (i.e., if there is something useful to use for norm adaptation)
            2. for every data point collected, revise the membership functions of the rules.
            This needs to be done for every rule basein the system
            (i.e.,both for the social interpreter and for the social qualifiers etc.)
            """
            if len(self.agent.collected_knowledge)>self.agent.min_nr_datapoints_for_adaptation:
                print("Adapting the rules in all fuzzy rule bases...")

                print("collected knowledge")
                print(self.agent.collected_knowledge)

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
                for social_int in averaged_knowledge:
                    dp = averaged_knowledge[social_int]
                    #first the fsi
                    # print("Adapting the rules in the fuzzy social interpreter...")
                    self.adaptRuleBase(self.agent.fsi, dp)
                    #then all the fsq
                    # print("Adapting the rules in the fuzzy social qualifiers...")
                    for fsq in self.agent.fsq:
                        # print("... another social qualifier...{}".format(fsq))
                        self.adaptRuleBase(self.agent.fsq[fsq], dp)
                self.agent.collected_knowledge = []
                print("Adaptation completed.")

        def adaptRuleBase(self, fuzzy_system, dp):
            """
            TODO: QUESTION: SHOULD WE MODIFY ALL FUZZY SETS RELATED TO A VARIABLE OR ONLY THE ONE THAT IS DIRECTLY AFFECTED?
            FOR EXAMPLE IF WE WANT TO SHIFT RIGHT THE MEDIUM_DISTANCE VARIABLE (BECUASE TOO LOW)
            SHOULD WE SHIFT RIGHT ALSO THE HIGH_DISTANCE AND THE LOW DISTANCE?
            OR MAYBE SHOULD WE JUST CHANGE THE MINIMUM VALUE OF THE HIGH_DIST AND THE MAX VALUE OF THE LOW DIST SO THAT WE DO NOT HAVE GAPS?
            MAYBE WE CAN EXPERIMENT WITH THIS?

            """
            rulebase = fuzzy_system.getRuleBase()  # this is inside the loop so that iteratively it can be modified
            # determine the social intepretation in the data point (e.g, SOCIALITY)
            social_int = dp[Constants.TOPIC_SOCIAL_INTERPR]
            # - determine all ling val in all the rules s.t. they relate to the social interpretation (i.e., the ling var contained in the rules that refer to social_int IS high, e.g., SOCIALITY IS high)
            lvs = rulebase.getLVSFromRulesContainingHighValuesOf(social_int)

            print("\tData point is: ", str(dp))
            # print("\tSocial interpretation is "+str(social_int))
            # print("\tRules (and associated ling. var) containing '", str(social_int), "IS high' are ", str(lvs))
            adapted = []
            for r in lvs: #for all rules
                for lv in lvs[r]: #for each linguistic variable
                    if (not lv == social_int) and (str(lv) in dp) and (not (str(lv).strip() in Constants.STATIC_LV)):
                        current_fuzzy_ling_var = rulebase.ling_vars_dict[lv] #retrieve the fuzzy linguistic variable (e.g., DIST)
                        fuzzy_sets = current_fuzzy_ling_var.fuzzy_sets
                        fuzzy_set = None #retrieve the fuzzy_set (e.g., mid_dist if the rule contains mid_dist)
                        term = None
                        for fs in fuzzy_sets:
                            if (lv+" IS "+str(fs._term)) in r:
                                fuzzy_set = rulebase.fuzzy_sets_dict[fs._term]
                                term = lv+" IS "+str(fs._term)
                                break
                        if (not term is None) and (not str(term) in adapted): #only once because I go directly to modify the membership functions, which will then apply to all variables
                            print("\tterm is ", str(term))
                            curr_mfs = fuzzy_set.getMF()
                            curr_mid_value = float(curr_mfs["b"]) #todo assuming for now it is triangular with 3 values a b c
                            data_value = float(dp[lv]) #todo aassuming they are always numerical

                            # print("\tcurrent mid value of "+str(lv)+" "+str(fuzzy_set.term)+": "+str(curr_mid_value))
                            print("\tdata value of "+str(lv)+" "+str(fuzzy_set.term)+": "+str(data_value))

                            #compute the error between the mid value in the fuzzy set and the value in the collected knowledge
                            error = curr_mid_value-data_value
                            # print("\terror:"+str(error))
                            #perform inference with the self.agent.FS to determine the change
                            self.agent.FS.set_variable(self.agent.error_name, error)
                            fs_output = self.agent.FS.Mamdani_inference()
                            change = float(fs_output[self.agent.change_name])
                            # print("\testimated change:"+str(change))

                            #apply the change (i.e., modify the parameters of the fuzzy sets, and update the fuzzy sets in the actual rule base)
                            #modify the param of the fuzzy sets
                            new_mfs = {}
                            for mf in curr_mfs:
                                new_mfs[mf] = curr_mfs[mf]+change
                            print("\tcurrent mfs:"+str(curr_mfs))
                            print("\tnew mfs:"+str(new_mfs))
                            #update the fuzzy sets in the actual rule base
                            # print("\tmaking a deep copy of the rulebase")
                            new_rule_base = copy.deepcopy(rulebase)
                            # print("\tupdating the mfs in the new rule base")
                            new_rule_base.updateMFs(fuzzy_set.term, new_mfs)
                            # print("\tupdating the reference to the rule base")
                            fuzzy_system.updateRuleBase(new_rule_base)

                            adapted.append(str(term))

    async def setup(self):
        await super().setup()
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

        start_at = datetime.now() + timedelta(seconds=5)
        b = self.AdaptNorms(period=6, start_at=start_at)
        self.add_behaviour(b)


    async def do_work(self, work_info):
        """ work_info is the message from the data collector with all the info
        it is a string which represents a list, where element 0 is the topic of element 1, and element 2 is the topic of element 2, etc."""
        work_info_list = utils.splitStringToList(work_info)
        nr_pairs = int(len(work_info_list)/2) #n.b. it is expected to be always even
        data_point = {}
        done = 0
        for i in range(nr_pairs):
            topic = work_info_list[done+i]
            value = work_info_list[done+i+1]

            if topic==Constants.TOPIC_DISTANCE:
                value = float(value)

            data_point[topic] = value
            done = done+1

        self.collected_knowledge.append(data_point)




