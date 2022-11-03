import random

import requests


def getRandomNewsFromBBC():
    choice = "the weather today"
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
        article = open_bbc_page["articles"]

        # empty list which will
        # contain all trending news
        results = []

        for ar in article:
            results.append(ar["title"])

        # print(results)

        choice = random.choice(results)
        # print(choice)
    except:
        choice = "the weather today"

    return choice
