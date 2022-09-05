from spade.message import Message
import utils.constants as Constants

def prepareMessage(received_jid, performative, msg_body):
    msg = Message(received_jid)  # Instantiate the message
    msg.set_metadata("performative", performative)  # Set the "inform" FIPA performative
    if isinstance(msg_body, str):
        msg.body = msg_body
    elif isinstance(msg_body, list):
        msg.body = joinStrings(msg_body)
    return msg

def splitStringToList(str_to_split):
    return str_to_split.split(Constants.STRING_SEPARATOR)

def joinStrings(list_to_join):
    return Constants.STRING_SEPARATOR.join(list_to_join)

def splitStringBelToList(str_to_split):
    return str_to_split.split(Constants.BEL_STRING_SEPARATOR)

def joinStringsBel(list_to_join):
    return Constants.BEL_STRING_SEPARATOR.join(list_to_join)


def getStringFromJID(JID):
    return JID.localpart + "@" + JID.domain