from functools import partial

def _tup(args, func):
    return (func,) + args

def tup(*args):
    return partial(_tup, args)
