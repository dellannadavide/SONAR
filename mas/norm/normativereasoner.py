import utils.constants as Constants

class NormativeReasoner:
    """ This class represents an external (to the bdi agent, i.e., to agentspeak) normative reasoning module.
     At the moment it is not used though. """

    def __init__(self) -> None:
        super().__init__()
        """
        This dictionary containts paris <key, dict>
        where key corresponds to a context (a condition that characterizes a situation),
        and dict is a dictionary containing 4 lists each containing, respectively, prohibited actions, prohibited goals, obliged actions, obliged goals, 
        in that context.
        If no norm applies in a certain context, the lists are empty."""
        self.norms = {
            Constants.LV_DIST: {},
            Constants.LV_DUTY: {},
            Constants.LV_INTELLECT: {},
            Constants.LV_ADVERSITY: {},
            Constants.LV_MATING: {},
            Constants.LV_POSITIVITY: {},
            Constants.LV_NEGATIVITY: {},
            Constants.LV_DECEPTION: {},
            Constants.LV_SOCIALITY: {},
            "PRIVATE": {},
            "SOCIAL": {},
            "PUBLIC": {}
        }
        for c in self.norms:
            self.norms[c] = {"P_A": [], "P_G": [], "O_A": [], "O_G": []}

        self.norms["SOCIAL"]["O_G"] = [["obliged_goal", "greet"]]

    def getApplicableNorms(self, list_of_social_eval_pairs):
        social_context = {}
        nr_pairs = int(len(list_of_social_eval_pairs) / 2)
        for i in range(nr_pairs):
            social_context[list_of_social_eval_pairs[i * 2]] = float(list_of_social_eval_pairs[(i * 2) + 1])

        """
        Here any kind of complex normative reasoning could be introduced.
        This class could actually even be an another BDI agent that performs inference.
        Or normative reasoning could be done via some formal reasoner of other type (e.g., logic based).
        or it can also consider whatever information needed, e.g., from online or so.
        
        For the time being, normative reasoning will be very simple. 
        Norms will consist of simple set of rules:
        IF context THEN prohibited(<action, or goal>)
        IF context THEN obliged(<action, or goal>)
        the actual context is going to be the most certain social interpretation in the social context dict
        so basically given a certain social context we determine a number of prohibited/obliged actions or goals
        """

        context = max(social_context, key=social_context.get)
        if context in self.norms:
            return self.norms[context]
        else:
            return {"P_A": [], "P_G": [], "O_A": [], "O_G": []}
