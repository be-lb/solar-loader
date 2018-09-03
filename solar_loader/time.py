from datetime import datetime, timedelta
from django.conf import settings
from pytz import timezone, utc

brussels_zone = timezone('Europe/Brussels')


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