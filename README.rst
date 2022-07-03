.. |ut| replace:: unittest
.. _ut: http://docs.python.org/3/library/unittest.html

.. |tc| replace:: unittest.TestCase
.. _tc: http://docs.python.org/3/library/unittest.html#unittest.TestCase

.. |subtests| replace:: subtests
.. _subtests: https://docs.python.org/3/library/unittest.html#subtests

.. |pyt| replace:: pytest
.. _pyt: https://docs.pytest.org/en/stable/contents.html

.. |pytest-subtests| replace:: pytest-subtests
.. _pytest-subtests: https://pypi.org/project/pytest-subtests/

.. _repeated_test:

*************
repeated_test
*************

.. image:: https://badges.gitter.im/epsy/repeated_test.svg
   :alt: Join the chat at https://gitter.im/epsy/repeated_test
   :target: https://gitter.im/epsy/repeated_test?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
.. image:: https://github.com/epsy/repeated_test/actions/workflows/ci.yml/badge.svg?branch=master
    :target: https://github.com/epsy/repeated_test/actions/workflows/ci.yml
.. image:: https://coveralls.io/repos/github/epsy/repeated_test/badge.svg?branch=master
    :target: https://coveralls.io/github/epsy/repeated_test?branch=master

``repeated_test`` lets you write tests that apply the same function to
many sets of parameters.


.. _example:

For instance:

.. code-block:: python

    from repeated_test import Fixtures

    class MyFixtures(Fixtures):
        def _test(self, expected, *terms):
            self.assertEqual(expected, sum(terms))

        a = 10, 5, 5
        b = 15, 7, 8
        c = 42, 1, 1

The result is unittest-compatible, and provides useful context in the
traceback in case of errors:

.. code-block:: console

    $ python -m unittest my_tests
    ..F
    ======================================================================
    FAIL: test_c (my_tests.MyFixtures)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "my_tests.py", line 9, in MyFixtures
        c = 42, 1, 1
      File "my_tests.py", line 5, in _test
        self.assertEqual(expected, sum(terms))
    AssertionError: 42 != 2

    ----------------------------------------------------------------------
    Ran 3 tests in 0.002s

    FAILED (failures=1)

.. _install:

You can install it using:

.. code-block:: console

    $ pip install --user repeated_test


.. _help:

Help / Issues
=============

You can get help in the
`gitter.im chatroom <https://gitter.im/epsy/repeated_test>`_.

If you find any issues or have any requests, use
`GitHub Issues <https://github.com/epsy/repeated_test/issues>`_.


.. _reference:

Reference
=========

.. _intro:

Introduction
------------

Python's |ut|_ modules helps in performing various forms of automated testing.
One writes a class deriving from |tc|_ and adds various ``test_xyz`` methods.
Test runners run these tests, keeping count of successful and failed tests,
and produces a trace with the causes of these failures.

Sometimes it makes sense to have one test be carried out for a large amount
of different inputs.
This module aims to provide an efficient way to do this.

It allows you to write fixtures (inputs) as plain members of a
class, and bind a test function to them. This test function is called for each
fixture as you will see below. The produced class is a |tc|_ subclass, so it is
compatible with |ut|_ and other |ut|-compatible test runners.


.. _testcase:

Building a test case
--------------------

In order to produce a |tc|_, ``repeated_test`` requires you to:

* Subclass ``repeated_test.Fixtures``
* Write a ``_test`` method that takes a few parameters, making use of any
  |tc|_ method it needs
* Assign fixtures directly in the class body, which are then unpacked as
  arguments to the ``_test`` method (as in ``_test(*args)``)

You can use any |tc|_ methods in your test function, such as ``assertEqual()``
and so forth.

.. code-block:: python

    from repeated_test import Fixtures

    class MyFixtures(Fixtures):
        def _test(self, arg1, arg2, arg3):
            self.assertEqual(..., ...)

        Ps = 'p1', 'p2', 'p3'
        # _test(*Ps) will be called, ie. _test('p1', p2', 'p3')

        Qs = 'q1', 'q2', 'q3'
        # _test(*Qs) will be called, ie. _test('q1', q2', 'q3')

Make sure that your fixture tuples provide the correct amount of arguments
for your ``_test`` method, unless it has an ``*args`` parameter.


.. _running:

Running a test case
-------------------

You can run a ``repeated_test`` test case like any other |tc|_ class:

.. code-block:: shell

    python -m unittest
    python -m unittest my_test_module
    python -m unittest my_test_module.MyFixtures

    # To refer to an individual test, prefix the name of the fixture with "test_"
    python -m unittest my_test_module.MyFixtures.test_Ps

Learn more in the `official unittest docs <https://docs.python.org/3/library/unittest.html#command-line-interface>`_.

You can also use a |ut|-compatible test runer, like |pyt|_:

.. code-block:: shell

    python -m pytest
    python -m pytest my_test_module.py
    python -m pytest my_test_module.py -k MyFixtures
    python -m pytest my_test_module.py -k test_Ps
    python -m pytest my_test_module.py::MyFixtures::test_Ps

Learn more in the `official pytest docs <https://docs.pytest.org/en/stable/how-to/usage.html>`_

.. _options:

Passing in keyword arguments
----------------------------

You can pass in keyword arguments using ``repeated_test.options``:

.. code-block:: python

    import sys

    from repeated_test import Fixtures, options

    class MyFixtures(Fixtures):
        def _test(self, arg1, arg2, *, min_version=None, max_version=None):
            ...

        not_using_versions = "abc", "abc"
        # -> _test("abc", "abc")

        using_max_version = "abc", "abc", options(max_version=(3, 9))
        # -> _test("abc", "abc", max_version=(3, 9))

        using_both_versions = "abc", "abc", options(min_version=(3, 8), max_version=(3, 9))
        # -> _test("abc", "abc", min_version=(3, 8), max_version=(3, 9))

        using_both_versions_2 = "abc", "abc", options(min_version=(3, 8)), options(max_version=(3, 9))
        # Same, but by specifying options separately

This can be useful if you have multiple options that are only used some of the time.

.. _manage-options:

Passing in keyword arguments to multiple tests
----------------------------------------------

If you are re-using the same keyword arguments across multiple tests,
there are several ways to do so:

- Using ``@repeated_test.with_options(...)`` lets you
  specify options for every fixture within a class.
- Using ``with repeated_test.options(...)`` lets you
  specify options for every fixture within the ``with`` block.
- You can continue using ``options()`` on individual fixtures,
  and override values provided by surrounding code.
- You can use ``repeated_test.skip_option`` to stop supplying any argument.
  The argument won't be supplied to the function,
  which is useful for using a default value,
  or for removing common options from a class whose test function doesn't handle

.. code-block:: python

    from repeated_test import Fixtures, options, with_options

    @with_options(kwarg1="value from decorator")
    class MyFixtures(Fixtures):
        def _test(self, arg1, arg2, *, kwarg1, kwarg2="default"):
            ...

        using_provided_values = "arg1", "arg2"
        # -> _test("arg1", "arg2", kwarg1="value from decorator", kwarg2="default")

        overriding_provided_values = "arg1", "arg2", options(kwarg1="kwarg1", kwarg2="kwarg2")
        # -> _test("arg1", "arg2", kwarg1="kwarg1", kwarg2="kwarg2")

        with options(kwarg1="value from context manager"):
            using_value_from_context_manager = "arg1", "arg2"
            # -> _test("arg1", "arg2", kwarg1="value from context manager", kwarg2="default")

            overriding_value_from_context_manager = "arg1", "arg2", options(kwarg1="kwarg1")
            # -> _test("arg1", "arg2", kwarg1="kwarg1", kwarg2="default")

        with options(kwarg2="value from context manager"):
            removing_value = "arg1", "arg2"
            # -> _test("arg1", "arg2", kwarg1="value from decorator", kwarg2="value from context manager")
            removing_value = "arg1", "arg2", options(kwarg2=skip_option)
            # -> _test("arg1", "arg2", kwarg1="value from decorator", kwarg2="default")

.. _options-matrix:

Testing multiple values for a keyword parameter
-----------------------------------------------

You can also use ``@with_options_matrix``
to provide multiple values for a keyword parameter.
``repeated_test`` will run every combination
except for parameters that are overridden.

.. code-block:: python

    from repeated_test import Fixtures, options, with_options_matrix


    @with_options_matrix(
        spam=["spam1", "spam2"],
        ham=["ham1", "ham2"],
    )
    class MyFixtures(Fixtures):
        def _test(self, arg1, arg2, *, spam, ham):
            ...

        using_provided_values = "arg1", "arg2"
        # -> _test("arg1", "arg2", spam="spam1", ham="ham1")
        # -> _test("arg1", "arg2", spam="spam1", ham="ham2")
        # -> _test("arg1", "arg2", spam="spam2", ham="ham1")
        # -> _test("arg1", "arg2", spam="spam2", ham="ham2")

        with options(spam="spam"):
            overriding_one_value = "arg1", "arg2"
            # -> _test("arg1", "arg2", spam="spam", ham="ham1")
            # -> _test("arg1", "arg2", spam="spam", ham="ham2")

``repeated_test`` will report each combination using unittest's |subtests|_ feature.
|pyt| does not have this feature built-in, but the |pytest-subtests|_ plugin adds support.

.. code-block:: console

    ======================================================================
    FAIL: test_overriding_one_value (example_options._test) (ham='ham1')
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "/home/ykaiser/repeated_test/example_options.py", line 41, in MyFixtures
        overriding_one_value = "arg1", "arg2"
      File "/home/ykaiser/repeated_test/example_options.py", line 32, in _test
        self.fail("example failure")
    AssertionError: example failure

    ======================================================================
    FAIL: test_overriding_one_value (example_options._test) (ham='ham2')
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "/home/ykaiser/repeated_test/example_options.py", line 41, in MyFixtures
        overriding_one_value = "arg1", "arg2"
      File "/home/ykaiser/repeated_test/example_options.py", line 32, in _test
        self.fail("example failure")
    AssertionError: example failure

.. _naming:
.. _escaping:

Naming and escaping
-------------------

You may name your test tuples however you like, though they may not start with
``test_`` or ``_``. They are copied to the resulting |tc|_ class, and test
methods are created for them. Their name is that of the tuple, prefixed with
``test_``.

.. _regular test methods:
.. _regular:

Members starting with ``test_`` or ``_`` are directly copied over to the
resulting |tc|_ class, without being treated as fixtures. You can use this to
insert regular tests amongst your fixtures, or constants that you do not wish
to be treated as tests:

.. code-block:: python

    from repeated_test import Fixtures

    class MyFixtures(Fixtures):
        def _test(self, arg1, arg2, arg3):
            self.assertEqual(..., ...)

        def test_other(self):
            self.assertEqual(3, 1+2)

        _spam = 'spam, bacon and eggs'
        # _spam won't be treated as a fixture, so _test(*_spam) won't be called

        ham = _spam, _spam, _spam

You may even call the test function using ``self._test(...)`` if necessary.


.. _separate:

Separating tests and fixtures
-----------------------------

You can apply a fixtures class to a different test function using its
``with_test`` method:

.. code-block:: python

    class MyFixtures(Fixtures):
        _test = None
        ...

    @MyFixtures.with_test
    def other_test(self, arg1, arg2, arg3):
        self.assertEqual(..., ...)

While the function appears out of any class, it will be used as a method of
the resulting |tc|_ class, so keep in mind that it takes a ``self`` parameter.

You can reuse a fixture class however many times you like.

If you specify a test function this way, you can set ``_test = None``
in your fixtures definition. However, it will not be discovered by |ut|_,
so `regular test methods`_ won't be run.
Omitting ``_test`` completely raises an error in order to prevent accidentally
disabling your tests.


.. _decorator:

Working with functions as fixtures
----------------------------------

It can be fairly impractical to use functions in your fixture tuples in this
scheme. If your fixture tuple is meant to have one function in it, you can
use the ``tup`` decorator:

.. code-block:: python

    from repeated_test import Fixtures, tup

    class my_tests(Fixtures):
        def _test(self, func, arg1, arg2):
            self.assertEqual(..., ...)

        @tup('arg1', 'arg2')
        def ham():
            pass
        # equivalent to
        def _ham():
            pass
        ham = _ham, 'arg1', 'arg2'


.. _non-unittest:

Replacing |tc| with another class
---------------------------------

You can replace |tc| with another class using ``WithTestClass(cls)``.

For instance, if you wish to use ``unittest2``:

.. code-block:: python

    import unittest2
    from repeated_test import WithTestClass

    class my_tests(WithTestClass(unittest2.TestCase)):
        ...
