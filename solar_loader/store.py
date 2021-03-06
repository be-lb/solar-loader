from pathlib import Path
from time import perf_counter
from psycopg2.extensions import AsIs
import numpy as np
from munch import munchify
import logging
from uuid import uuid4

from django.db import connections
import random

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
            arg = "'{}'".format(arg)
        elif t == bytes:
            arg = "'{}'".format(arg)
        elif t == AsIs:
            arg = arg.getquoted().decode()

        nq = q.replace('%s', str(arg), 1)
        # print('NQ({})'.format(nq))
        return format_q(nq, args[1:])
        # try:
        # except Exception as ex:
        #     print('format_q: {} {}'.format(q, arg))
        #     raise ex
    return q


class Data:
    def __init__(self, connection_name, tables, reset=False):
        if isinstance(connection_name, str):
            self._cn = [connection_name]
        else:
            self._cn = connection_name

        self._queries = list(make_queries(tables))
        self._times = []
        self._store_id = uuid4()

        if reset:
            for cn in self._cn:
                c = connections[cn]
                c.close()

    def get_connection(self):
        return connections[random.choice(self._cn)]

    def find_query(self, query_name):
        for name, query in self._queries:
            if name == query_name:
                return query
        raise QueryNotFound(query_name)

    def explain(self, query_name, args=()):
        q = self.find_query(query_name)
        return format_q(q, args)

    def exec(self, query_name, args=()):
        conn = self.get_connection()
        # print('SQL({}): {}'.format(self._store_id, query_name))
        with conn.cursor() as cur:
            cur.execute(self.find_query(query_name), args)

    def rows(self, query_name, safe_params={}, args=()):
        # print('SQL({}): {}'.format(self._store_id, query_name))
        conn = self.get_connection()
        q = self.find_query(query_name)
        try:
            with conn.cursor() as cur:
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
            logger.error("""
Error:DB:rows({})
{}
========================
{}
========================
""".format(query_name, ex, format_q(q, args)))

    def total_exec(self):
        return len(self._times)

    def total_time(self):
        return np.sum(self._times)

    def mean_time(self):
        return np.mean(self._times)
