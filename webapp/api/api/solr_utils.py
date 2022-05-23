import json
import logging
from typing import List

import requests
from django.http import HttpResponseServerError
from rest_framework.response import Response

from api.models import ConceptDB
from core.settings import SOLR_HOST, SOLR_PORT

SOLR_INDEX_SCHEMA = {}

logger = logging.getLogger(__name__)


def _cache_solr_collection_schema_types(collection):
    url = f'http://{SOLR_HOST}:{SOLR_PORT}/solr/{collection}/schema'
    logger.info(f'Retrieving solr schema: {url}')
    resp = json.loads(requests.get(url).text)
    cui_type = [n for n in resp['schema']['fields'] if n['name'] == 'cui'][0]['type']
    # just store cui type for the time being
    SOLR_INDEX_SCHEMA[collection] = {'cui': cui_type}


def collections_available(cdbs: List[int]):
    url = f'http://{SOLR_HOST}:{SOLR_PORT}/solr/admin/collections?action=LIST'
    resp = requests.get(url)
    if resp.status_code == 200:
        collections = json.loads(resp.text)['collections']
        # cache schema field types
        for col in collections:
            _cache_solr_collection_schema_types(col)
        current_collections_cdb_ids = [c.split('_id_')[-1] for c in collections]
        return Response({'results': {cdb_id: cdb_id in current_collections_cdb_ids for cdb_id in cdbs}})
    else:
        return HttpResponseServerError('Error requesting solr concept search collection list')


def search_collection(cdbs: List[int], query: str):
    query = query.strip().replace(r'\s+', r'\s').split(' ')
    if len(query) == 0:
        return Response({'results': []})
    query = [f'{query[i]}~1' if i < len(query) - 1 else f'{query[i]}*' for i in range(len(query))]

    res = []
    if len(cdbs) > 0:
        uniq_results_map = {}
        for cdb in cdbs:
            # TOOD: Consider making async
            cdb_model = ConceptDB.objects.get(id=cdb)
            collection_name = f'{cdb_model.name}_id_{cdb_model.id}'
            if collection_name not in SOLR_INDEX_SCHEMA:
                _cache_solr_collection_schema_types(collection_name)
            try:
                query_num = int(query[0][:-1])
                query_str = f'cui:{query_num}'
            except ValueError:
                if len(query) > 1:  # cannot be a cui if multi-word
                    query_str = ''.join([f' name:{q}' for q in query])
                elif SOLR_INDEX_SCHEMA[collection_name]['cui'] != 'plongs':  # single word could be alphanumeric cui
                    query_str = f'cui:{query[0][:-1]} OR name:{query[0][:-1]} OR name:{query[0]}'
                else:  # single word, numeric cui.
                    query_str = f'name:{query[0][:-1]} OR name:{query[0]}'

            solr_url = f'http://{SOLR_HOST}:{SOLR_PORT}/solr/{collection_name}/select?q.op=OR&q={query_str}&rows=15'
            logger.info(f'Searching solr collection: {solr_url}')
            resp = json.loads(requests.get(solr_url).text)
            if 'error' in resp:
                return HttpResponseServerError(f'Concept Search Index {collection_name} not available, '
                                               f'import concept DB first before trying to search it.')
            else:
                docs = [d for d in resp['response']['docs']]
                for d in docs:
                    if d['cui'][0] not in uniq_results_map:
                        uniq_results_map[d['cui'][0]] = {'cui': d['cui'][0], 'pretty_name': d['pretty_name'][0]}
        res = sorted(uniq_results_map.values(), key=lambda r: len(r['pretty_name']))
    return Response({'results': res})