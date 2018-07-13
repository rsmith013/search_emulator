# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from elasticsearch import Elasticsearch
from sklearn.externals import joblib
import json
import os
import numpy as n
from catalogue_sim.settings import BASE_DIR

es = Elasticsearch([{"host": "jasmin-es1.ceda.ac.uk", "port": 9000}])
model_file = os.path.join(BASE_DIR, "search", "model.json")
terms_file = os.path.join(BASE_DIR, "search", "learning_terms.json")

with open(terms_file) as input:
    terms_data = json.load(input)
    unique_terms = terms_data['training_set']
    output = terms_data['output']

clf = joblib.load(model_file)



def get_title(uuid):

    """
        Query elasticsearch for the title of the specified document by uuid
    
        :param uuid: uuid to query
        :return: Title of document. Returns unknown if no results.
        """
    body = {
        "_source": "title",
        "query": {
            "term": {
                "uuid": uuid
            }
        }
    }
    res = es.search(index="cedamoles-haystack-prod", body=body)

    if res["hits"]["total"] == 1:
        title = res["hits"]["hits"][0]["_source"]["title"]
    else:
        title = "unknown"
    return title

def find_probabilities(search_query):
    search = search_query
    bag2 = []
    for word in unique_terms:
        if word in search:
            bag2.append(1)
        else:
            bag2.append(0)
    bag2 = n.array(bag2).reshape(1, -1)
    predicted = clf.predict_proba(bag2)
    sorted_probabilitys = sorted(predicted[0], reverse=True)

    probabilities = []
    for i in sorted_probabilitys[0:3]:
        record = (output[int(n.where(predicted[0] == i)[0])])
        probabilities.append ({"title": get_title(record),
                               "uuid": record,
                               "probability": int(i *100)})
    return probabilities

print (find_probabilities("rainfall"))
# Create your views here.

def home(request):
    results = {}
    if request.GET:
        search_query = request.GET['q']
        if search_query:

            body = {
                "query": {
                    "match": {
                        "text": search_query
                    }
                }
            }

            res = es.search(index="cedamoles-haystack-prod", body=body)

            total_results = res['hits']['total']
            if total_results > 0:
                res_hits = res['hits']['hits']

                titles = [hit["_source"]['title'] for hit in res_hits]
                uuids = [hit["_source"]['uuid'] for hit in res_hits]

                record_list = []
                for title, uuid in zip(titles, uuids):
                    record_list.append({"title": title, "uuid": uuid})

                results["records"] = record_list
                results["count"] = total_results
                results["uuid"] = [hit["_source"]['uuid'] for hit in res_hits]

                uuid = "dbd451271eb04662beade68da43546e1"
                results["suggested_results"] = find_probabilities(search_query)

    return render(request, 'search/search.html', context=results)
