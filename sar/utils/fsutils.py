import copy

import simpful as sf
from simpful import *
import utils.constants as Constants
import pandas as pd

from sar.utils.moea import getContextualizedFS


def scaleFrom01ToAB(x, a, b, lambd, k_SF):
    if x <= lambd:
        return (a + ((b - a) * ((lambd ** (1 - k_SF)) * (x ** k_SF))))
    else:
        return (a + ((b - a) * (1 - (((1 - lambd) ** (1 - k_SF)) * ((1 - x ** (k_SF)))))))

def linearScaleFromABToA1B1(x, a, b, a1, b1):
    xin01 = (x-a)/(b-a)
    xinA1B1 = a1+((b1-a1)*xin01)
    return xinA1B1

def scaleUniverse(sf_ling_var, a, b, lambd, k_SF): #sf_ling_var is a simpful linguistic var (not a SARFuzzyLingVar)
    sf_ling_var._universe_of_discourse = [scaleFrom01ToAB(sf_ling_var._universe_of_discourse[0], a, b, lambd, k_SF),
                                                         scaleFrom01ToAB(sf_ling_var._universe_of_discourse[1], a, b, lambd, k_SF)]

def linearScaleUniverseToA1B1(sf_ling_var, a1, b1): #sf_ling_var is a simpful linguistic var (not a SARFuzzyLingVar)
    sf_ling_var._universe_of_discourse = [linearScaleFromABToA1B1(sf_ling_var._universe_of_discourse[0], sf_ling_var._universe_of_discourse[0], sf_ling_var._universe_of_discourse[1], a1, b1),
                                          linearScaleFromABToA1B1(sf_ling_var._universe_of_discourse[1], sf_ling_var._universe_of_discourse[0], sf_ling_var._universe_of_discourse[1], a1, b1)]
    return sf_ling_var._universe_of_discourse


class SARFuzzyLingVar:
    def __init__(self, name, concept, universe_of_discourse, fuzzy_sets, fuzzy_sets_names) -> None:
        super().__init__()
        self.name = name
        self.concept = concept
        self.universe_of_discourse = universe_of_discourse
        self.fuzzy_sets = fuzzy_sets
        self.fuzzy_sets_names = fuzzy_sets_names
        self.ling_var = self.createSimpfulLingVar()

    def getName(self):
        return self.name

    def getVar(self):
        return self.ling_var

    def updateFuzzySets(self, new_fuzzy_sets):
        self.fuzzy_sets = new_fuzzy_sets
        self.ling_var = self.createSimpfulLingVar()

    def createSimpfulLingVar(self):
        return sf.LinguisticVariable(self.fuzzy_sets, concept=self.concept,
                                     universe_of_discourse=self.universe_of_discourse)


class SARFuzzySet:
    def __init__(self, term: str, type: str, param: dict):
        super().__init__()
        # print("---- creating a new SARFUZZYSET with ")
        # print(term)
        # print(type)
        # print(param)

        self.term = term
        self.type = type
        self.param = param
        self.fuzzy_set = self.createSimpfulFuzzySet()



    def createSimpfulFuzzySet(self):
        if self.type == Constants.FS_TRIANGULAR_MF:
            if (not "a" in self.param) or (not "b" in self.param) or (not "c" in self.param):
                print("dict 'param' must specify param a,b and c for defining a triangular mf")
                return None
            else:
                return sf.FuzzySet(function=Triangular_MF(a=self.param["a"], b=self.param["b"], c=self.param["c"]),
                                   term=self.term)
        elif self.type == Constants.FS_TRAPEZOIDAL_MF:
            if (not "a" in self.param) or (not "b" in self.param) or (not "c" in self.param) or (not "d" in self.param):
                print("dict 'param' must specify param a,b,c,d for defining a trapezoidal mf")
                return None
            else:
                return DynamicTrapezoidFuzzySet(function=DynamicTrapezoidal_MF(a=self.param["a"], b=self.param["b"], c=self.param["c"], d=self.param["d"]),
                                   term=self.term)
        elif self.type == Constants.FS_GAUSSIAN_MF:
            if (not "a" in self.param) or (not "b" in self.param):
                print("dict 'param' must specify param a,b for defining a gaussian mf")
                return None
            else:
                return sf.GaussianFuzzySet(mu=self.param["a"], sigma=self.param["b"], term=self.term)
        else:
            print("Type of MF (" + self.type + ") not supported yet")
            return None

    def getMF(self):
        return self.param

    def updateMF(self, new_param):
        if self.type == Constants.FS_TRIANGULAR_MF:
            if (not "a" in new_param) or (not "b" in new_param) or (not "c" in new_param):
                print("the dictionary with the parameters must specify param a,b and c for defining a triangular mf")
            else:
                self.param = new_param
                self.fuzzy_set = self.createSimpfulFuzzySet()
        elif self.type == Constants.FS_TRAPEZOIDAL_MF:
            if (not "a" in new_param) or (not "b" in new_param) or (not "c" in new_param) or (not "d" in new_param):
                print("the dictionary with the parameters must specify param a,b and c for defining a triangular mf")
            else:
                self.param = new_param
                self.fuzzy_set = self.createSimpfulFuzzySet()
        elif self.type == Constants.FS_GAUSSIAN_MF:
            if (not "a" in new_param) or (not "b" in new_param):
                print("dict 'param' must specify param a,b for defining a gaussian mf")
                return None
            else:
                self.param = new_param
                self.fuzzy_set = self.createSimpfulFuzzySet()
        else:
            print("Type of MF (" + self.type + ") not supported yet")


class SARFuzzyRuleBase:
    """
    A Norm Base is actually a fuzzy system
    """
    def __init__(self, fuzzy_sets_file, ling_var_file, rules_file, aspect) -> None:
        super().__init__()
        self.aspect = aspect
        self.rules = self.extractRulesFromFile(rules_file)
        self.fuzzy_sets_dict = self.extractFuzzySetsFromFile(fuzzy_sets_file)
        self.ling_vars_dict = self.extractLingVarFromFile(ling_var_file, self.fuzzy_sets_dict, self.rules)

        # print(self.fuzzy_sets_dict)
        # print(self.ling_vars_dict)
        # print(self.rules)


        self.fs = self.createFuzzySystem()



        # print(aspect)
        self.inputs, self.outputs = self.getInputOutputVariables(self.rules, self.ling_vars_dict)
        self.dynamic_ling_var = []
        for v in self.inputs:
            if v in Constants.DYNAMIC_LV:
                self.dynamic_ling_var.append(v)
        for v in self.outputs:
            if v in Constants.DYNAMIC_LV:
                self.dynamic_ling_var.append(v)

        # print("In creating a fuzzy rule base with inputs and outputs")
        # print(self.inputs)
        # print(self.outputs)
        # print("I identify the following dynamic variables, which will be affected by autonomous adaptation")
        # print(self.dynamic_ling_var)

        # self.base_fs = copy.deepcopy(self.fs)

    def addNewRules(self, rules):
        self.rules.append(rules)
        self.fs.add_rules(rules)

    def updateMFParams(self, fuzzy_set_id, new_mfs):
        fuzzy_set = self.fuzzy_sets_dict[fuzzy_set_id]
        fuzzy_set.updateMF(new_mfs)


    def updateFuzzySet(self, ling_var_id, fuzzy_set_id, new_fuzzyset):
        self.fuzzy_sets_dict[fuzzy_set_id] = new_fuzzyset
        self.ling_vars_dict[ling_var_id].updateFuzzySets(self.fuzzy_sets_dict[fuzzy_set_id])

    def getMF(self, fuzzy_set_id):
        return self.fuzzy_sets_dict[fuzzy_set_id]

    def setFuzzySystem(self, new_fs):
        self.fs = new_fs

    def getLVSFromRulesContainingHighValuesOf(self, variable):
        lvs = {}
        high_values_of_var = [str(variable)+" IS "+str(x) for x in Constants.FS_POSITIVE_INTERPRETATION_VALUES]
        for r in self.rules:
            for hv in high_values_of_var:
                if hv in r:
                    lvs[r] = [i for i in self.fs._lvs if (i in r)]
        return lvs

    # def updateLingVars(self):
    #     ling_vars = {}
    #     for ling_var in self.ling_vars_dict.keys():
    #         ling_vars[ling_var] = SARFuzzyLingVar(ling_var,
    #                                         self.ling_vars_dict[ling_var].concept,
    #                                         self.ling_vars_dict[ling_var].concept,
    #                                         fss,
    #                                         fss_ids)
    #
    #     return ling_vars

    def createFuzzySystem(self):
        fuzzy_system = sf.FuzzySystem(verbose=False)
        for lv_id in self.ling_vars_dict:
            partition = []
            for fuzzy_set_id in self.ling_vars_dict[lv_id].fuzzy_sets_names:
                partition.append(self.fuzzy_sets_dict[fuzzy_set_id].fuzzy_set)
            self.ling_vars_dict[lv_id] = SARFuzzyLingVar(lv_id,
                                               self.ling_vars_dict[lv_id].concept,
                                               self.ling_vars_dict[lv_id].universe_of_discourse,
                                               partition,
                                               self.ling_vars_dict[lv_id].fuzzy_sets_names)
            fuzzy_system.add_linguistic_variable(lv_id, self.ling_vars_dict[lv_id].getVar(), verbose=False)

        fuzzy_system.add_rules(self.rules, verbose=False)
        return fuzzy_system


    def extractRulesFromFile(self, rules_file):
        rules = []
        rules_df = pd.read_excel(rules_file, engine='openpyxl')
        for index, row in rules_df.iterrows():
            if str(row['FS'])==self.aspect:
                rule = str(row['Rule'])
                rules.append(rule)
        return rules

    def extractLingVarFromFile(self, ling_var_file, fuzzy_sets, rules):
        ling_vars = {}
        ling_vars_df = pd.read_excel(ling_var_file, engine='openpyxl')
        for index, row in ling_vars_df.iterrows():
            lv_id = str(row['Name'])
            if self.isLVinRules(lv_id, rules):
                fss_ids = str(row['FuzzySets']).split(sep="%%")
                fss = []
                for fs in fss_ids:
                    fss.append(fuzzy_sets[fs].fuzzy_set)
                ling_vars[lv_id] = SARFuzzyLingVar(lv_id,
                                                str(row['Concept']),
                                                [float(row['Min']), float(row['Max'])],
                                                fss,
                                                fss_ids)
        return ling_vars

    def isLVinRules(self, lv, rules):
        for r in rules:
            if lv in r:
                return True
        return False

    def extractFuzzySetsFromFile(self, fuzzy_sets_file):
        fuzzy_sets = {}
        fuzzy_sets_df = pd.read_excel(fuzzy_sets_file, engine='openpyxl')
        for index, row in fuzzy_sets_df.iterrows():
            fs_id = str(row['Term'])
            fuzzy_sets[fs_id] = SARFuzzySet(fs_id, str(row['Type']),
                                         {"a": float(row['a']),
                                               "b": float(row['b']),
                                               "c": float(row['c']),
                                                "d": float(row['d'])
                                              })
        return fuzzy_sets

    def getInputOutputVariables(self, rules, ling_vars_dict):
        # print("Extracting Input and Output variables from rules")
        inputs = set()
        outputs = set()
        for rule in rules:
            # print("rule: "+str(rule))
            parsed_antecedent = str(recursive_parse(preparse(rule), verbose=False, operators=self.fs._operators))
            parsed_consequent = str(postparse(rule, verbose=False))
            # print(parsed_antecedent)
            # print(parsed_consequent)
            for ling_var in ling_vars_dict.keys():
                # print(ling_var)
                if ling_var in parsed_antecedent:
                    # print("-> is in input")
                    inputs.add(ling_var)
                if ling_var in parsed_consequent:
                    # print("-> is in output")
                    outputs.add(ling_var)
        return inputs,outputs


    def getContextualizedFS(self, dataset, optim_param):
        # i first extract from the dataset the info relevant for the particular fs and prepare them for being used
        fs_specific_dataset = []

        for dp in dataset:
            try:
                datapoint = {}
                datapoint["inputs"] = {}
                datapoint["outputs"] = {}
                for input_var in self.inputs:
                    datapoint["inputs"][input_var] = dp[input_var]
                for output_var in self.outputs:
                    datapoint["outputs"][output_var] = dp[output_var]
                fs_specific_dataset.append(datapoint)
            except:
                print("Skipping data point with no sufficient data for adapting the current FS.")
                print(dp)
                print("Required inputs and outputs")
                print(self.inputs)
                print(self.outputs)

        if (len(fs_specific_dataset)>0) and (len(self.dynamic_ling_var)>0):
            # print("get the contextualized fs based on data", str(fs_specific_dataset))
            return getContextualizedFS(self.fs, self.dynamic_ling_var, fs_specific_dataset, optim_param=optim_param)
        return self.fs




class DynamicTrapezoidal_MF(sf.Trapezoidal_MF):
    def __init__(self, a=0, b=0.25, c=0.75, d=1, k_GP=None, theta=None):
        # print("Creating a dynamic trapezoidal mf")
        # print("with parameters")
        super().__init__(a, b, c, d)
        # print(self._a)
        # print(self._b)
        # print(self._c)
        # print(self._d)
        self._k_GP = k_GP
        self._theta = theta

    def _execute(self, x):
        # print("computing membership of value ", x, "in dyanimc trapezoidal mf with param")
        # print(self._a)
        # print(self._b)
        # print(self._c)
        # print(self._d)
        # print("value", super()._execute(x))
        if (self._k_GP is None) or (self._theta is None):
            return super()._execute(x)
        else:
            A_x = super()._execute(x)
            if A_x < self._theta:
                A_x = (self._theta ** (1 - self._k_GP)) * (A_x ** self._k_GP)
            else:
                A_x = 1 - (((1 - self._theta) ** (1 - self._k_GP)) * ((1 - A_x) ** self._k_GP))
            try:
                A_x = float(A_x)
            except:
                A_x = A_x.real

            return min(1, max(0.0, A_x))

class DynamicTrapezoidFuzzySet(sf.FuzzySet):
    def __init__(self, function=None, term=""):
        # print("creating a dynamic trapezoid fuzzy set for term ", term)
        super().__init__(function=function, term=term)

    def set_params(self, a=None, b=None, c=None, d=None, k_GP=None, theta=None):
        if a is not None: self._funpointer._a = a
        if b is not None: self._funpointer._b = b
        if c is not None: self._funpointer._c = c
        if d is not None: self._funpointer._d = d
        if k_GP is not None: self._funpointer._k_GP = k_GP
        if theta is not None: self._funpointer._theta = theta

    def setGeneralizedPositivelyModifierParams(self, theta, k_GP):
        self._funpointer._theta = theta
        self._funpointer._k_GP = k_GP
        return  self._funpointer._theta, self._funpointer._k_GP

    def get_params(self):
        return self._funpointer._a, self._funpointer._b, self._funpointer._c, self._funpointer._d, self._funpointer._k_GP, self._funpointer._theta

    def scale(self, a, b, lambd, k_SF):
        self._funpointer._a = scaleFrom01ToAB(self._funpointer._a, a, b, lambd, k_SF)
        self._funpointer._b = scaleFrom01ToAB(self._funpointer._b, a, b, lambd, k_SF)
        self._funpointer._c = scaleFrom01ToAB(self._funpointer._c, a, b, lambd, k_SF)
        self._funpointer._d = scaleFrom01ToAB(self._funpointer._d, a, b, lambd, k_SF)
        return {"a": self._funpointer._a, "b": self._funpointer._b, "c": self._funpointer._c, "d": self._funpointer._d}

    def scaleLinear(self, a, b, a1, b1):
        self._funpointer._a = linearScaleFromABToA1B1(self._funpointer._a, a, b, a1, b1)
        self._funpointer._b = linearScaleFromABToA1B1(self._funpointer._b, a, b, a1, b1)
        self._funpointer._c = linearScaleFromABToA1B1(self._funpointer._c, a, b, a1, b1)
        self._funpointer._d = linearScaleFromABToA1B1(self._funpointer._d, a, b, a1, b1)
        return {"a": self._funpointer._a, "b": self._funpointer._b, "c": self._funpointer._c, "d": self._funpointer._d}

    def updateSupportBoundaries(self, a1, d1):
        self._funpointer._a = a1
        self._funpointer._d = d1
        self._funpointer._b = max(self._funpointer._a, min(self._funpointer._b, self._funpointer._d))
        self._funpointer._c = max(self._funpointer._a, min(self._funpointer._c, self._funpointer._d))
        return {"a": self._funpointer._a, "b": self._funpointer._b, "c": self._funpointer._c, "d": self._funpointer._d}

    def modifyCorePosition(self, k_CP):
        a, b, c, d, k_GP, theta = self.get_params()
        if k_CP < 0:
            self._funpointer._b = b - ((a - b) * k_CP)
            self._funpointer._c = c - ((a - b) * k_CP)
        else:
            self._funpointer._b = b + ((d - c) * k_CP)
            self._funpointer._c = c + ((d - c) * k_CP)
        return {"a": self._funpointer._a, "b": self._funpointer._b, "c": self._funpointer._c, "d": self._funpointer._d}

    def modifyCoreWidth(self, k_CW):
        a, b, c, d, k_GP, theta = self.get_params()
        denom = (b - a + d - c)
        w = (c - b) / denom if denom > 0 else 0
        if k_CW < 0:
            self._funpointer._b = b + (w * (a - b) * k_CW)
            self._funpointer._c = c + (w * (d - c) * k_CW)
        else:
            self._funpointer._b = b + ((a - b) * k_CW)
            self._funpointer._c = c + ((d - c) * k_CW)
        return {"a": self._funpointer._a, "b": self._funpointer._b, "c": self._funpointer._c, "d": self._funpointer._d}

    def modifySupportWidth(self, k_SW, lv_universe):
        a, b, c, d, k_GP, theta = self.get_params()
        sm = (a + d) / 2
        # determine the new values
        new_a = sm + (k_SW * (a - sm))
        new_b = sm + (k_SW * (b - sm))
        new_c = sm + (k_SW * (c - sm))
        new_d = sm + (k_SW * (d - sm))

        # making them fit the universe
        self._funpointer._a = max(lv_universe[0], min(new_a, lv_universe[1]))
        self._funpointer._b = max(lv_universe[0], min(new_b, lv_universe[1]))
        self._funpointer._c = max(lv_universe[0], min(new_c, lv_universe[1]))
        self._funpointer._d = max(lv_universe[0], min(new_d, lv_universe[1]))

        return {"a": self._funpointer._a, "b": self._funpointer._b, "c": self._funpointer._c, "d": self._funpointer._d}