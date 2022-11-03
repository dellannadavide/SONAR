from abc import abstractmethod
import spacy

nlp = spacy.load("en_core_web_sm")

from statemachine import StateMachine, State


class ChatterStateMachine(StateMachine):
    def __init__(self, chatter) -> None:
        super().__init__()
        self.chatter = chatter
        self.name = ""
        self.temp_name = ""

    class ChatterState(State):
        @abstractmethod
        def process_input(self, user_input: str):
            pass

    class DefaultChatterState(ChatterState):
        def process_input(self, user_input):
            return None

    class NameRetrievalState(ChatterState):
        def __init__(self, name, value=None, initial=False, nlp=None):
            super().__init__(name, value, initial)
            self.nlp = nlp

        def setNLP(self, nlp):
            self.nlp = nlp

        def process_input(self, user_input):
            detected_name = None
            if not self.nlp is None:
                doc = self.nlp(user_input)
                for token in doc:
                    if token.pos_ == "PROPN":
                        detected_name = token.text
            return detected_name

    class NameConfirmationState(ChatterState):
        def process_input(self, user_input):
            return str(user_input).lower()

    # States
    default = DefaultChatterState('Default', initial=True)
    name_retrieval = NameRetrievalState('Retrieving Person Name')
    name_confirmation = NameConfirmationState('Confirming Person Name')

    # State Transitions, and associated events
    retrieve_name = default.to(name_retrieval)

    confirm_name = name_retrieval.to(name_confirmation)

    def on_confirm_name(self):
        print("bot: Your name is", self.temp_name, ", correct? (Yes or No)")

    repeat_name = name_confirmation.to(name_retrieval)

    def on_repeat_name(self):
        print("bot: Alright, can you repeat your name then?")

    end_name_retrieval_positive = name_confirmation.to(default)

    def on_end_name_retrieval_positive(self):
        print("bot: Got it! Nice to meet you", self.name, "!")

    def process_input(self, user_input):
        state_output = self.current_state.process_input(user_input)
        if self.current_state == ChatterStateMachine.default:
            if not state_output is None:
                print("something is wrong")
        elif self.current_state == ChatterStateMachine.name_retrieval:
            if state_output is not None:  # the output is the name
                self.temp_name = state_output
                print("---setting temp_name to", self.temp_name)
                self.confirm_name()  # I transition to confirmation
            else:  # then no name detected
                print("I couldn't get it. Could you repeat, please?")  # and stay in the same state
        elif self.current_state == ChatterStateMachine.name_confirmation:
            if state_output == "yes":
                self.name = self.temp_name
                self.end_name_retrieval_positive()
            elif state_output == "no":
                self.temp_name = ""
                self.repeat_name()  # i go back to name_retrieval
            else:
                print("bot: Please, to avoid misunderstandings, answer with yes or no. Is your name", self.temp_name, "?")
        else:
            print("I'm in some wrong state ", self.current_state)



chatter_state_machine = ChatterStateMachine("test")
chatter_state_machine.name_retrieval.setNLP(nlp)

user_input = "hey there what'sapp my name is david"
print("user: ", user_input)
chatter_state_machine.process_input(user_input)

print("bot: hello, what's your name?")
chatter_state_machine.retrieve_name()  # after this I am in name_retrieval

user_input = "hey there what'sapp my name is david"
print("user: ", user_input)
chatter_state_machine.process_input(user_input)

user_input = "yes that's correct"
print("user: ", user_input)
chatter_state_machine.process_input(user_input)

user_input = "ok"
print("user: ", user_input)
chatter_state_machine.process_input(user_input)

user_input = "no"
print("user: ", user_input)
chatter_state_machine.process_input(user_input)

user_input = "carlo"
print("user: ", user_input)
chatter_state_machine.process_input(user_input)

user_input = "yes"
print("user: ", user_input)
chatter_state_machine.process_input(user_input)