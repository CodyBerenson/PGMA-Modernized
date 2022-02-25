"""Two Way Ordered DICTionary for Python.

Attributes:
    _DEFAULT_OBJECT (object): Object that it's used as a default parameter.

"""

import sys
import collections


__all__ = ["TwoWayOrderedDict"]

__version__ = "1.2"

__license__ = "Unlicense"


_DEFAULT_OBJECT = object()


########## Custom views to mimic Python3 view objects ##########
# See: https://docs.python.org/3/library/stdtypes.html#dict-views

class DictKeysView(collections.KeysView):

    def __init__(self, data):
        super(DictKeysView, self).__init__(data)
        self.__data = data

    def __repr__(self):
        return "dict_keys({data})".format(data=list(self))

    def __contains__(self, key):
        return key in [key for key in self.__data]


class DictValuesView(collections.ValuesView):

    def __init__(self, data):
        super(DictValuesView, self).__init__(data)
        self.__data = data

    def __repr__(self):
        return "dict_values({data})".format(data=list(self))

    def __contains__(self, value):
        return value in [self.__data[key] for key in self.__data]


class DictItemsView(collections.ItemsView):

    def __init__(self, data):
        super(DictItemsView, self).__init__(data)
        self.__data = data

    def __repr__(self):
        return "dict_items({data})".format(data=list(self))

    def __contains__(self, item):
        return item in [(key, self.__data[key]) for key in self.__data]

###########################################################


class TwoWayOrderedDict(dict):

    """Custom data structure which implements a two way ordrered dictionary.

    Custom dictionary that supports key:value relationships AND value:key
    relationships. It also remembers the order in which the items were inserted
    and supports almost all the features of the build-in dict.

    Examples:
        Unordered initialization::

            >>> tdict = TwoWayOrderedDict(a=1, b=2, c=3)

        Ordered initialization::

            >>> tdict = TwoWayOrderedDict([('a', 1), ('b', 2), ('c', 3)])

        Simple usage::

            >>> tdict = TwoWayOrderedDict()
            >>> tdict['a'] = 1
            >>> tdict['b'] = 2
            >>> tdict['c'] = 3

            >>> tdict['a']  # Outputs 1
            >>> tdict[1]  # Outputs 'a'

            >>> del tdict[2]

            >>> print(tdict)
            TwoWayOrderedDict([('a', 1), ('c', 3)])

    """

    _PREV = 0
    _KEY = 1
    _NEXT = 2

    def __init__(self, *args, **kwargs):
        super(TwoWayOrderedDict, self).__init__()

        self.clear()
        self.update(*args, **kwargs)

    def __setitem__(self, key, value):
        if key in self:
            # Make sure that key != self[key] before removing self[key] from
            # our linked list because we will lose the order
            # For example {'a': 'a'} and we do d['a'] = 2
            if key != self[key]:
                self._remove_mapped_key(self[key])

            dict.__delitem__(self, self[key])

        if value in self:
            # Make sure that key != value before removing value from our
            # linked list because we will lose the order if we remove
            # value = key from our linked list
            if key != value:
                self._remove_mapped_key(value)

            self._remove_mapped_key(self[value])

            # Check if self[value] is in the dict in case that the
            # first del (line:117) has already removed the self[value]
            # For example {'a': 1, 1: 'a'} and we do d['a'] = 'a'
            if self[value] in self:
                dict.__delitem__(self, self[value])

        if key not in self._items_map:
            last = self._items[self._PREV]
            last[self._NEXT] = self._items[self._PREV] = self._items_map[key] = [last, key, self._items]

        dict.__setitem__(self, key, value)
        dict.__setitem__(self, value, key)

    def __delitem__(self, key):
        self._remove_mapped_key(self[key])
        self._remove_mapped_key(key)

        dict.__delitem__(self, self[key])

        # Cases like {'a': 'a'} where we have only one copy instead of {'a': 1, 1: 'a'}
        if key in self:
            dict.__delitem__(self, key)

    def __len__(self):
        return len(self._items_map)

    def __iter__(self):
        return self._iterate()

    def __reversed__(self):
        return self._iterate(reverse=True)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, list(self.items()))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.items() == other.items()

    def __ne__(self, other):
        return not self == other

    def _remove_mapped_key(self, key):
        """Remove the given key both from the linked list and the items map."""
        if key in self._items_map:
            prev_item, _, next_item = self._items_map.pop(key)
            prev_item[self._NEXT] = next_item
            next_item[self._PREV] = prev_item

    def _iterate(self, reverse=False):
        """Generator that iterates over the dictionary keys."""
        index = self._PREV if reverse else self._NEXT
        curr = self._items[index]

        while curr is not self._items:
            yield curr[self._KEY]
            curr = curr[index]

    def items(self):
        return DictItemsView(self)

    def values(self):
        return DictValuesView(self)

    def keys(self):
        return DictKeysView(self)

    def pop(self, key, default=_DEFAULT_OBJECT):
        try:
            value = self[key]

            del self[key]
        except KeyError as error:
            if default == _DEFAULT_OBJECT:
                raise error

            value = default

        return value

    def popitem(self, last=True):
        """Remove and return a (key, value) pair from the dictionary.

        Args:
            last (boolean): When True popitem() will remove the last list item.
                When False popitem() will remove the first list item.

        Note:
            popitem() is useful to destructively iterate over a dictionary.

        Raises:
            KeyError: If the dictionary is empty.

        """
        if not self:
            raise KeyError('popitem(): dictionary is empty')

        index = self._PREV if last else self._NEXT

        _, key, _ = self._items[index]
        value = self.pop(key)

        return key, value

    def update(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError("expected at most 1 arguments, got {0}".format(len(args)))

        for item in args:
            if isinstance(item, dict):
                item = item.items()

            for key, value in item:
                self[key] = value

        for key, value in kwargs.items():
            self[key] = value

    def setdefault(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    def copy(self):
        return self.__class__(self.items())

    def clear(self):
        self._items = item = []
        # Cycled double linked list [previous, key, next]
        self._items += [item, None, item]
        # Map linked list items into keys to speed up lookup
        self._items_map = {}
        dict.clear(self)

    @staticmethod
    def __not_implemented():
        raise NotImplementedError("Please use the equivalent items(), keys(), values() methods")

    if sys.version_info < (3, 0) and sys.version_info >= (2, 2):
        iteritems = iterkeys = itervalues = viewitems = viewkeys = viewvalues = __not_implemented
