import copy
import threading
import traceback
import random

import utils.constants as Constants
from mas.utils.fsutils import SARFuzzyRuleBase

import logging
logger = logging.getLogger("sonar.mas.norm.fuzzysocialinterpreter")

class FuzzySocialInterpreter:
    """ The Fuzzy Social Interpreter is a fuzzy inference system.
    Every worker agent can create an internal instance of a fuzzy social interpreted for its own task-specifics,
    however at the moment only one fuzzy social interpreter is created and shared by all agents in the MAS """
    def __init__(self, fuzzy_sets_file, ling_var_file, rules_file, min_certainty) -> None:
        super().__init__()
        self.fuzzy_sets_file = fuzzy_sets_file
        self.ling_var_file = ling_var_file
        self.rules_file = rules_file
        self.fuzzyRuleBase = SARFuzzyRuleBase(self.fuzzy_sets_file, self.ling_var_file, self.rules_file, "social_interpreter")
        self.min_certainty = min_certainty

        #self.DIAMONDS = ['DUTY', 'INTELLECT', 'ADVERSITY', 'MATING', 'POSITIVITY', 'NEGATIVITY', 'DECEPTION', 'SOCIALITY']
        self.lock = threading.Lock()

    def getSocialInterpretationValues(self, inputs):
        fs_output = None
        self.lock.acquire()
        try:
            for i in inputs:
                if i in self.fuzzyRuleBase.inputs:
                    # print("----------setting variable "+str(i)+" to "+str(inputs[i]))
                    self.fuzzyRuleBase.fs.set_variable(i, inputs[i]) #todo somewhere mapping should be written
            # print("----------performing mamdani inference in the zsocial interpreter")
            # print(self.fuzzyRuleBase.fs._rules)
            fs_output = self.fuzzyRuleBase.fs.Mamdani_inference(verbose=False)
            # print(fs_output)
            # print("----------end of inference")
        except Exception:
            logger.exception(traceback.format_exc())
            pass
        self.lock.release()
        return fs_output


    def getBestSocialInterpretation(self, inputs):
        fs_output = self.getSocialInterpretationValues(inputs)
        if not fs_output is None:
            best_interpr = max(fs_output, key=fs_output.get)
            # print("Inputs: "+str(inputs))
            # print(best_interpr)
            """ Communicating the social interpretation back"""
            if fs_output[best_interpr] > self.min_certainty:
                # I want to retrieve all interpr that have same certainty as the max and randomly select among them (otherwise we select always the first)
                all_best_int = []
                for interpr in fs_output.keys():
                    if fs_output[interpr] == fs_output[best_interpr]:
                        all_best_int.append(interpr)
                best_interpr = random.choice(all_best_int)
                return fs_output, best_interpr
            else:
                return fs_output, "UNKNOWN"
        else:
            logger.log(Constants.LOGGING_LV_DEBUG_SONAR, "The inputs "+str(inputs)+" are currently not supported")
            best_social_interpr = "UNKNOWN"
            social_values = {}
            for o in self.fuzzyRuleBase.outputs:
                social_values[o] = 0.0
            return social_values, best_social_interpr

    def getRuleBase(self):
        return self.fuzzyRuleBase

    def updateRuleBase(self, newRuleBase):
        self.lock.acquire()
        self.fuzzyRuleBase = newRuleBase
        self.lock.release()

    def updateRuleBaseFS(self, newFS):
        rulebase = copy.deepcopy(self.getRuleBase())
        for lv in newFS._lvs:
            v = newFS._lvs[lv]
            lv_universe = v._universe_of_discourse
            for fs in v._FSlist:
                try:
                    a, b, c, d, k_GP, theta = fs.get_params()
                    a = max(lv_universe[0], min(a, lv_universe[1]))
                    b = max(lv_universe[0], min(b, lv_universe[1]))
                    c = max(lv_universe[0], min(c, lv_universe[1]))
                    d = max(lv_universe[0], min(d, lv_universe[1]))
                    new_fs_param = {"a": a,
                                    "b": b,
                                    "c": c,
                                    "d": d,
                                    "k_GP": k_GP,
                                    "theta": theta}
                    rulebase.updateMFParams(fs._term, new_fs_param)
                except:
                    pass

        new_fuzzy_system = rulebase.createFuzzySystem()
        rulebase.setFuzzySystem(new_fuzzy_system)
        self.updateRuleBase(rulebase)

    def contextualize(self, dataset, optim_param):
        # print("======= current fs ======")
        # print(self.fuzzyRuleBase.fs)
        # for lv in self.fuzzyRuleBase.fs._lvs:
        #     v = self.fuzzyRuleBase.fs._lvs[lv]
        #     print(v._concept)
        #     for fs in v._FSlist:
        #         try:
        #             print(fs.get_params())
        #         except:
        #             pass
        contextualized_FS = self.fuzzyRuleBase.getContextualizedFS(dataset, optim_param) #returns a simpful fs

        # print("======= contextualized fs ======")
        # print(contextualized_FS)
        # for lv in contextualized_FS._lvs:
        #     v = contextualized_FS._lvs[lv]
        #     print(v._concept)
        #     for fs in v._FSlist:
        #         try:
        #             print(fs.get_params())
        #         except:
        #             pass
        self.updateRuleBaseFS(contextualized_FS)