from datetime import datetime, timedelta
from django.conf import settings
from pytz import timezone, utc
from time import perf_counter
from collections import deque, namedtuple
import numpy as np

brussels_zone = timezone('Europe/Brussels')

times_queue = deque()
Timed = namedtuple('Timed', ['counter', 't'])


class TimeCounter:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.start = perf_counter()

    def __exit__(self, *args):
        times_queue.append(Timed(self.name, perf_counter() - self.start))


def start_counter():
    times_queue.clear()


def summarize_times():
    keys = []
    for ct in times_queue:
        if ct.counter not in keys:
            keys.append(ct.counter)

    for k in sorted(keys):
        values = list(
            map(lambda x: x.t, filter(lambda x: x.counter == k, times_queue)))
        n = len(values)
        t = np.sum(values)
        print('Time spent in {}: n = {}, t = {:.2f} s, t/n = {:.2f} ms'.format(
            k, n, t, (t / float(n)) * 1000.0))


def time_range(start, interval, n):
    for i in range(n):
        yield start + (interval * i)


def hours_for_year(year):
    start = datetime(year, 1, 1, 0, 0, 0, 0, brussels_zone)
    d = timedelta(hours=1)
    return time_range(start, d, 365 * 24)


def get_days(start_month, start_day, interval, n):
    start = datetime(
        datetime.now(brussels_zone).year, start_month, start_day, 0, 0, 0, 0,
        brussels_zone)
    d = timedelta(hours=1)
    days = []
    for t in time_range(start, interval, n):
        days.append([t + (d * i) for i in range(24)])
    return days


def generate_sample_days(sample_rate):
    sample_rate = 365 / sample_rate
    days = get_days(3, 21, timedelta(days=sample_rate), int(sample_rate))
    return days


def generate_sample_times(sample_rate):
    for day in generate_sample_days(sample_rate):
        for tim in day:
            yield tim