import re


def get_username(email_address):
    match = re.match(r'([^@]+)@example\.com', email_address)
    return match.group(1)


class Foo(object):
    __slots__ = (1, 2, 3)

    def error(self):
        x = {}
        y = x["y"]
        return y
