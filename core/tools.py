import functools
import hashlib

import pandas as pd
import numpy as np

from core.storage import Storage


def compound_exp(r):
    """
    returns the result of compounding the set of returns in r
    """
    return np.expm1(np.log1p(r).sum())


def hash_single(arg):
    if isinstance(arg, pd.Series) or isinstance(arg, pd.DataFrame):
        return hashlib.sha256(
            pd.util.hash_pandas_object(arg, index=True).values).hexdigest()
    elif isinstance(arg, tuple) or isinstance(arg, list):
        m = hashlib.md5()
        for s in arg:
            m.update(str(s).encode())
        return m.hexdigest()
    elif isinstance(arg, str):
        m = hashlib.md5()
        m.update(arg.encode())
        return m.hexdigest()
    else:
        return hash(arg)


def hash_multiple(args, kwargs):
    hashed_args = tuple(hash_single(arg) for arg in args)
    # (0, 'bb7831021d8a3e98102cca4d329b1201a5d9dff5538a8ebb4229994ac60f6fb1')
    hashed_kwargs = tuple(hash_single(kwarg) for kwarg in kwargs.values())
    return hash_single(hashed_args + hashed_kwargs)


def cached(storage: Storage = None, memory_cache=True):
    """
    A function that creates a decorator which will use "cachefile"
    for caching the results of the decorated function "fn"
    :param storage:
    :type storage:
    :return:
    :rtype:
    """

    def decorator(fn):
        if memory_cache:
            fn_cache = {}

        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            kwargs_with_fn = kwargs.copy()
            kwargs_with_fn["fn_module"] = fn.__module__
            kwargs_with_fn["fn_name"] = fn.__name__
            hash_label = hash_multiple(args, kwargs_with_fn)
            if kwargs.get("no_cache", False):
                kwargs.pop("no_cache")
                return fn(*args, **kwargs)

            if memory_cache:
                #  exists in memory cache
                res = fn_cache.get(hash_label)
                if res is not None:
                    return res

            # If exists in storage cache
            if storage.exist(hash_label):
                return storage.load(hash_label)
            # execute the function with all arguments passed
            res = fn(*args, **kwargs)

            if memory_cache:
                # save to memory cache
                fn_cache[hash_label] = res

            # save to storage
            storage.save(hash_label, res)
            return res

        return wrapped

    return decorator
