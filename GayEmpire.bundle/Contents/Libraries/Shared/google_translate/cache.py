#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Module that contains the cache object."""

from __future__ import unicode_literals

import time
import logging

from .utils import (
    write_dict,
    get_dict
)


class Cache(object):

    """Store objects for a period of time.

    Cache like object that uses a dictionary to store multiple objects for a
    period of time. This cache can also be stored in a json file for later use.

    Examples:
        Simple use case::

            >>> from google_translate.cache import Cache

            >>> cache = Cache(100, 3600.0) # Store items for 1 hour
            >>> cache.add('key', 'value')
            >>> value = cache.get('key')

            >>> cache.store('mycache')     # Store our cache in 'mycache' file

            >>> new_cache = Cache(200, 300.0)
            >>> new_cache.load('mycache')  # Load items from 'mycache' file
            >>> new_cache.remove_old()     # Remove all the old items

    Attributes:
        _VALUE (int): Static number(index) that points to the value part of
            the cache item.

        _TIMESTAMP (int): Static number(index) that points to the timestamp
            part of the cache item.

    Args:
        max_size (int): Maximum number of items that the cache can store. The
            cache automatically removes the oldest item when it reaches
            the max_size.

        valid_period (float): Time in seconds that the cache items are valid.
            This value can be changed after the object initialization.

    """

    _VALUE = 0
    _TIMESTAMP = 1

    def __init__(self, max_size, valid_period):
        if not isinstance(max_size, int):
            raise TypeError(max_size)

        if not isinstance(valid_period, float):
            raise TypeError(valid_period)

        if max_size < 1:
            raise ValueError(max_size)

        if valid_period <= 0.0:
            raise ValueError(valid_period)

        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self._valid_period = valid_period
        self._max_size = max_size
        self._items = {}

        self.logger.debug("Cache initiated max_size: (%s), valid_period: (%s)", max_size, valid_period)

    @property
    def max_size(self):
        return self._max_size

    @property
    def valid_period(self):
        return self._valid_period

    @valid_period.setter
    def valid_period(self, value):
        if not isinstance(value, float):
            raise TypeError(value)

        if value <= 0.0:
            raise ValueError(value)

        self._valid_period = value
        self.logger.debug("Valid period changed to: (%s)", value)

    def has_space(self):
        """Returns True if the cache has not reached the max_size else False."""
        return len(self._items) < self._max_size

    def has(self, key):
        """Returns True if the key is in the cache else False."""
        return key in self._items

    def get_oldest(self):
        """Returns the oldest key in the cache if one exists else None."""
        min_timestamp = None
        min_key = None

        for key in self._items:
            if min_timestamp is None:
                min_timestamp = self._items[key][self._TIMESTAMP]
                min_key = key
                continue

            if self._items[key][self._TIMESTAMP] < min_timestamp:
                min_timestamp = self._items[key][self._TIMESTAMP]
                min_key = key

        return min_key

    def add(self, key, obj):
        """Add new item to the cache.

        Adds the key-obj combination to the cache. If the cache reaches the
        max_size then the oldest item is automatically removed.

        Args:
            key (hashable type): Key under which the obj will be stored.

            obj (object): Object to store in the cache.

        """
        self.logger.debug("Adding new item to cache, key: %r", key)

        # If key not in cache and the cache is out of space
        if not key in self._items and len(self._items) == self._max_size:
            self.logger.warning("Cache out of limit")
            oldest = self.get_oldest()

            del self._items[oldest]
            self.logger.debug("Key removed: %r", oldest)

        self._items[key] = [obj, time.time()]

    def get(self, key):
        """Get item from the cache.

        Returns the item corresponding to the given key if the given key exists
        else None. Note that if the timestamp of the item is old then it will
        return None even if the key exists.

        Args:
            key (hashable type): Key to search for.

        """
        self.logger.debug("Searching cache for key: %r", key)

        if key in self._items and self._valid_timestamp(key):
            self.logger.info("Item found in cache")
            return self._items[key][self._VALUE]

        self.logger.info("Item not in cache")
        return None

    def remove_old(self):
        """Remove old items from the cache.

        Removes all the items with invalid timestamp from the cache
        and returns the number of the items removed.

        """
        self.logger.info("Removing old items from cache")
        items_removed = 0

        for key in self._items.keys():
            if not self._valid_timestamp(key):
                del self._items[key]
                items_removed += 1

        self.logger.debug("Items removed: (%s)", items_removed)
        return items_removed

    def store(self, filename):
        """Store the cache to the given filename.

        Returns:
            True on success else False.

        """
        self.logger.debug("Saving cache state to: %r", filename)
        return write_dict(filename, self._items)

    def load(self, filename):
        """Load the cache content from the given filename.

        Returns:
            True on success else False.

        Note:
            The cache stops adding new items when it reaches the max_size.

        """
        self.logger.debug("Retrieving cache state from: %r", filename)

        loaded_items = get_dict(filename)

        if loaded_items is None:
            return False

        for key in loaded_items:
            if len(self._items) == self.max_size:
                self.logger.warning("Cache reached max size while loading content")
                break

            self._items[key] = loaded_items[key]

        return True

    def items(self):
        """Returns list with (key, [obj, timestamp]) pairs."""
        return self._items.items()

    def _valid_timestamp(self, key):
        """Returns True if the given key has a valid timestamp else False."""
        return time.time() - self._items[key][self._TIMESTAMP] <= self._valid_period

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self._items.items())

    def __len__(self):
        return len(self._items)
