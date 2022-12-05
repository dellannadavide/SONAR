""" Constants to be used for utilities """
LOGGING_LV_DEBUG_NOSAR = 15
LOGGING_LV_DEBUG_NOSAR_NAME = "DEBUG_NOSAR"

VERBOSE_FALSE = 0
VERBOSE_VERY_LOW = 0.5
VERBOSE_BASIC = 1
VERBOSE_TRUE = 2
VERBOSE_VERY_HIGH = 3

MQTT_BROKER_ADDRESS = "localhost"
MQTT_CLIENT_TYPE_LISTENER = "MQTT_CLIENT_TYPE_LISTENER"
MQTT_CLIENT_TYPE_PUBLISHER = "MQTT_CLIENT_TYPE_PUBLISHER"

TOPIC_GROUP_VISION = "NAO_TOPIC_GROUP_VISION/"
TOPIC_HUMAN_DETECTION = TOPIC_GROUP_VISION + "NAO_TOPIC_HUMAN_DETECTED"
TOPIC_HEAD_TRACKER = TOPIC_GROUP_VISION + "NAO_TOPIC_HEAD_TRACKER"
TOPIC_IMAGE = TOPIC_GROUP_VISION + "NAO_TOPIC_IMAGE"
TOPIC_OBJECT_DETECTION = TOPIC_GROUP_VISION + "NAO_TOPIC_OBJECT_DETECTION"
TOPIC_EMOTION_DETECTION = TOPIC_GROUP_VISION + "NAO_TOPIC_EMOTION_DETECTION"

TOPIC_GROUP_SOUND = "NAO_TOPIC_GROUP_SOUND/"
TOPIC_SPEECH = TOPIC_GROUP_SOUND + "NAO_TOPIC_SPEECH"
TOPIC_MICENERGY = TOPIC_GROUP_SOUND + "NAO_TOPIC_MICENERGY"

TOPIC_DISTANCE = "NAO_TOPIC_DISTANCE"
TOPIC_DIRECTIVE_TTS = "NAO_TOPIC_DIRECTIVE_TTS"
TOPIC_DIRECTIVE_SYSTEM = "NAO_TOPIC_DIRECTIVE_SYSTEM"
TOPIC_POSTURE = "NAO_TOPIC_POSTURE"
TOPIC_MOTION = "NAO_TOPIC_MOTION"
TOPIC_SOCIAL_INTERPR = "NAO_TOPIC_SOCIAL_INTERPR"
TOPIC_BEHAVIOR = "NAO_TOPIC_BEHAVIOR"

TOPIC_LEDS = "NAO_TOPIC_LEDS"

TOPIC_NAME_LEARNT = "NAO_TOPIC_NAME_LEARNT"

TOPIC_INTERNAL_COMMUNICATIONS = "NAO_TOPIC_INTERNAL_COMMUNICATIONS"

SPADE_MSG_METADATA_PERFORMATIVE = "performative"
SPADE_MSG_METADATA_KEYS_TYPE = "keys_type"

SPADE_MSG_DIRECTIVE = "SPADE_MSG_DIRECTIVE"
SPADE_MSG_PERSON = "SPADE_MSG_PERSON"
SPADE_MSG_OBJECT = "SPADE_MSG_OBJECT"
SPADE_MSG_TO_SAY = "SPADE_MSG_TO_SAY"
SPADE_MSG_SAID = "SPADE_MSG_SAID"
SPADE_MSG_NAO_ROLE = "SPADE_MSG_NAO_ROLE"
SPADE_MSG_HUMAN_EMOTION = "SPADE_MSG_HUMAN_EMOTION"
SPADE_MSG_POSTURE = "SPADE_MSG_POSTURE"
SPADE_MSG_DIRECTION = "SPADE_MSG_DIRECTION"
SPADE_MSG_BATCH_ID = "SPADE_MSG_BATCH_ID"
SPADE_MSG_SOCIAL_EVAL = "social_eval"

ASL_FLUENT_ROLE_SUBORDINATE = "subordinate"
ASL_FLUENT_ROLE_NONE = "no_role"
ASL_FLUENT_EMOTION_NEUTRAL = "neutral_emotion"
ASL_FLUENT_UNKNOWN_PERSON = "unknown"
ASL_FLUENT_UNKNOWN_DIRECTION = "unknown"
ASL_FLUENT_CENTER_DIRECTION = "center"
ASL_FLUENT_TOP_DIRECTION = "top"
ASL_FLUENT_BOTTOM_DIRECTION = "bottom"
ASL_FLUENT_RIGHT_DIRECTION = "right"
ASL_FLUENT_LEFT_DIRECTION = "left"
ASL_FLUENT_TOP_RIGHT_DIRECTION = ASL_FLUENT_TOP_DIRECTION + "_" + ASL_FLUENT_RIGHT_DIRECTION
ASL_FLUENT_TOP_LEFT_DIRECTION = ASL_FLUENT_TOP_DIRECTION + "_" + ASL_FLUENT_LEFT_DIRECTION
ASL_FLUENT_BOTTOM_RIGHT_DIRECTION = ASL_FLUENT_BOTTOM_DIRECTION + "_" + ASL_FLUENT_RIGHT_DIRECTION
ASL_FLUENT_BOTTOM_LEFT_DIRECTION = ASL_FLUENT_BOTTOM_DIRECTION + "_" + ASL_FLUENT_LEFT_DIRECTION
ASL_FLUENT_FACE = "face"
ASL_FLUENT_IS_POSTURE = "is_posture"
ASL_FLUENT_IS_ANIMAATION = "is_animation"
ASL_FLUENT_BYE = "bye_bye"
ASL_FLUENT_WHAT_YOU_SEE = "tell_what_you_see"
ASL_FLUENT_WHAT_USER_SAID = "tell_what_user_said"
ASL_FLUENT_WHAT_ROBOT_SAID = "tell_what_you_said"
ASL_FLUENT_TELL_ROBOT_NAME = "tell_robot_name"

ASL_BEL_PERSON_NAME = "person_name"
ASL_BEL_IS_ADMIN = "is_admin"
ASL_BEL_VISIBLE = "visible"
ASL_BEL_CURR_ROLE = "curr_role"
ASL_BEL_IS_LOOKING = "is_looking"
ASL_BEL_DISTANCE = "distance"
ASL_BEL_PERCEIVED_OBJECT = "perceived_object"
ASL_BEL_DETECTED_EMOTION = "detected_emotion"
ASL_BEL_SAID = "said"
ASL_BEL_PERFORM_REASONING = "perform_reasoning"
ASL_BEL_PREPARE_FOR_NEXT_CYCLE = "prepare_for_next_cycle"
ASL_BEL_ADD_SPONT_CONV_GOAL = "add_spontaneous_conversation_goal"
ASL_BEL_INTERNAL = "internal"

ASL_BEL_IS_ASLEEP = "is_asleep"



ASL_BEL_PROHIBITED_GOAL = "prohibited_goal"
ASL_BEL_PROHIBITED_ACTION = "prohibited_action"
ASL_BEL_OBLIGED_GOAL = "obliged_goal"
ASL_BEL_OBLIGED_ACTION = "obliged_action"
ASL_BEL_PROHIBITIONS_OBLIGATIONS = [ASL_BEL_PROHIBITED_GOAL,
                                    ASL_BEL_PROHIBITED_ACTION,
                                    ASL_BEL_OBLIGED_GOAL,
                                    ASL_BEL_OBLIGED_ACTION]

ASL_BEL_MOVED_HEAD_PREFIX = "moved_head_"
ASL_BEL_ESTABLISHED_TRUST = "established_trust"
ASL_BEL_UPDATED_TOPIC_INTEREST = "updated_topic_interest"
ASL_BEL_UPDATED_TOPIC_PERC = "updated_topic_perc"
ASL_BEL_UPDATED_TOPIC_SPONTANEOUS = "updated_topic_spontaneous"

ASL_SOURCE_PERCEPT_SUFFIX = "[source(percept)]"

""" Note: the values of all constants starting with 'LV' may be used by the fuzzy systems,
and therefore are also used in the excel initialization files.
So values should match.
"""

LV_DUTY = "DUTY"
LV_INTELLECT = "INTELLECT"
LV_ADVERSITY = "ADVERSITY"
LV_MATING = "MATING"
LV_POSITIVITY = "POSITIVITY"
LV_NEGATIVITY = "NEGATIVITY"
LV_DECEPTION = "DECEPTION"
LV_SOCIALITY = "SOCIALITY"
LV_SOCIAL = "SOCIAL"
LV_PERSONAL = "PERSONAL"
LV_PUBLIC = "PUBLIC"
LV_UNKNOWN = "UNKNOWN"

LV_DIST = "DIST"
LV_VOLUME = "VOLUME"
LV_MOVEMENTS = "MOVEMENTS"
LV_SPEED_VOICE = "SPEED_VOICE"
LV_TONE_VOICE = "TONE_VOICE"

LV_ROLE_SUBORDINATE = "ROLE_SUBORDINATE"

VOCABULARY_PERSONAL_CONVERSATION = {"personal", "private", "secret", "confidential", "classified",
                                    "keep it for yourself", "keep it to yourself",
                                    "keep for yourself", "keep to yourself",
                                    "don't tell anyone", "do not tell anyone",
                                    "do not tell anybody", "don't tell anybody", "trust", "trust you",
                                    "keep it just for yourself", "keep it only for yourself", "keep it just to yourself",
                                    "keep it only to yourself", "keep just for yourself", "keep only for yourself",
                                    "keep just to yourself", "keep only to yourself"}

VOCABULARY_BYE_BYE = {"goodbye", "goodnight", "bye", "bye-bye", "bye bye", "see you later", "see you soon",
                      "adios", "adieu", "talk to you later", "goodnight", "catch you later", "I have to leave",
                      "leave now", "I want to leave", "I need to leave", "I have to go",
                        "I need to go", "I should go", "see you tomorrow"}


VOCABULARY_TELL_ROBOT_NAME = {"what's your name", "what is your name", "what can i call you", "how can i call you",
                              "how can i address you", "how should i call you", "how should i address you",
                              "how shall i call you", "how shall i address you", "what are you named",
                              "what do you call yourself", "may i ask your name", "may i ask what's your name",
                              "may i ask what is your name"}

VOCABULARY_WHAT_IS_THIS = {"what is this", "what's this", "can you see this", "do you see this", "what can you see",
                           "what do you see", "do you know what is this",
                           "do you know what this is",
                           "do you know what is this thing", "do you know what is this object",
                           "can you tell me what is this", "can you tell me what this is",
                           "can you tell me what is this object",
                           "can you tell me what you see", "tell me what you see", "tell me what you can see",
                           "tell me what is this", "tell me what is this object", "tell me what is this thing"}

VOCABULARY_WHAT_USER_SAID = {"what did i say", "what did i just say", "tell me what did i say",
                             "tell me what i said", "tell me what i just said", "can you tell me what did i say",
                             "can you tell me what i said", "can you tell me what i just said", "can you tell me what i said",
                             "what did i ask", "what did i ask you", "what did i just ask", "tell me what did i ask",
                             "tell me what i asked", "tell me what i just asked you", "tell me what i asked",
                             "can you tell me what did i ask you",
                             "can you tell me what i asked", "can you tell me what i just asked",
                             "can you tell me what i asked"
                             }

VOCABULARY_WHAT_ROBOT_SAID = {"what did you say", "can you repeat", "can you repeat please", "can you repeat what you said",
                              "can you repeat what you just said"}

VOCABULARY_ANYWAYS = ["", "anyways", "anyway", "anyhow", "in any case", "having said that", "also", "on top of that",
                      "apart from that", "aside from that", "other than that", "in adition to that", "by the way",
                      "on another note", "on a related note", "anyhoo", "on a different note"]

SOCIAL_QUESTIONS_EXAMPLES = [
    "What tv shows are you into?",
    "What's your favorite movie?",
    "What's your favorite sport?",
    "What's your favorite food?",
    "What's your favourite book?",
    "I have a question for you. If you could visit anywhere in the world, where would you go?",
    "What's your favorite activity to do when you have time off?",
    "What are some fun things to do here in The Netherlands?",
    "What do you like to do that's fun and relaxing?",
    "Do you have friends?",
    "Question. What''s something you always wanted to try but haven't?",
    "Can I ask you a question? What makes you unique?",
    "Tell me a random fun fact about you!",
    "Would you rather go to the beach or to the mountains?",
    "Would you rather always be 10 minutes late or always be 20 minutes early?",
    "Would you rather have unlimited battery life on all of your devices or have free WiFi wherever you go?",
    "Would you rather be in a zombie apocalypse or a robot apocalypse?",
    "What's your favourite place in the world?",
    "What's something you're proud of?",
    "Where are you from?",
    "Do you have a favourite hobby?",
    "If you could go out to dinner with anyone in the world, who would it be?",
    "What's your favourite food?",
    "How do you communicate your feelings to others?",
    "What do you do in your spare time?",
    "Do you think we have things in common?",
    "If I were an animal, what kind would I be?",
    "What's your favorite thing you've learned about me so far?",
    "What was your first impression of me?",
    "What's your least favorite thing you've learned about me so far?",
    "What do you do for a living?"
]



LV_VOC_PERSONAL = "PERSONAL_VOCABULARY"

SOCIAL_INTERPRETATIONS = [
    LV_DUTY,  # D
    LV_INTELLECT,  # I
    LV_ADVERSITY,  # A
    LV_MATING,  # M
    LV_POSITIVITY,  # O
    LV_NEGATIVITY,  # N
    LV_DECEPTION,  # D
    LV_SOCIALITY,  # S
    LV_SOCIAL,
    LV_PERSONAL,
    LV_PUBLIC,
    LV_UNKNOWN
]

LV_FAMILY = "FAMILY"
LV_MATE = "MATE"
LV_FRIENDS = "FRIENDS"
LV_COHABITANTS = "COHABITANTS"
LV_COLLEAGUES = "COLLEAGUES"
LV_ALONE = "ALONE"
LV_SPORTS = "SPORTS"
LV_EXAM = "EXAM"
LV_FOOD = "FOOD"
LV_EATING = "EATING"
LV_DRINKING = "DRINKING"
LV_COMMUNICATING = "COMMUNICATING"
LV_TV = "TV"
LV_COMMUTING = "COMMUTING"
LV_COMPUTER = "COMPUTER"
LV_VIDEOGAMES = "VIDEOGAMES"
LV_READING = "READING"
LV_WORKING = "WORKING"
LV_SHOPPING = "SHOPPING"
LV_GROOMING = "GROOMING"
LV_WAITING = "WAITING"
LV_SLEEP = "SLEEP"
LV_MUSIC = "MUSIC"
LV_TELEPHONE = "TELEPHONE"
LV_HOME = "HOME"
LV_BATHROOM = "BATHROOM"
LV_KITCHEN = "KITCHEN"
LV_BED = "BED"
LV_UNIVERSITY = "UNIVERSITY"
LV_BAR = "BAR"

LV_SOCIAL_CUES = [LV_FAMILY,
                  LV_MATE,
                  LV_FRIENDS,
                  LV_COHABITANTS,
                  LV_COLLEAGUES,
                  LV_ALONE,
                  LV_SPORTS,
                  LV_EXAM,
                  LV_FOOD,
                  LV_EATING,
                  LV_DRINKING,
                  LV_COMMUNICATING,
                  LV_TV,
                  LV_COMMUTING,
                  LV_COMPUTER,
                  LV_VIDEOGAMES,
                  LV_READING,
                  LV_WORKING,
                  LV_SHOPPING,
                  LV_GROOMING,
                  LV_WAITING,
                  LV_SLEEP,
                  LV_MUSIC,
                  LV_TELEPHONE,
                  LV_HOME,
                  LV_BATHROOM,
                  LV_KITCHEN,
                  LV_BED,
                  LV_UNIVERSITY,
                  LV_BAR]

STATIC_LV = LV_SOCIAL_CUES
DYNAMIC_LV = [LV_DIST, LV_VOLUME, LV_MOVEMENTS]

ACTUATION_ASPECT_CHATTER = "chat_qualifier"
ACTUATION_ASPECT_SYSTEM = "system_qualifier"
ACTUATION_ASPECT_POSITION = "position_qualifier"
ACTUATION_ASPECT_POSTURE = "posture_qualifier"
ACTUATION_ASPECTS = [
    ACTUATION_ASPECT_CHATTER,
    ACTUATION_ASPECT_SYSTEM,
    ACTUATION_ASPECT_POSITION,
    ACTUATION_ASPECT_POSTURE
]

PERFORMATIVE_INFORM = "inform"
PERFORMATIVE_REQUEST = "request"
PERFORMATIVE_NEW_BELIEF = "newbel"

NO_DATA = "NO_DATA"

STRING_SEPARATOR = "<str_sep>"
BEL_STRING_SEPARATOR = "<bel_str_sep>"
ASL_STRING_SEPARATOR = "__"
STRING_SEPARATOR_INNER = "<str_sep_inner>"

DIRECTIVE_SHUT_DOWN = "to_shut_down"
DIRECTIVE_SLEEP = "to_sleep"
DIRECTIVE_WAKE_UP = "to_wake_up"
DIRECTIVE_SAY = "say"
DIRECTIVE_SAY_SPONTANEOUS = "say_spontaneous"
DIRECTIVE_SAY_IN_RESPONSE = "say_in_response"
DIRECTIVE_SAY_WHAT_USER_SAID = "say_what_user_said"
DIRECTIVE_SAY_WHAT_BOT_SAID = "say_what_bot_said"
DIRECTIVE_BEGIN_GREETING = "begin_greeting_procedure"
DIRECTIVE_BEGIN_GOODBYE = "begin_goodbye_procedure"
DIRECTIVE_CONTINUE_CONVERSATION = "continue_conversation"
DIRECTIVE_TURN_CONVERSATION = "turn_conversation"
DIRECTIVE_REPLY_TO_REACTIVE = "reply_to"
DIRECTIVE_REPLY_TO_PROACTIVE = "reply_to_proactive"
DIRECTIVE_REPLY_PARROT = "reply_parrot"
DIRECTIVE_SET_USER_INPUT_PROCESSED_WITH_NO_REPLY = "set_user_input_processed_no_reply"
DIRECTIVE_GOTOPOSTURE = "go_to_posture"
DIRECTIVE_MOVEHEAD = "move_head"
DIRECTIVE_PLAYANIMATION = "play_animation"
DIRECTIVE_EXEC_BEHAVIOR = "exec_behavior"
DIRECTIVE_UPDATE_TOPIC_INTEREST = "update_topic_interest"
DIRECTIVE_LED_CHANGE_COLOR = "change_led_color"
DIRECTIVE_LED_SET_COLOR = "set_led_color"
DIRECTIVE_LED_SET_THINKING = "set_led_thinking_color"

SPEECH_KEYWORDS_AFFIRMATIVE = ["yes", "yeah", "correct", "exactly", "yep", "bravo", "ok"]
SPEECH_KEYWORDS_NEGATIVE = ["no", "nope", "wrong", "not", "yep", "incorrect", "nu", "but"]

I_YOU_MAPPING = {
    "am" : "are",
    "are" : "am",
    'i' : 'you',
    'my' : 'yours',
    'me' : 'you',
    'mine' : 'yours',
    'you' : 'I',
    'your' : 'my',
    'yours' : 'mine'
}



COLORS_BLUE = "blue"
COLORS_WHITE = "white"
COLORS_GREEN = "green"
COLORS_RED = "red"

POSTURE_SIT = "Sit"
POSTURE_CROUCH = "Crouch"
POSTURE_LAYINGBACK = "LayingBack"
POSTURE_LAYINGBELLY = "LayingBelly"
POSTURE_STAND = "Stand"

POSTURES = {"sit": POSTURE_CROUCH,
            "sit" + ASL_STRING_SEPARATOR + "down": POSTURE_CROUCH,
            "crouch": POSTURE_CROUCH,
            "lay" + ASL_STRING_SEPARATOR + "back": POSTURE_LAYINGBACK,
            "lay" + ASL_STRING_SEPARATOR + "belly": POSTURE_LAYINGBELLY,
            "stand": POSTURE_STAND,
            "stand" + ASL_STRING_SEPARATOR + "up": POSTURE_STAND}


POSTURES_ADDITIONAL_COMMAND_PREFIXES = [["can", "you"], ["do", "you", "know", "how", "to"]]
for posture_key in list(POSTURES.keys()):
    for pref_l in POSTURES_ADDITIONAL_COMMAND_PREFIXES:
        POSTURES[ASL_STRING_SEPARATOR.join(pref_l+[posture_key])] = POSTURES[posture_key]

ANIMATION_ESTABLISH_TRUST = "establish_trust"
ANIMATION_YES_SIR = "yes_sir"
ANIMATION_FEAR = "fear"
ANIMATION_JOY = "joy"
ANIMATION_LOVE = "love"
ANIMATION_SADNESS = "sadness"
ANIMATION_SURPRISE = "surprise"
ANIMATION_LOOK_BOTTOM = "look_bottom"
ANIMATION_LOOK_BOTTOM_LEFT = "look_bottom_left"
ANIMATION_LOOK_BOTTOM_RIGHT = "look_bottom_right"
ANIMATION_LOOK_LEFT = "look_left"
ANIMATION_LOOK_RIGHT = "look_right"
ANIMATION_LOOK_TOP = "look_top"
ANIMATION_LOOK_TOP_LEFT = "look_top_left"
ANIMATION_LOOK_TOP_RIGHT = "look_top_right"
ANIMATION_DANCE = "dance"


ANIMATIONS = {ASL_STRING_SEPARATOR.join(["play", "yes", "sir"]): ANIMATION_YES_SIR,
              ASL_STRING_SEPARATOR.join(["play", "establish", "trust"]): ANIMATION_ESTABLISH_TRUST,
              ASL_STRING_SEPARATOR.join(["play", "fear"]): ANIMATION_FEAR,
              ASL_STRING_SEPARATOR.join(["play", "joy"]): ANIMATION_JOY,
              ASL_STRING_SEPARATOR.join(["play", "love"]): ANIMATION_LOVE,
              ASL_STRING_SEPARATOR.join(["play", "sadness"]): ANIMATION_SADNESS,
              ASL_STRING_SEPARATOR.join(["play", "surprise"]): ANIMATION_SURPRISE,
              ASL_STRING_SEPARATOR.join(["look", "bottom"]): ANIMATION_LOOK_BOTTOM,
              ASL_STRING_SEPARATOR.join(["look", "down"]): ANIMATION_LOOK_BOTTOM,
              ASL_STRING_SEPARATOR.join(["look", "bottom", "left"]): ANIMATION_LOOK_BOTTOM_LEFT,
              ASL_STRING_SEPARATOR.join(["look", "bottom", "right"]): ANIMATION_LOOK_BOTTOM_RIGHT,
              ASL_STRING_SEPARATOR.join(["look", "left"]): ANIMATION_LOOK_LEFT,
              ASL_STRING_SEPARATOR.join(["look", "right"]): ANIMATION_LOOK_RIGHT,
              ASL_STRING_SEPARATOR.join(["look", "top"]): ANIMATION_LOOK_TOP,
              ASL_STRING_SEPARATOR.join(["look", "up"]): ANIMATION_LOOK_TOP,
              ASL_STRING_SEPARATOR.join(["look", "top", "left"]): ANIMATION_LOOK_TOP_LEFT,
              ASL_STRING_SEPARATOR.join(["look", "top", "right"]): ANIMATION_LOOK_TOP_RIGHT,
              "dance": ANIMATION_DANCE
              }

ANIMATION_ADDITIONAL_COMMAND_PREFIXES = [["can", "you"], ["do", "you", "know", "how", "to"]]
for animation_key in list(ANIMATIONS.keys()):
    for pref_l in ANIMATION_ADDITIONAL_COMMAND_PREFIXES:
        ANIMATIONS[ASL_STRING_SEPARATOR.join(pref_l+[animation_key])] = ANIMATIONS[animation_key]

FS_TRIANGULAR_MF = "triangular_mf"
FS_TRAPEZOIDAL_MF = "trapezoidal_mf"
FS_GAUSSIAN_MF = "gaussian_mf"

FS_POSITIVE_INTERPRETATION_VALUES = ["hpc", "vhpc", "appc", "ppc",
                                     "high"]  # todo note "high" should be removed and this should also be checked in general conceptually

NSGA2 = "NSGA2"
RNSGA2 = "RNSGA2"
NSGA3 = "NSGA3"
UNSGA3 = "UNSGA3"
GA = "GA"
DE = "DE"

PHI_INTERPRETABILITY_INDEX = "PHI"
AVG_COVERAGE_INDEX = "COVERAGE"

BDI_CORE_NAME = "nosar_bdicore"
BDI_CORE_JID = "nosar_bdicore@localhost"
BDI_CORE_PWD = "nosar_bdicore"
CHATTER_NAME = "nosar_chatter"
CHATTER_JID = "nosar_chatter@localhost"
CHATTER_PWD = "nosar_chatter"
DATA_COLLECTOR_NAME = "nosar_data_collector"
DATA_COLLECTOR_JID = "nosar_data_collector@localhost"
DATA_COLLECTOR_PWD = "nosar_data_collector"
SYSTEM_HANDLER_NAME = "nosar_system_handler"
SYSTEM_HANDLER_JID = "nosar_system_handler@localhost"
SYSTEM_HANDLER_PWD = "nosar_system_handler"
POSITION_HANDLER_NAME = "nosar_position_handler"
POSITION_HANDLER_JID = "nosar_position_handler@localhost"
POSITION_HANDLER_PWD = "nosar_position_handler"
VISION_HANDLER_NAME = "nosar_vision_handler"
VISION_HANDLER_JID = "nosar_vision_handler@localhost"
VISION_HANDLER_PWD = "nosar_vision_handler"
POSTURE_HANDLER_NAME = "nosar_posture_handler"
POSTURE_HANDLER_JID = "nosar_posture_handler@localhost"
POSTURE_HANDLER_PWD = "nosar_posture_handler"
NORM_ADAPTER_NAME = "nosar_norm_adapter"
NORM_ADAPTER_JID = "nosar_norm_adapter@localhost"
NORM_ADAPTER_PWD = "nosar_norm_adapter"

XMPP_AGENTS_DETAILS = {
    BDI_CORE_NAME: {"jid": BDI_CORE_JID, "pwd": BDI_CORE_PWD, },
    CHATTER_NAME: {"jid": CHATTER_JID, "pwd": CHATTER_PWD},
    DATA_COLLECTOR_NAME: {"jid": BDI_CORE_JID, "pwd": BDI_CORE_PWD},
    SYSTEM_HANDLER_NAME: {"jid": SYSTEM_HANDLER_JID, "pwd": SYSTEM_HANDLER_PWD},
    POSITION_HANDLER_NAME: {"jid": POSITION_HANDLER_JID, "pwd": POSITION_HANDLER_PWD},
    VISION_HANDLER_NAME: {"jid": VISION_HANDLER_JID, "pwd": VISION_HANDLER_PWD},
    POSTURE_HANDLER_NAME: {"jid": POSTURE_HANDLER_JID, "pwd": POSTURE_HANDLER_PWD},
    NORM_ADAPTER_NAME: {"jid": NORM_ADAPTER_JID, "pwd": NORM_ADAPTER_PWD}
}

ROBOT_NAME = "Nao"
