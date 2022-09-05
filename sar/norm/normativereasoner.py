import utils.constants as Constants

class NormativeReasoner:

    def __init__(self) -> None:
        super().__init__()
        """
        This dictionary containts paris <key, list>
        where key corresponds to a social interpretation of a context,
        and list is a list of prohibited or obliged actions or goals in that context.
        If no norm applies in a certain context, the list is empty."""
        self.norms = {
            Constants.LV_DIST: [],
            Constants.LV_DUTY: [],
            Constants.LV_INTELLECT: [],
            Constants.LV_ADVERSITY: [],
            Constants.LV_MATING: [],
            Constants.LV_POSITIVITY: [],
            Constants.LV_NEGATIVITY: [],
            Constants.LV_DECEPTION: [],
            Constants.LV_SOCIALITY: []

        }

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
        return self.norms[context]
