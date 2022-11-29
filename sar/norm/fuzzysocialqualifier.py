import copy
import threading
import traceback

import utils.constants as Constants
from sar.utils.fsutils import SARFuzzyRuleBase

import logging
logger = logging.getLogger("nosar.sar.norm.fuzzysocialqualifier")

class FuzzySocialQualifier:
        def __init__(self, aspect, fuzzy_sets_file, ling_var_file, rules_file) -> None:
            super().__init__()
            self.aspect = aspect
            self.fuzzy_sets_file = fuzzy_sets_file
            self.ling_var_file = ling_var_file
            self.rules_file = rules_file
            self.fuzzyRuleBase = SARFuzzyRuleBase(self.fuzzy_sets_file, self.ling_var_file, self.rules_file, self.aspect)

            self.lock = threading.Lock()

        def getSocialQualification(self, input):
            fs_output = None
            self.lock.acquire()
            try:
                for i in self.fuzzyRuleBase.inputs:
                    if i in input.keys():
                        # try:
                        self.fuzzyRuleBase.fs.set_variable(i, input[i])
                            # print("Set val "+str(input[i])+" to var "+str(i))
                        # except:
                        #     logger.info("Variable "+str(i)+" not in the fuzzyRuleBase, skipping.")
                    else:
                        self.fuzzyRuleBase.fs.set_variable(i, self.fuzzyRuleBase.ling_vars_dict[i].getDefaultVal())
                fs_output = self.fuzzyRuleBase.fs.Mamdani_inference(verbose=False)
                # output_val = max(fs_output, key=fs_output.get)
            except Exception:
                logger.exception(traceback.format_exc())
                pass
            self.lock.release()
            return fs_output

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
            contextualized_FS = self.fuzzyRuleBase.getContextualizedFS(dataset, optim_param)
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