from pathlib import Path
from time import perf_counter
import numpy as np
from munch import munchify

from django.db import connections
from django.conf import settings


def make_queries(tables):
    sql_dir = Path(__file__).parent.joinpath('sql')
    tables_config = munchify(tables)
    for sql_path in sql_dir.glob('*.sql'):
        query_name = sql_path.stem
        with open(sql_path.as_posix()) as tpf:
            tpl = tpf.read()
            query = tpl.format(**tables_config)
            yield (
                query_name,
                query,
            )


class QueryNotFound(Exception):
    def __init__(self, expression):
        self.expression = expression
        self.message = 'Query "{}" Not Found'.format(expression)


class Data:
    def __init__(self, connection_name, tables):
        self._cn = connection_name
        self._queries = list(make_queries(tables))
        self._times = []

    def find_query(self, query_name):
        for name, query in self._queries:
            if name == query_name:
                return query
        raise QueryNotFound(query_name)

    def rows(self, query_name, *args):
        conn = connections[self._cn]
        try:
            with conn.cursor() as cur:
                q = self.find_query(query_name)
                if settings.DEBUG:
                    print('>> SQL({}) on {}'.format(query_name, self._cn))
                    print(q, args)
                start_time = perf_counter()
                cur.execute(q, *args)
                self._times.append(perf_counter() - start_time)
                for row in cur:
                    yield row
        except Exception as ex:
            print('Error:DB:rows({}) \n{}'.format(query_name, ex))

    def total_exec(self):
        return len(self._times)

    def total_time(self):
        return np.sum(self._times)

    def mean_time(self):
        return np.mean(self._times)