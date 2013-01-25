import os


def load_fixture(filename):
    path = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(path, 'fixtures', filename)
    fh = open(filename, 'r')
    return fh.read()
