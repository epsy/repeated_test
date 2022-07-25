def evaluated(func):
    """Marks func as to-be-evaluated before obtaining the tuple used with the ``_test`` function"""
    return Evaluated(func)


def flatten_evaluated_items(self, args, kwargs):
    for item in args:
        if isinstance(item, Evaluated):
            yield from flatten_evaluated_items(self, item.func(self, **kwargs), kwargs)
        else:
            yield item


class Evaluated:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __repr__(self):
        return f'repeated_test.evaluated({self.func!r})'
