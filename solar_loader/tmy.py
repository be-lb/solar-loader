import csv
import numpy as np
from datetime import timedelta
from pytz import timezone, utc

brussels_zone = timezone('Europe/Brussels')
central_europe_zone = timezone('CET')


def make_key(t):
    # lt = t.astimezone(brussels_zone)
    lt = t.astimezone(central_europe_zone)
    if 0 == lt.hour:
        lt = lt - timedelta(days=1)
        m, d, h = (
            lt.month,
            lt.day,
            24,
        )
    else:
        m, d, h = (
            lt.month,
            lt.day,
            lt.hour,
        )

    return '{}-{}-{}'.format(m, d, h)


def time_range(start, interval, n):
    return [start + (interval * i) for i in range(n)]


class TMY:
    def __init__(self, tmy_path):
        self.rows = dict()
        self.reverse_index = dict()
        with open(tmy_path) as f:
            for i, row in enumerate(csv.DictReader(f, delimiter=',')):
                if i == 0:
                    print(row.keys())
                # k = '{}-{}-{}'.format(row['Month'], row['Day'], row['Hour'])
                k = '{}-{}-{}'.format(row['m'], row['dm'], row['h'])
                self.rows[k] = row
                self.reverse_index[k] = i

    def row(self, t):
        return self.rows[make_key(t)]

    def get_value(self, key, t, fn=None):
        val = self.row(t)[key]
        if fn is not None:
            return fn(val)
        return val

    def get_float(self, key, t):
        return self.get_value(key, t, lambda x: float(x))

    def get_float_average(self, key, t, sample_rate):
        sr = int(sample_rate)
        start = t - timedelta(days=sr // 2)
        ref = self.get_float(key, t)
        values = []

        for st in time_range(start, timedelta(days=1), sr):
            values.append(self.get_float(key, st))

        avg = np.mean(values)
        # print('{}({}) => {} {}'.format(key, sample_rate, ref, avg))
        return avg

    def get_index(self, t):
        return self.reverse_index[make_key(t)]
