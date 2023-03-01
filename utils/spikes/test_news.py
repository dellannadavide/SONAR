# importing requests package
import random

import requests

from transformers import pipeline, Conversation

from transformers.utils import logging


logging.set_verbosity(40) #errors

summarizer_1 = pipeline("summarization")
qa_model = pipeline("question-answering", model="deepset/roberta-base-squad2", tokenizer="deepset/roberta-base-squad2")
t2tgenerator = pipeline("text2text-generation", model="valhalla/t5-base-e2e-qg")

print(qa_model(question="What did I say?", context="I said do you think you're free or do you think your servant"))
print(summarizer_1("You said do you think you're free or do you think your servant")[0][
                "summary_text"])

exit()

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
    # results = []
    # descr = []
    for ar in article:
        # results.append(ar["title"])
        # descr.append(ar["description"])
        news = ar["title"]+ ". " + ar["description"]
        print("News: "+news)

        # possible_questions_types = ["You think about ", "You've heard that "]
        # q_type = random.choice(possible_questions_types)

        generated_q = t2tgenerator("generate questions : "+ news,
                                        max_length=18,
                                        do_sample=True,
                                        top_p=0.92,
                                        top_k=100,
                                        temperature=0.75)
        question = "Anyways. "+ generated_q[0]['generated_text'].split("<sep>")[0]
        print("Question: "+question)

        answer = qa_model(question=question, context=news)
        print("Answer: "+str(answer))



    # summarizer_2 = pipeline("summarization", model="facebook/bart-large-cnn")
    # summarizer_3 = pipeline("summarization", model="t5-large")
    # for d in descr:
    #     print(d)
    #     print(summarizer_1(d, min_length=5, max_length=20)[0]["summary_text"])
    #     # print(summarizer_2(d, min_length=5, max_length=20)[0]["summary_text"])
    #     # print(summarizer_3(d, min_length=5, max_length=20)[0]["summary_text"])
    #         # print(summary))
    #
    # for i in range(len(results)):
    #     # printing all trending news
    #     print(i + 1, results[i])

    # to read the news out loud for us
    # from win32com.client import Dispatch
    # speak = Dispatch("SAPI.Spvoice")
    # speak.Speak(results)

    # t2tpipeline = pipeline("text2text-generation", model="valhalla/t5-base-e2e-qg")
    # for t in results:
    #     getTextFor(t2tpipeline, "generate questions", "You think about "+t)

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