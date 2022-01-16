# repeated_test -- A framework for repeating a test over many values
# Copyright (C) 2011-2022 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

from functools import partial

def _tup(args, func):
    return (func,) + args

def tup(*args):
    return partial(_tup, args)
