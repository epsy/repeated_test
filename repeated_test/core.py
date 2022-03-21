# repeated_test -- A framework for repeating a test over many values
# Copyright (C) 2011-2022 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

import itertools
import sys
import traceback
import unittest

import six
import collections

from repeated_test.utils import options


__unittest = True # hides frames from this file from unittest output


class FixturesDict(collections.abc.MutableMapping):
    def __init__(self, *args, **kwargs):
        self.d = {}
        self.lines = {}
        super(FixturesDict, self).__init__(*args, **kwargs)

    def __iter__(self):
        return iter(self.d)

    def __len__(self):
        return len(self.d)

    def __setitem__(self, key, value):
        if key in self.d and (not key.startswith('_') or key == '_test'):
            raise ValueError("Fixture already present: " + key)
        else:
            if key.startswith('test_'):
                if key[5:] in self.d:
                    raise ValueError(
                        "Plain test conflicts with fixture: " + key)
            elif not key.startswith('_'):
                if 'test_' + key in self.d:
                    raise ValueError(
                        "Fixture conflicts with plain test: " + key)
        self.lines[key] = traceback.extract_stack(sys._getframe(1), 1)[0][:3]
        self.d[key] = value

    def __getitem__(self, key):
        return self.d[key]

    def __delitem__(self, key):
        del self.d[key]


OPTIONS_MATRIX_KEY = '_repeated_test__options_matrix'


def find_member_in_bases(bases, key, default):
    for base in bases:
        for cls in base.__mro__:
            if key in cls.__dict__:
                return cls.__dict__[key]
    return default


class FixturesMeta(type):
    @classmethod
    def __prepare__(cls, name, bases, TestCase=None):
        ret = FixturesDict()
        if TestCase is not None:
            ret['_TestCase'] = TestCase
        return ret

    def __new__(meta, name, bases, d, TestCase=None):
        container_loc = traceback.extract_stack(sys._getframe(1), 2)[0][:3]
        TestCase = d.get('_TestCase', TestCase or unittest.TestCase)
        members = dict(d.d)
        for key, value in d.d.items():
            if not key.startswith('test_') and not key.startswith('_'):
                members['test_' + key] = _make_testfunc_runner(
                    value, d.lines.get(key), container_loc, name, key)
        bases = tuple(b for b in bases if b is not object)
        if '_test' not in members:
            raise ValueError("'_test' function missing from Fixtures class")
        if members['_test'] is not None:
            bases = bases + (TestCase,)
        members['_repeated_test__lines'] = d.lines
        members['_TestCase'] = TestCase
        options_matrix_in_base = find_member_in_bases(bases, OPTIONS_MATRIX_KEY, {})
        options_matrix = members.get(OPTIONS_MATRIX_KEY, {})
        members[OPTIONS_MATRIX_KEY] = {
            **options_matrix_in_base,
            **options_matrix,
        }
        return super(FixturesMeta, meta).__new__(meta, name, bases, members)

    def __init__(self, *args, **kwargs):
        kwargs.pop('TestCase', None)
        super(FixturesMeta, self).__init__(*args, **kwargs)

    def update(cls, *, func=None, options_matrix=None):
        meta = type(cls)
        tc_cls = (cls._TestCase,) if cls.__dict__['_test'] is None else ()
        bases = tuple(b for b in cls.__bases__ if b is not object) + tc_cls
        members = dict(cls.__dict__)
        func = func or members.get('_test', None)
        members['_test'] = func
        name = func.__name__ if func else cls.__name__
        original_options_matrix = members.get(OPTIONS_MATRIX_KEY, {})
        options_matrix = {
            **original_options_matrix,
            **(options_matrix or {}),
        }
        members[OPTIONS_MATRIX_KEY] = options_matrix
        return super(FixturesMeta, meta).__new__(
            meta, name, bases, members)

    def with_test(cls, func):
        return cls.update(func = func)

    def with_options_matrix(cls, **options_matrix):
        return cls.update(options_matrix=options_matrix)


class Fixtures(metaclass=FixturesMeta):
    _test = None


def WithTestClass(cls):
    class metaclass(FixturesMeta):
        def __new__(cls_, name, bases, d):
            return FixturesMeta(name, (), d, TestCase=cls)
    return type.__new__(metaclass, "WithTestClass_"+cls.__name__, (), {})


def _make_testfunc_runner(value, fake_loc,
                          container_loc, cls_name, member_name):
    def _run_test_matrix(self):
        matrix = getattr(self, OPTIONS_MATRIX_KEY)
        args, kwargs = options.split_into_args_kwargs(value)

        combo_source = (
            (lambda key: ((key, value) for value in values))(latest_key)
            for latest_key, values in matrix.items()
            if latest_key not in kwargs
        )

        product = itertools.product(*combo_source)

        first_two = list(itertools.islice(product, 2))

        if len(first_two) == 0:
            raise ValueError("Some options have no values")
        if len(first_two) == 1:
            return _run_test(self, args, dict(
                first_two[0] or {},
                **kwargs,
            ))
        else:
            for kv_pairs in itertools.chain(first_two, product):
                combination = dict(kv_pairs)
                with self.subTest(**combination):
                    _run_test(self, args, {
                        **combination,
                        **kwargs,
                    })

    def _run_test(self, args, kwargs):
        try:
            return self._test(*args, **kwargs)
        except Exception as exc:
            typ, exc, tb = sys.exc_info()
            _raise_at_custom_line(*fake_loc)(typ, exc, tb.tb_next)

    return _run_test_matrix


def _raise_at_custom_line(filename, lineno, funcname):
    funcname = funcname.strip('<>')
    d = {}
    six.exec_(compile(_make_raiser(lineno, funcname), filename, 'exec'), d)
    ret = d[funcname]
    return ret


def _make_raiser(lineno, funcname):
    padding = '\n'*(lineno-1) + 'def '+funcname+'(typ, exc, tb):'
    return padding+'raise exc.with_traceback(tb)'
