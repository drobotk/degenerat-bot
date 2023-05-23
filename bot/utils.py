import collections, collections.abc
import contextlib
import inspect
import itertools
import re
import typing
from urllib.parse import urlparse


def is_url(x: str) -> bool:
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])

    except:
        return False


def dots_after(inp: str, length: int) -> str:
    if len(inp) <= length:
        return inp

    return inp[: length - 3] + "..."


def sub_before(a: str, b: str, c: typing.Optional[str] = None) -> str:
    idx = a.find(b)
    if idx < 0:
        return c or a

    return a[:idx]


##################### yt-dlp/yt-dlp/yt_dlp/utils.py <3
NO_DEFAULT = object()
IDENTITY = lambda x: x


def try_call(*funcs, expected_type=None, args=[], kwargs={}):
    for f in funcs:
        try:
            val = f(*args, **kwargs)
        except (
            AttributeError,
            KeyError,
            TypeError,
            IndexError,
            ValueError,
            ZeroDivisionError,
        ):
            pass
        else:
            if expected_type is None or isinstance(val, expected_type):
                return val


def variadic(x, allowed_types=(str, bytes, dict)):
    return (
        x
        if isinstance(x, collections.abc.Iterable) and not isinstance(x, allowed_types)
        else (x,)
    )


def int_or_none(v, scale=1, default=None, get_attr=None, invscale=1):
    if get_attr and v is not None:
        v = getattr(v, get_attr, None)
    try:
        return int(v) * invscale // scale  # type: ignore (some long ass bullshit error that doesnt matter)
    except (ValueError, TypeError, OverflowError):
        return default


class LazyList(collections.abc.Sequence):
    """Lazy immutable list from an iterable
    Note that slices of a LazyList are lists and not LazyList"""

    class IndexError(IndexError):
        pass

    def __init__(self, iterable, *, reverse=False, _cache=None):
        self._iterable = iter(iterable)
        self._cache = [] if _cache is None else _cache
        self._reversed = reverse

    def __iter__(self):
        if self._reversed:
            # We need to consume the entire iterable to iterate in reverse
            yield from self.exhaust()
            return
        yield from self._cache
        for item in self._iterable:
            self._cache.append(item)
            yield item

    def _exhaust(self):
        self._cache.extend(self._iterable)
        self._iterable = []  # Discard the emptied iterable to make it pickle-able
        return self._cache

    def exhaust(self):
        """Evaluate the entire iterable"""
        return self._exhaust()[:: -1 if self._reversed else 1]

    @staticmethod
    def _reverse_index(x):
        return None if x is None else ~x

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            if self._reversed:
                idx = slice(
                    self._reverse_index(idx.start),
                    self._reverse_index(idx.stop),
                    -(idx.step or 1),
                )
            start, stop, step = idx.start, idx.stop, idx.step or 1
        elif isinstance(idx, int):
            if self._reversed:
                idx = self._reverse_index(idx)
            start, stop, step = idx, idx, 0
        else:
            raise TypeError("indices must be integers or slices")
        if (
            (start or 0) < 0
            or (stop or 0) < 0
            or (start is None and step < 0)
            or (stop is None and step > 0)
        ):
            # We need to consume the entire iterable to be able to slice from the end
            # Obviously, never use this with infinite iterables
            self._exhaust()
            try:
                return self._cache[idx]  # type: ignore (idc, not my code)
            except IndexError as e:
                raise self.IndexError(e) from e
        n = max(start or 0, stop or 0) - len(self._cache) + 1
        if n > 0:
            self._cache.extend(itertools.islice(self._iterable, n))
        try:
            return self._cache[idx]  # type: ignore (idc, not my code)
        except IndexError as e:
            raise self.IndexError(e) from e

    def __bool__(self):
        try:
            self[-1] if self._reversed else self[0]
        except self.IndexError:
            return False
        return True

    def __len__(self):
        self._exhaust()
        return len(self._cache)

    def __reversed__(self):
        return type(self)(
            self._iterable, reverse=not self._reversed, _cache=self._cache
        )

    def __copy__(self):
        return type(self)(self._iterable, reverse=self._reversed, _cache=self._cache)

    def __repr__(self):
        # repr and str should mimic a list. So we exhaust the iterable
        return repr(self.exhaust())

    def __str__(self):
        return repr(self.exhaust())


def traverse_obj(
    obj,
    *paths,
    default=NO_DEFAULT,
    expected_type=None,
    get_all=True,
    casesense=True,
    is_user_input=False,
    traverse_string=False
):
    is_sequence = lambda x: isinstance(x, collections.abc.Sequence) and not isinstance(
        x, (str, bytes)
    )
    casefold = lambda k: k.casefold() if isinstance(k, str) else k

    if isinstance(expected_type, type):
        type_test = lambda val: val if isinstance(val, expected_type) else None
    else:
        type_test = lambda val: try_call(expected_type or IDENTITY, args=(val,))

    def apply_key(key, obj, is_last):
        branching = False
        result = None

        if obj is None and traverse_string:
            pass

        elif key is None:
            result = obj

        elif isinstance(key, set):
            assert len(key) == 1, "Set should only be used to wrap a single item"
            item = next(iter(key))
            if isinstance(item, type):
                if isinstance(obj, item):
                    result = obj
            else:
                result = try_call(item, args=(obj,))

        elif isinstance(key, (list, tuple)):
            branching = True
            result = itertools.chain.from_iterable(
                apply_path(obj, branch, is_last)[0] for branch in key
            )

        elif key is ...:
            branching = True
            if isinstance(obj, collections.abc.Mapping):
                result = obj.values()
            elif is_sequence(obj):
                result = obj
            elif isinstance(obj, re.Match):
                result = obj.groups()
            elif traverse_string:
                branching = False
                result = str(obj)
            else:
                result = ()

        elif callable(key):
            branching = True
            if isinstance(obj, collections.abc.Mapping):
                iter_obj = obj.items()
            elif is_sequence(obj):
                iter_obj = enumerate(obj)
            elif isinstance(obj, re.Match):
                iter_obj = itertools.chain(
                    enumerate((obj.group(), *obj.groups())), obj.groupdict().items()
                )
            elif traverse_string:
                branching = False
                iter_obj = enumerate(str(obj))
            else:
                iter_obj = ()

            result = (v for k, v in iter_obj if try_call(key, args=(k, v)))
            if not branching:  # string traversal
                result = "".join(result)

        elif isinstance(key, dict):
            iter_obj = (
                (k, _traverse_obj(obj, v, False, is_last)) for k, v in key.items()
            )
            result = {
                k: v if v is not None else default
                for k, v in iter_obj
                if v is not None or default is not NO_DEFAULT
            } or None

        elif isinstance(obj, collections.abc.Mapping):
            result = (
                obj.get(key)
                if casesense or (key in obj)
                else next((v for k, v in obj.items() if casefold(k) == key), None)
            )

        elif isinstance(obj, re.Match):
            if isinstance(key, int) or casesense:
                with contextlib.suppress(IndexError):
                    result = obj.group(key)

            elif isinstance(key, str):
                result = next(
                    (v for k, v in obj.groupdict().items() if casefold(k) == key), None
                )

        elif isinstance(key, (int, slice)):
            if is_sequence(obj):
                branching = isinstance(key, slice)
                with contextlib.suppress(IndexError):
                    result = obj[key]
            elif traverse_string:
                with contextlib.suppress(IndexError):
                    result = str(obj)[key]

        return branching, result if branching else (result,)

    def lazy_last(iterable):
        iterator = iter(iterable)
        prev = next(iterator, NO_DEFAULT)
        if prev is NO_DEFAULT:
            return

        for item in iterator:
            yield False, prev
            prev = item

        yield True, prev

    def apply_path(start_obj, path, test_type):
        objs = (start_obj,)
        has_branched = False

        key = None
        for last, key in lazy_last(variadic(path, (str, bytes, dict, set))):
            if is_user_input and isinstance(key, str):
                if key == ":":
                    key = ...
                elif ":" in key:
                    key = slice(*map(int_or_none, key.split(":")))
                elif int_or_none(key) is not None:
                    key = int(key)

            if not casesense and isinstance(key, str):
                key = key.casefold()

            if __debug__ and callable(key):
                # Verify function signature
                inspect.signature(key).bind(None, None)

            new_objs = []
            for obj in objs:
                branching, results = apply_key(key, obj, last)
                has_branched |= branching
                new_objs.append(results)

            objs = itertools.chain.from_iterable(new_objs)

        if test_type and not isinstance(key, (dict, list, tuple)):
            objs = map(type_test, objs)

        return objs, has_branched, isinstance(key, dict)

    def _traverse_obj(obj, path, allow_empty, test_type):
        results, has_branched, is_dict = apply_path(obj, path, test_type)
        results = LazyList(item for item in results if item not in (None, {}))
        if get_all and has_branched:
            if results:
                return results.exhaust()
            if allow_empty:
                return [] if default is NO_DEFAULT else default
            return None

        return results[0] if results else {} if allow_empty and is_dict else None

    for index, path in enumerate(paths, 1):
        result = _traverse_obj(obj, path, index == len(paths), True)
        if result is not None:
            return result

    return None if default is NO_DEFAULT else default


##################################################### yt-dlp/yt-dlp/yt_dlp/utils.py <3
