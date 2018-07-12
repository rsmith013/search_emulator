# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from elasticsearch import Elasticsearch

es = Elasticsearch([{"host": "jasmin-es1.ceda.ac.uk", "port": 9000}])


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
                results["suggested_results"] = [
                    {"title": get_title("dbd451271eb04662beade68da43546e1"),
                     "uuid": uuid,
                     "probability": 50}]

    return render(request, 'search/search.html', context=results)
