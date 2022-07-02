# repeated_test -- A framework for repeating a test over many values
# Copyright (C) 2011-2022 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

from functools import partial

def _tup(args, func):
    return (func,) + args

def tup(*args):
    return partial(_tup, args)

class options:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

    __ACTIVE_OPTIONS = []

    @classmethod
    def split_into_args_kwargs(cls, args_and_options):
        args = []
        kwargs = {}
        for arg in args_and_options:
            if isinstance(arg, cls):
                kwargs.update(arg.kwargs)
            else:
                args.append(arg)
        return args, kwargs

    @classmethod
    def get_active_options(cls):
        return tuple(cls.__ACTIVE_OPTIONS)

    def __enter__(self):
        type(self).__ACTIVE_OPTIONS.append(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        type(self).__ACTIVE_OPTIONS.pop()

class _SkipOption:
    def __repr__(self):
        return "<skip option>"

skip_option = _SkipOption()

def with_options(**kwargs):
    return with_options_matrix(**{
        key: [value]
        for key, value in kwargs.items()
    })

def with_options_matrix(**kwargs):
    def wrap_class(cls):
        return cls.update(options_matrix=kwargs)
    return wrap_class

def filter_skips(d):
    return {
        k: v
        for k, v in d.items()
        if v is not skip_option
    }
