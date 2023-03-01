import sys

import skfuzzy as fuzz
from skfuzzy import control as ctrl
from skfuzzy.control.controlsystem import CrispValueCalculator

import utils.constants as Constants


class FuzzyController:
    """
    Class implementing a Fuzzy Controller to be used for the SAR creative and assessor controller
    This class makes use of the SkFuzzy library
    """

    @staticmethod
    def getMF(dimensions_values, variables_universe, fuzzysets_values, variables_default_val, possible_inputs, possible_outputs):
        """ Static function that returns the membership functions of all the input and output possible variables
        of the controller.
        The function is made static under the assumption that the membership functions and the variables do not change
        over time.
        """
        inputs_mf = {}
        outputs_mf = {}
        for i in possible_inputs:
            inputs_mf[i] = ctrl.Antecedent(variables_universe[i], i)
            for v in dimensions_values[i]:
                inputs_mf[i][v] = fuzz.trapmf(variables_universe[i], fuzzysets_values[i][v])
        for a in possible_outputs:
            outputs_mf[a] = ctrl.Consequent(variables_universe[a], a)
            for v in dimensions_values[a]:
                outputs_mf[a][v] = fuzz.trapmf(outputs_mf[a].universe, fuzzysets_values[a][v])
        return inputs_mf, outputs_mf

    def __init__(self, dimensions_values, variables_universe, fuzzysets_values, variables_default_val, possible_inputs, possible_outputs, rulebase):
        """ Initializes the controller.
        - Assigns a default value to the variables
        - Creates the controller (via the function updateController) with the give rulebase
        - Initializes the string representation of the rule base for indexing (could be optimized) """
        self.variables_default_val = variables_default_val
        self.inputs = []
        self.updateController(rulebase)
        self.rules_str = []
        for r in rulebase:
            self.rules_str.append(str(r))

    def refreshInputs(self):
        """ Refreshes the inputs of the controller """
        self.inputs = [i for i in self.controlsystem._get_inputs()]

    def feed_inputs(self, inputs):
        """ Feeds the inputs in @input to the controller"""
        for v in self.inputs:
            try:
                self.controlsystem.input[v] = inputs[v]
            except:
                pass

    def updateController(self, rulebase):
        """ Creates a new Fuzzy Control System with rule base @rulebase, and assigns it to the current instance """
        self.control = ctrl.ControlSystem(rulebase)
        self.controlsystem = ctrl.ControlSystemSimulation(self.control, cache=False) #cache=False for lower memory usage
        self.refreshInputs()

    def compute(self, verbose=False):
        """
        RE-IMPLEMENTATION OF THE compute() method from skfuzzy, which computes the output of the controller given the
        current inputs. The function is re-implemented so that it is possible to catch all the exceptions and
        still work in case some outputs are not retrieved (since this can happen in the system, given the fact that
        we autonomously evolve the rules, which can lead to rule bases that do not cover all possible cases).

        The function returns a crisp value for the output variables of the controller
        and the level of activation (firing strength) of all the rules
        """

        rules_activations = {}
        c_out = {}
        is_exception = False

        self.controlsystem.input._update_to_current()
        if verbose > Constants.VERBOSE_BASIC:
            print("assessor inputs")
            print(self.controlsystem.input)
        # Check if any fuzzy variables lack input values and fuzzify inputs
        for antecedent in self.controlsystem.ctrl.antecedents:
            if antecedent.input[self.controlsystem] is None:
                print("All antecedents must have input values!")
                raise ValueError("All antecedents must have input values!")
            CrispValueCalculator(antecedent, self.controlsystem).fuzz(antecedent.input[self.controlsystem])
        # Calculate rules, taking inputs and accumulating outputs
        first = True
        for rule in self.controlsystem.ctrl.rules:
            # Clear results of prior runs from Terms if needed.
            if first:
                for c in rule.consequent:
                    c.term.membership_value[self.controlsystem] = None
                    c.activation[self.controlsystem] = None
                first = False
            self.controlsystem.compute_rule(rule)
            if verbose > Constants.VERBOSE_BASIC:
                print("antecedent membership of rule " + str(rule))
                print(rule.antecedent.membership_value[self.controlsystem])
            rules_activations[str(rule)] = rule.aggregate_firing[self.controlsystem]  # this is also added

        for consequent in self.controlsystem.ctrl.consequents:
            try:  # here's the difference now. I'm introducing this try-catch test
                consequent.output[self.controlsystem] = CrispValueCalculator(consequent, self.controlsystem).defuzz()
                self.controlsystem.output[consequent.label] = consequent.output[self.controlsystem]
                c_out[consequent.label] = self.controlsystem.output[consequent.label]
                # print("defuzz for "+str(consequent.label)+": "+str(c_out[consequent.label]))
            except:
                # in case it fails to defuzzify because the area is 0, then I give the default value to the variable
                # print("Zero defuzz area for "+str(consequent.label))
                c_out[consequent.label] = self.variables_default_val[consequent.label]
                is_exception = True

        if verbose > Constants.VERBOSE_BASIC:
            print("assessor inputs")
            print(self.controlsystem.input)
            print("rules activations after compute")
            for r in rules_activations:
                print(str(r) + "\n\t\t--->" + str(rules_activations[r]))
            print("c_outs " + str(c_out))

        self.controlsystem._reset_simulation()
        return c_out, rules_activations, is_exception

    def computeOutput(self, inputs, verbose=False):
        """ Function that first feeds the given inputs to the controller,
        and then compute the output of the controller """
        self.feed_inputs(inputs)
        return self.compute(verbose)

    def addRules(self, rules):
        """ Function that adds a set of rules to the rule base of the controller """
        for r in rules:
            if not str(r) in self.rules_str:
                self.control.addrule(r)
                self.rules_str.append(str(r))
        self.refreshInputs()
        newrulebase = [i for i in self.control.rules]
        return newrulebase

    def getRules(self):
        """ Function that returns the current rules in the rule base of the controller """
        return self.control.rules

    def getAllRules(self):
        """ Function similar to getRules, but returns a list of rules """
        allr = []
        try:
            allr = self.control.rules.all_rules
        except:
            pass
        return allr

    def printRules(self):
        """ Function to print all rules in the current rule base"""
        for rule in self.control.rules:
            print(rule)

    def createAndAddRule(self, antecedents, consequents, controller_inputs_mf, controller_outputs_mf):
        """ Function that, given sets of terms for the antecendent and consequent of a rule,
        synthesises the rule, and adds it to the rule base of the controller """
        rule = None
        try:
            #create the rule
            ante = None
            for a in antecedents:
                ling_var = controller_inputs_mf[a[0]]
                ling_val = a[1]
                term = ling_var[ling_val]
                if ante is None:
                    ante = term
                else:
                    ante = ante & term
            conseq = None
            for c in consequents:
                ling_var = controller_outputs_mf[c[0]]
                ling_val = c[1]
                term = ling_var[ling_val]
                if conseq is None:
                    conseq = term
                else:
                    conseq = conseq & term
            rule = ctrl.Rule(ante, conseq)
            #add the rule
            self.addRules([rule])
        except:
            print(sys.exc_info())
            print("Could not create rule with antecedents: "+str(antecedents)+" and consequents: "+str(consequents))
        return rule
