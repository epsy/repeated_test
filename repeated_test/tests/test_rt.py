import sys
import inspect
import unittest2
from repeated_test import Fixtures, tup


class RepeatedTestTests(unittest2.TestCase):
    def setUp(self):
        class sum_tests(Fixtures):
            def _test(self, total, *terms):
                self.assertEqual(total, sum(terms))
            a = 3, 2, 1
            b = 6, 3, 2, 1
            c = 15, 5, 3
            d = 4, 2, 2
        self.sum_tests = sum_tests

    def run_test(self, fixture, name):
        tc = fixture(methodName=name)
        getattr(tc, name)()

    def test_success(self):
        self.run_test(self.sum_tests, 'test_a')
        self.run_test(self.sum_tests, 'test_b')
        self.run_test(self.sum_tests, 'test_d')

    def test_failure(self):
        with self.assertRaises(AssertionError):
            self.run_test(self.sum_tests, 'test_c')

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

        with self.assertRaises(AssertionError):
            self.run_test(mul_test, 'test_a')

    def test_unspecified_test(self):
        class fixtures(Fixtures):
            a = 3, 6, 2
            b = 6, 24, 4
            c = 31, 64, 33
            d = 2, 4, 2

        @fixtures.with_test
        def div_tests(self, r, a, b):
            self.assertEqual(r, a / b)
        self.run_test(div_tests, 'test_a')
        self.run_test(div_tests, 'test_b')
        self.run_test(div_tests, 'test_d')
        with self.assertRaises(AssertionError):
            self.run_test(div_tests, 'test_c')

        @fixtures.with_test
        def sub_tests(self, r, a, b):
            self.assertEqual(r, a - b)
        self.run_test(sub_tests, 'test_c')
        self.run_test(sub_tests, 'test_d')
        with self.assertRaises(AssertionError):
            self.run_test(sub_tests, 'test_a')
        with self.assertRaises(AssertionError):
            self.run_test(sub_tests, 'test_b')

    def test_line(self):
        try:
            self.run_test(self.sum_tests, "test_c")
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
        self.assertIn("sum_tests", tb_funcs)
        self.assertIn(["            c = 15, 5, 3\n"], tb_lines)

    @unittest2.skipIf(
        sys.version_info < (3,), "Py version lacks custom class dict support")
    def test_dup(self):
        with self.assertRaises(ValueError):
            class fail_tests(Fixtures):
                a = 1
                a = 2

    def test_tup(self):
        def func():
            raise NotImplementedError
        self.assertEqual(tup(1, 2, 3)(func), (func, 1, 2, 3))
