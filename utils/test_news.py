# importing requests package
import requests

from transformers import pipeline, Conversation

from transformers.utils import logging


logging.set_verbosity(40) #errors


def NewsFromBBC():
    # BBC news api
    # following query parameters are used
    # source, sortBy and apiKey
    query_params = {
        "source": "bbc-news",
        "sortBy": "top",
        "apiKey": "815391c5e3c24f1f99772d347b69b10d"
    }
    main_url = " https://newsapi.org/v1/articles"

    # fetching data in json format
    res = requests.get(main_url, params=query_params)
    open_bbc_page = res.json()

    # getting all articles in a string article
    article = open_bbc_page["articles"]

    # empty list which will
    # contain all trending news
    results = []

    for ar in article:
        results.append(ar["title"])

    for i in range(len(results)):
        # printing all trending news
        print(i + 1, results[i])

    # to read the news out loud for us
    # from win32com.client import Dispatch
    # speak = Dispatch("SAPI.Spvoice")
    # speak.Speak(results)

    t2tpipeline = pipeline("text2text-generation", model="valhalla/t5-base-e2e-qg")
    for t in results:
        getTextFor(t2tpipeline, "generate questions", "You think about "+t)

def getTextFor(t2tpip, task, text):
    if task=="generate questions":
        r = t2tpip("generate questions : "+text,
                   max_length=20,
                   do_sample=True,
                 top_p=0.92,
                 top_k=100,
                 temperature=0.75
                   , num_return_sequences=10
                   )
        print("questions for ", text, ": ")
        for s in r:
            first = s['generated_text'].split("<sep>")[0]
            print(first)
        print("")
        return r[0]['generated_text'].split("<sep>")[0]
    return "ok"

# Driver Code
if __name__ == '__main__':
    # function call
    NewsFromBBC()