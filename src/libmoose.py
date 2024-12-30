#!/usr/bin/python3
import json
import logging
import sys
from typing import List, Optional, Union
import yaml

import requests
import elasticsearch
import elasticsearch.helpers

class utils:
    def load_config(config_path: str) -> dict:
        with open(config_path, 'r') as file:
            config = yaml.load(file, Loader=yaml.BaseLoader)
        return config

class moose_es:
    """ some wrappers around elasticsearch-py """
    def __init__(self, config: str, timeout: float = 120.0) -> None:
        self.config = config
        self.timeout = timeout
        self.client = self.get_client()

    def get_client(self) -> elasticsearch.client.Elasticsearch:
        es_hosts = self.config['es_nodes']
        username = self.config['username']
        password = self.config['password']
        es = elasticsearch.Elasticsearch(
            hosts=es_hosts,
            http_auth=(username, password),
            timeout=self.timeout
        )
        return es

    #def get_async_client(self) -> elasticsearch.client.AsyncElasticsearch:
    #    es_hosts = self.config['es_nodes']
    #    username = self.config['username']
    #    password = self.config['password']
    #    es = elasticsearch.Elasticsearch(
    #        hosts=es_hosts,
    #        http_auth=(username, password),
    #        timeout=self.timeout
    #    )
    #    return es

    def format_doc(self, doc):
        if args.full_docs:
            final_doc = doc
        else:
            final_doc = doc['_source']
        if args.format == 'json':
            msg = json.dumps(final_doc)
        elif args.format == 'txt':
            msg = '{0} {1} {2}'.format(
                    doc['_source']['@timestamp'],
                    doc['_source']['host']['name'],
                    doc['_source']['message']
                   )
        return msg

    def sql_query(self,
                 query: str,
                 return_format: List[Union['txt', 'json']] = 'json'):
        """ run an SQL query and print the results """
        query = {
            'query': query
        }
        sql = elasticsearch.client.SqlClient(self.client)
        results = sql.query(body=query, params={'format': return_format}, request_timeout=self.timeout)
        return results

    def count(self, index: str, query: dict):
        result = self.client.count(body=query,
                                   index=index,
                                   request_timeout=self.timeout)
        return result

    def aggregation(self, index: str, query: dict):
        result = self.client.search(body=query,
                                    index=index,
                                    request_timeout=self.timeout,
                                    filter_path=['aggregations'])
        return result

    def get_scroller(self,
                 index: str,
                 query: dict,
                 scroll: str = '5m',
                 preserve_order: bool = True):
        """ Use helper. return generator to scroll through search results """
        scroller = elasticsearch.helpers.scan(
                        self.client,
                        query,
                        index=index,
                        scroll=scroll,
                        request_timeout=self.timeout,
                        preserve_order=preserve_order
                    )
        return scroller

    def get_custom_scroller(self,
                 index: str,
                 query: dict,
                 size: int = 10,
                 sort: Union[dict, str] = "_doc",
                 scroll: str = '1m'):
        """ return generator to scroll through search results """
        response = self.client.search(index=index, query=query, scroll='1m', sort=sort)
        scroll_id = response['_scroll_id']

        while scroll_id and response['hits']['hits']:
            for hit in response['hits']['hits']:
                yield hit
            response = self.client.scroll(scroll_id=scroll_id, scroll='1m')
            scroll_id = response.get('_scroll_id')

    def get_search_after(self, index: str, query: dict, preserve_order: bool = False):
        try:
            while True:
                response = es.search(index=args.index, query=query['query'], sort=query['sort'])
                hits = response["hits"]["hits"]

                if not hits:
                    break

                for hit in hits:
                    yield hit

                # get the sort values of the last document for the next "page" of
                last_sort = hits[-1]["sort"]
                query["search_after"] = last_sort
        finally:
            es.close()

class moose_es_admin:
    """ Shortcuts for managing elasticsearch """
    def __init__(self, config: dict):
        self.config = config
        self.host = config['es_nodes'][-1]
        self.username = config['username']
        self.password = config['password']

    def es(self,
           method: List[Union['GET', 'POST', 'PUT', 'DELETE']],
           endpoint: str,
           params: Optional[dict] = None,
           body: Optional[dict] = None) -> dict:
        """Send generic requests to Elasticsearch API."""
        es_url = self.host + endpoint
        if body:
            headers = {
                'Content-Type': 'application/json'
            }
        else:
            headers = None
        result = requests.request(method,
                                 es_url,
                                 headers=headers,
                                 auth=(self.username, self.password),
                                 params=params,
                                 json=body)
        return result

    def create_snapshot(self, repo, snapshot_name, indices, include_global_state):
        url = '/_snapshot/{}/{}'.format(repo, snapshot_name)
        req_body = {
            'indices': list(indices),
            'include_global_state': include_global_state,
            'metadata': {
                'taken_by': 'es_snapshot.py'
            }
        }
        return es('PUT', url, data=req_body)

    def alert_slack(error, hook_name):
        """Post message to slack."""
        hook_url = self.config['slack_hooks'][hook_name]
        message = {
            'text': "Moose: {}".format(error)
        }
        requests.request('POST', hook_url, json=message)

    def init_logger():
        """Log locally to /var/log/{script_name}.log."""
        script_name = sys.argv[0] \
            .split('/')[-1]
        logger = logging.getLogger(script_name)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z')
        handlers = [ logging.FileHandler('/var/log/{}.log'.format(script_name)),
                     logging.StreamHandler() ]
        for handle in handlers:
            handle.setFormatter(formatter)
            logger.addHandler(handle)
        return logger
