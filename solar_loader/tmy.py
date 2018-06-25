import csv


def make_key(t):
    m, d, h = (
        t.month,
        t.day,
        t.hour,
    )
    return '{}-{}-{}'.format(m, d, h + 1)


class TMY:
    def __init__(self, tmy_path):
        self.rows = dict()
        self.reverse_index = dict()
        with open(tmy_path) as f:
            for i, row in enumerate(csv.DictReader(f, delimiter=';')):
                k = '{}-{}-{}'.format(row['Month'], row['Day'], row['Hour'])
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

    def get_index(self, t):
        return self.reverse_index[make_key(t)]
