import random

import requests

import logging
logger = logging.getLogger("sonar.mas.utils.news")

def getRandomNewsFromBBC():
    ret_choice = "today"
    ret_descr = "I think it's a nice day"
    try:
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
        articles = open_bbc_page["articles"]

        # # empty list which will
        # # contain all trending news
        # results = []
        # results_descr =
        #
        # for ar in article:
        #     results.append(ar["title"])

        # print(results)
        article = random.choice(articles)
        ret_choice = article["title"]
        ret_descr = article["description"]
        # print(choice)
    except:
        return ret_choice, ret_descr

    return ret_choice, ret_descr
