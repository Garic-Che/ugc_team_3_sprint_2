import time

from elasticsearch import Elasticsearch
import backoff

from helpers import ElasticsearchSettings

@backoff.on_exception(backoff.expo,exception=ValueError,max_time=60)
def is_pinging(client: Elasticsearch):
    if not client.ping():
        raise ValueError("Connection failed")

if __name__ == "__main__":
    es_settings = ElasticsearchSettings()
    es_client = Elasticsearch(hosts=es_settings.get_host(), verify_certs=False)
    is_pinging(es_client)
