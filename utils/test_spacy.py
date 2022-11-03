import spacy
from spacytextblob.spacytextblob import SpacyTextBlob

nlp = spacy.load('en_core_web_sm')
nlp.add_pipe('spacytextblob')

from transformers import pipeline
classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

sentences = [
    "yes it is",
    "correct",
    "yes",
    "exactly",
    "no it's not",
    "nope",
    "not really",
    "that's not correct",
    "no it's not but never mind",
    "bravo",
    "not really but ok",
    "not really but also a little bit yes",
    "yes my name is Davie",
    "no it's not but that's a nice name"
]

def isYesNoUnclearAnswer(text):
    doc = nlp(text)
    evidence_positive = False
    evidence_negative = False
    for token in doc:
        if token.text in ["yes", "yeah", "correct", "exactly", "yep", "bravo", "ok"]:
            evidence_positive = True
        if token.text in ["no", "nope", "wrong", "not", "yep", "incorrect", "nu", "but"]:
            evidence_negative = True
    if evidence_positive and not evidence_negative:
        return "yes"
    elif evidence_negative and not evidence_positive:
        return "no"
    else:
        return "unclear"

print("Sentence\t\tSpacy\t\tTransformers\t\tRuleBased")
for s in sentences:
    doc = nlp(s)
    print("\t\t".join([s, str(doc._.blob.polarity), classifier(s)[0]["label"], isYesNoUnclearAnswer(s)]))



classifier2 = pipeline("text-classification", model='shahrukhx01/question-vs-statement-classifier')
print(classifier2("is this a question"))