from pathlib import Path
from time import perf_counter
from psycopg2.extensions import AsIs
import numpy as np
from munch import munchify
import logging

from django.db import connections
from django.conf import settings

logger = logging.getLogger(__name__)


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


def format_q(q, args):
    if len(args) > 0:
        arg = args[0]
        t = type(arg)

        if t == str:
            arg = '{}'.format(arg)
        elif t == bytes:
            arg = '{}'.format(arg)
        elif t == AsIs:
            arg = arg.getquoted().decode()

        return format_q(q.replace('%s', str(arg)), args[1:])
        # try:
        # except Exception as ex:
        #     print('format_q: {} {}'.format(q, arg))
        #     raise ex
    return q


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

    def exec(self, query_name, args=()):
        conn = connections[self._cn]
        with conn.cursor() as cur:
            cur.execute(self.find_query(query_name), args)

    def rows(self, query_name, safe_params={}, args=()):
        logger.debug('SQL({}) on {}'.format(query_name, self._cn))
        conn = connections[self._cn]
        try:
            with conn.cursor() as cur:
                q = self.find_query(query_name)
                start_time = perf_counter()
                for k in safe_params:
                    q = q.replace('__{}__'.format(k), safe_params[k])
                # print('+++++ SQL({}) ++++++++++++++++++++'.format(query_name))
                # print(format_q(q, args))
                cur.execute(q, args)
                self._times.append(perf_counter() - start_time)
                for row in cur:
                    yield row
        except Exception as ex:
            logger.error(
                'Error:DB:rows({})\n {} \n========================\n{}'.format(
                    query_name, format_q(q, args), ex))

    def total_exec(self):
        return len(self._times)

    def total_time(self):
        return np.sum(self._times)

    def mean_time(self):
        return np.mean(self._times)
