# repeated_test -- A framework for repeating a test over many values
# Copyright (C) 2011-2022 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

import sys
import inspect
from types import TracebackType
from typing import Optional
import unittest


from repeated_test import Fixtures, WithTestClass, tup, core, options


skip_noprepare = unittest.skipIf(
    sys.version_info < (3,),
    "Py version lacks custom class dict support")


def get_tb_funcs_lines(tb: Optional[TracebackType]):
    tb_funcs = []
    tb_lines = []
    while tb is not None:
        fi = inspect.getframeinfo(tb)
        tb_funcs.append(fi.function)
        tb_lines.append(fi.code_context)
        tb = tb.tb_next
    return tb_funcs, tb_lines


class RepeatedTestTests(unittest.TestCase):
    def setUp(self):
        class sum_tests(Fixtures):
            def _test(self, total, *terms, optional=0):
                self.assertEqual(total, sum(terms) + optional)
            a = 3, 2, 1
            b = 6, 3, 2, 1
            c = 15, 5, 3
            d = 4, 2, 2
            optional_success = 6, 3, 2, options(optional=1)
            optional_failure = 1, 3, 2, options(optional=1)
            optional_badargs = 3, 2, 1, options(doesntexist=1)

        self.sum_tests = sum_tests

    def run_test(self, fixture, name, **kwargs):
        with self.subTest(name):
            self.run_test_without_subtest(fixture, name, **kwargs)

    def run_test_without_subtest(self, fixture, name, *, raises=None):
        tc = fixture(methodName=name)
        if raises is not None:
            with self.assertRaises(raises):
                getattr(tc, name)()
        else:
            getattr(tc, name)()

    def test_success(self):
        self.run_test(self.sum_tests, 'test_a')
        self.run_test(self.sum_tests, 'test_b')
        self.run_test(self.sum_tests, 'test_d')
        self.run_test(self.sum_tests, 'test_optional_success')

    def test_failure(self):
        self.run_test(self.sum_tests, 'test_c', raises=AssertionError)
        self.run_test(self.sum_tests, 'test_optional_failure', raises=AssertionError)
        self.run_test(self.sum_tests, 'test_optional_badargs', raises=TypeError)

    def test_alt_test(self):
        @self.sum_tests.with_test
        def mul_test(self, mul, *terms):
            result = 1
            for t in terms:
                result *= t
            self.assertEqual(result, mul)

        self.run_test(mul_test, 'test_b')
        self.run_test(mul_test, 'test_c')
        self.run_test(mul_test, 'test_d')

        self.run_test(mul_test, 'test_a', raises=AssertionError)

    def test_unspecified_test(self):
        class fixtures(Fixtures):
            _test = None

            a = 3, 6, 2
            b = 6, 24, 4
            c = 31, 64, 33
            d = 2, 4, 2

        self.assertFalse(issubclass(fixtures, unittest.TestCase))

        @fixtures.with_test
        def div_tests(self, r, a, b):
            self.assertEqual(r, a / b)
        self.run_test(div_tests, 'test_a')
        self.run_test(div_tests, 'test_b')
        self.run_test(div_tests, 'test_d')
        self.run_test(div_tests, 'test_c', raises=AssertionError)

        @fixtures.with_test
        def sub_tests(self, r, a, b):
            self.assertEqual(r, a - b)
        self.run_test(sub_tests, 'test_c')
        self.run_test(sub_tests, 'test_d')
        self.run_test(sub_tests, 'test_a', raises=AssertionError)
        self.run_test(sub_tests, 'test_b', raises=AssertionError)

    def test_options(self):
        def mul(terms):
            result = 1
            for t in terms:
                result *= t
            return result

        class option_tests(Fixtures):
            def _test(self, expected_result, *terms, operation=sum, modulo=None):
                result = operation(terms)
                if modulo is not None:
                    result = result % modulo
                self.assertEqual(expected_result, result)

            not_using_options = 5, 2, 3
            has_options = 6, 2, 3, options(operation=mul)
            has_multiple_options_one_call = 1, 2, 3, options(operation=mul, modulo=5)
            has_multiple_options_multiple_calls = 1, 2, 3, options(operation=mul), options(modulo=5)
            has_interleaved_option_calls = 1, options(operation=mul), 2, options(modulo=5), 3

            fails_assertion = 0, 2, 3, options(operation=mul, modulo=5)

        self.run_test(option_tests, "test_not_using_options")
        self.run_test(option_tests, "test_has_options")
        self.run_test(option_tests, "test_has_multiple_options_one_call")
        self.run_test(option_tests, "test_has_multiple_options_multiple_calls")
        self.run_test(option_tests, "test_has_interleaved_option_calls")

        self.run_test(option_tests, "test_fails_assertion", raises=AssertionError)

    def test_options_required_args(self):
        class option_tests(Fixtures):
            def _test(self, a, b, *, expected):
                self.assertEqual(expected, a + b)

            kwoarg_as_options = 1, 2, options(expected=3)
            pokarg_as_options = 1, options(b=2, expected=3)

            missing_kwoarg = 1, 2
            duplicate_argument = 2, options(a=1, expected=3)

        self.run_test(option_tests, "test_kwoarg_as_options")
        self.run_test(option_tests, "test_pokarg_as_options")

        self.run_test(option_tests, "test_missing_kwoarg", raises=TypeError)
        self.run_test(option_tests, "test_duplicate_argument", raises=TypeError)


    def test_missing_test(self):
        with self.assertRaises(ValueError,
                        msg="'_test' function missing from Fixtures class"):
            class my_tests(Fixtures):
                a = 1, 2, 3
                b = 4, 5, 6

    def assert_tb(self, fixture, name, func, line, *,  raises=AssertionError):
        with self.subTest(name):
            try:
                self.run_test_without_subtest(fixture, name)
            except raises:
                _, _, tb = sys.exc_info()
            else:
                raise AssertionError(f"Expected {raises.__name__} to be raised")
            tb_funcs, tb_lines = get_tb_funcs_lines(tb)
            self.assertIn(func, tb_funcs)
            self.assertIn([f"            {line}\n"], tb_lines)

    def test_line(self):
        self.assert_tb(self.sum_tests, "test_c", "sum_tests", "c = 15, 5, 3")
        self.assert_tb(self.sum_tests, "test_optional_failure", "sum_tests", "optional_failure = 1, 3, 2, options(optional=1)")
        self.assert_tb(self.sum_tests, "test_optional_badargs", "sum_tests", "optional_badargs = 3, 2, 1, options(doesntexist=1)", raises=TypeError)

    def test_func_location(self):
        class func_tests(Fixtures):
            def _test(self, func, a, b):
                raise AssertionError

            @tup("one", "params")
            def one():
                pass # pragma: no cover
        try:
            self.run_test_without_subtest(func_tests, "test_one")
        except AssertionError:
            _, _, tb = sys.exc_info()
        else:
            raise AssertionError("Expected AssertionError")
        tb_funcs = []
        tb_lines = []
        while tb is not None:
            fi = inspect.getframeinfo(tb)
            tb_funcs.append(fi.function)
            tb_lines.append(fi.code_context)
            tb = tb.tb_next
        self.assertIn("func_tests", tb_funcs)
        try:
            self.assertIn(['            @tup("one", "params")\n'], tb_lines)
        except AssertionError:
            self.assertIn(['            def one():\n'], tb_lines)

    def test_relocate_frame_chevrons(self):
        f = core._raise_at_custom_line("mymodule.py", 123, "<module>")
        self.assertEqual(f.__name__, 'module')

    @skip_noprepare
    def test_dup(self):
        with self.assertRaises(ValueError):
            class fail_tests(Fixtures):
                a = 1
                a = 2

    @skip_noprepare
    def test_dup_with(self):
        with self.assertRaises(ValueError):
            class fail_tests(WithTestClass(unittest.TestCase)):
                a = 1
                a = 2

    @skip_noprepare
    def test_dup_ok(self):
        class fail_tests(Fixtures):
            def _test(self):
                raise NotImplementedError
            _private = 1
            _private = 2

    @skip_noprepare
    def test_dup_testfunc(self):
        with self.assertRaises(ValueError):
            class fail_tests(Fixtures):
                def _test(self):
                    raise NotImplementedError
                _test # silences pyflakes redef warning
                def _test(self):
                    raise NotImplementedError

    @skip_noprepare
    def test_dup_regular(self):
        with self.assertRaises(ValueError):
            class fail_tests(Fixtures):
                def test_1(self):
                    raise NotImplementedError
                test_1 # silences pyflakes redef warning
                def test_1(self):
                    raise NotImplementedError

    def test_copied_func(self):
        trap = []
        class fixtures(Fixtures):
            def _test(self):
                raise NotImplementedError
            def test_a(self):
                trap.append(0)
        self.assertEqual(trap, [])
        self.run_test(fixtures, 'test_a')
        self.assertEqual(trap, [0])

    @skip_noprepare
    def test_dup_copied_func(self):
        with self.assertRaises(ValueError):
            class fail_test_1(Fixtures):
                def _test(self):
                    raise NotImplementedError
                def test_a(self):
                    raise NotImplementedError
                a = ()
        with self.assertRaises(ValueError):
            class fail_test_2(Fixtures):
                def _test(self):
                    raise NotImplementedError
                a = ()
                def test_a(self):
                    raise NotImplementedError

    def test_tup(self):
        def func():
            raise NotImplementedError
        self.assertEqual(tup(1, 2, 3)(func), (func, 1, 2, 3))

    def test_unittest(self):
        self.assertTrue(issubclass(self.sum_tests, unittest.TestCase))


class CustomTestClassTests(unittest.TestCase):
    def setUp(self):
        class MyTestCase(object):
            pass
        self.ctc = MyTestCase

    def test_missing_test(self):
        m = WithTestClass(self.ctc)
        with self.assertRaises(ValueError,
                        msg="'_test' function missing from Fixtures class"):
            class tests(m):
                t1 = 1, 2, 3

    def test_par(self):
        m = WithTestClass(self.ctc)
        class tests(m):
            def _test(self):
                raise NotImplementedError
        self.assertTrue(issubclass(tests, self.ctc))

        @tests.with_test
        def other_test():
            raise NotImplementedError
        self.assertTrue(issubclass(other_test, self.ctc))

    def test_par_sep(self):
        m = WithTestClass(self.ctc)
        class fixtures(m):
            _test = None
        @fixtures.with_test
        def sep_test():
            raise NotImplementedError
        self.assertTrue(issubclass(sep_test, self.ctc))

    def test_body(self):
        class tests(Fixtures):
            _TestCase = self.ctc
            def _test(self):
                raise NotImplementedError
        self.assertTrue(issubclass(tests, self.ctc))

        @tests.with_test
        def other_test():
            raise NotImplementedError
        self.assertTrue(issubclass(other_test, self.ctc))

    def test_body_sep(self):
        class fixtures(Fixtures):
            _TestCase = self.ctc
            _test = None
        @fixtures.with_test
        def sep_test():
            raise NotImplementedError
        self.assertTrue(issubclass(sep_test, self.ctc))

    def test_keyword(self):
        meta = core.FixturesMeta
        name = 'fixtures'
        bases = object,
        d = meta.__prepare__(name, bases, TestCase=self.ctc)
        def _testfunc(self):
            raise NotImplementedError
        d['_test'] = _testfunc
        fixtures = meta(name, bases, d)
        self.assertTrue(issubclass(fixtures, self.ctc))

        @fixtures.with_test
        def other_test():
            raise NotImplementedError
        self.assertTrue(issubclass(other_test, self.ctc))

    def test_keyword_sep(self):
        meta = core.FixturesMeta
        name = 'fixtures'
        bases = object,
        d = meta.__prepare__(name, bases, TestCase=self.ctc)
        d['_test'] = None
        fixtures = meta(name, bases, d)

        @fixtures.with_test
        def other_test():
            raise NotImplementedError
        self.assertTrue(issubclass(other_test, self.ctc))
