import sys
import re
import traceback
import unittest

import six
import collections


try:
    abc = collections.abc
except AttributeError:
    abc = collections


__unittest = True # hides frames from this file from unittest output


class FixturesDict(abc.MutableMapping):
    def __init__(self, *args, **kwargs):
        self.d = {}
        self.lines = {}
        super(FixturesDict, self).__init__(*args, **kwargs)

    def __iter__(self):
        return iter(self.d)

    def __len__(self):
        return len(self.d)

    def __setitem__(self, key, value):
        if key in self.d:
            raise ValueError("Fixture already present: " + key)
        self.lines[key] = traceback.extract_stack(sys._getframe(1), 1)[0][:3]
        self.d[key] = value

    def __getitem__(self, key):
        return self.d[key]

    def __delitem__(self, key):
        del self.d[key]


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
        try: # py3
            orig = d.d
            lines = d.lines
        except AttributeError: # py2: No custom class dict
            orig = d
            lines = {}
        members = dict(orig)
        for key, value in orig.items():
            if not key.startswith('test_') and not key.startswith('_'):
                members['test_' + key] = _make_testfunc_runner(
                    value, lines.get(key), container_loc, name, key)
        bases = tuple(b for b in bases if b is not object)
        if '_test' in members:
            bases = bases + (TestCase,)
        members['_repeated_test__lines'] = lines
        members['_TestCase'] = TestCase
        return super(FixturesMeta, meta).__new__(meta, name, bases, members)

    def __init__(self, *args, **kwargs):
        kwargs.pop('TestCase', None)
        super(FixturesMeta, self).__init__(*args, **kwargs)

    def with_test(cls, func):
        meta = type(cls)
        tc_cls = (cls._TestCase,) if '_test' not in cls.__dict__ else ()
        bases = tuple(b for b in cls.__bases__ if b is not object) + tc_cls
        members = dict(cls.__dict__)
        members['_test'] = func
        return super(FixturesMeta, meta).__new__(
            meta, func.__name__, bases, members)


Fixtures = six.with_metaclass(FixturesMeta)


def WithTestClass(cls):
    class metaclass(type):
        def __new__(cls_, name, this_bases, d):
            return FixturesMeta(name, (), d, TestCase=cls)
    return type.__new__(metaclass, "WithTestClass_"+cls.__name__, (), {})


def _make_testfunc_runner(value, fake_loc,
                          container_loc, cls_name, member_name):
    def _run_test(self):
        try:
            return self._test(*value)
        except Exception as exc:
            typ, exc, tb = sys.exc_info()
            _raise_at_custom_line(
                *get_loc(fake_loc, container_loc, cls_name, member_name)
                )(typ, exc, tb.tb_next)
    return _run_test


def get_loc(fake_loc, cls_loc, cls_name, member_name):
    if fake_loc is not None:
        return fake_loc
    cls_filename, cls_lineno, cls_funcname = cls_loc
    lines = list(open(cls_filename))
    pat = re.compile(r"^\s*" + re.escape(member_name) + "\s*=")
    for i, line in enumerate(lines[cls_lineno:], cls_lineno+1):
        if pat.match(line):
            return cls_filename, i, cls_name
    else:
        return cls_loc


def _raise_at_custom_line(filename, lineno, funcname):
    d = {}
    six.exec_(compile(_make_raiser(lineno, funcname), filename, 'exec'), d)
    return d[funcname]


def _make_raiser(lineno, funcname):
    padding = '\n'*(lineno-1) + 'def '+funcname+'(typ, exc, tb):'
    if sys.version_info < (3,):
        return (
            padding + 'other(typ, exc, tb)\n'
            'def other(typ, exc, tb):raise typ, exc, tb')
    else:
        return padding+'raise exc.with_traceback(tb)'
