#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Contains different selector objects.

Selector objects can be used as stand alone objects
or add extra functionality to the translators.

Selectors:
    ProxySelector, UserAgentSelector

Attributes:
    _IPV4_REGEXP (regexp): Regular expression to much IPv4 addresses.

"""

from __future__ import unicode_literals

import re
import random
import logging

from urllib2 import HTTPError, URLError

from .utils import (
    load_from_file,
    make_request,
    parse_reply
)

_IPV4_REGEXP = re.compile(r"^([0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,5}$")


class ProxySelector(object):

    """Select proxy base on some criterias.

    ProxySelector supports two proxy modes. Single proxy given by the user or
    multiple proxies from a file. You can also use both of them in which case
    the user defined proxy overwrites the proxies from the file. ProxySelector
    can choose multiple proxies either by using the given sequence or by
    picking one randomly. ProxySelector can detect duplicate entries & invalid
    ip addresses (currently only IPv4 is supported). Finally the user has the
    ability to remove non working proxies.

    Examples:
        Use single proxy (not very handy)::

            >>> proxy_selector = ProxySelector("127.0.0.1:8080")

            >>> proxy = proxy_selector.get_proxy()

        Use multiple proxies from file::

            >>> proxy_selector = ProxySelector(proxy_file="my_proxies")

            >>> proxy = proxy_selector.get_proxy()

    Args:
        proxy (string): User defined proxy.

        proxy_file (string): Absolute path to file that contains multiple
            proxy entries, one per line.

        prevent_fallback (boolean): When True ProxySelector will always return
            a proxy even if the proxy does not work (good to avoid making a
            request without one).

        random_selection (boolean): When True ProxySelector will pick a proxy
            randomly unlike the normal sequence mode.

    """

    def __init__(self, proxy=None, proxy_file=None, prevent_fallback=False, random_selection=False):
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

        self._proxy = None
        self._proxy_list = []
        self._proxy_counter = 0
        self._prevent_fallback = prevent_fallback
        self._random_selection = random_selection

        if ProxySelector.is_valid_proxy(proxy):
            self._proxy = proxy

        if proxy_file is not None:
            for proxy in load_from_file(proxy_file):
                if ProxySelector.is_valid_proxy(proxy) and not proxy in self._proxy_list:
                    self._proxy_list.append(proxy)

        self.logger.debug("User defined proxy: %r", self._proxy)
        self.logger.debug("Proxy list: %r", self._proxy_list)
        self.logger.debug("Proxy file: %r", proxy_file)
        self.logger.debug("Prevent fallback: %r", self._prevent_fallback)
        self.logger.debug("Random selection: %r", self._random_selection)

    def get_proxy(self):
        """Returns a proxy back to the user."""
        self.logger.info("Retrieving proxy")

        if self._proxy is not None:
            return self._proxy

        if self._proxy_list:
            if self._random_selection:
                return random.choice(self._proxy_list)

            if self._proxy_counter == len(self._proxy_list):
                self._proxy_counter = 0

            self.logger.debug("Proxy counter: (%s)", self._proxy_counter)

            proxy = self._proxy_list[self._proxy_counter]
            self._proxy_counter += 1

            return proxy

        return None

    def remove_proxy(self, proxy):
        """Removes the given proxy from the ProxySelector.

        Args:
            proxy (string): Proxy string in the format "ip:port".

        Returns:
            True on success else False.

        """
        self.logger.debug("Removing proxy: %r", proxy)

        removed = False

        if self._prevent_fallback:
            # Only remove the proxy from the list if there are two or more
            # items in the list or the user defined proxy is set
            if proxy in self._proxy_list and (len(self._proxy_list) > 1 or self._proxy is not None):
                if self._proxy_list.index(proxy) < self._proxy_counter:
                    self._proxy_counter -= 1

                self._proxy_list.remove(proxy)
                removed = True

            # Only remove the user specified proxy if there
            # is at least one item in the proxy list
            if proxy == self._proxy and self._proxy_list:
                self._proxy = None
                removed = True
        else:
            if proxy in self._proxy_list:
                if self._proxy_list.index(proxy) < self._proxy_counter:
                    self._proxy_counter -= 1

                self._proxy_list.remove(proxy)
                removed = True

            if proxy == self._proxy:
                self._proxy = None
                removed = True

        self.logger.debug("Proxy removed: %r", removed)

        return removed

    @staticmethod
    def is_valid_proxy(proxy):
        """Static method to check if the given proxy is valid."""
        if not isinstance(proxy, basestring):
            return False

        return (ProxySelector._is_valid_ipv4(proxy) or
                ProxySelector._is_valid_ipv6(proxy))

    @staticmethod
    def _is_valid_ipv4(address):
        """Check if the given address is valid IPv4.

        Note:
            It checks to see if the given IPv4 address has the right
            format and not if it's a network, broadcast, etc..

        """
        if not _IPV4_REGEXP.match(address):
            return False

        ip_addr, port = address.split(':')

        for octet in ip_addr.split('.'):
            if int(octet) > 255 or int(octet) < 0:
                return False

        if int(port) < 1 or int(port) > 65535:
            return False

        return True

    @staticmethod
    def _is_valid_ipv6(address):
        #TODO implement it
        return False


class UserAgentSelector(object):

    """Select user-agent base on some criterias.

    UserAgentSelector supports three basic modes. Single user-agent given by
    the user, multiple user-agents from a file (one per line) and multiple
    user-agents loaded from the handy list of 'techblog.willhouse.com'. You can
    also enable all the modes together or different combinations of them. Note
    that the user defined ua always overwrites the other user-agents (from file
    or HTTP). By default when multiple user-agents are used the get_useragent()
    method returns a user-agent randomly, but if you set single_ua to True then
    UserAgentSelector will pick a user-agent during the initialization and
    stick with it.

    Examples:
        Use single user-agent::

            >>> ua_selector = UserAgentSelector("Mozilla9000")

            >>> ua_selector.get_useragent()

        Use multiple user-agents from HTTP::

            >>> ua_selector = UserAgentSelector(http_mode=True)

            >>> ua_selector.get_useragent()

    Attributes:
        DEFAULT_UA (string): Default user-agent to use.

        HTTP_URL (string): Place to load user-agents from when
            http_mode is enabled.

    Args:
        user_agent (string): User defined user-agent.

        user_agent_file (string): Absolute path to file that contains multiple
            user-agent entries, one per line.

        http_mode (boolean): When True UserAgentSelector will try to retrieve a
            list of user-agents from the place that HTTP_URL points to.

        single_ua (boolean): When True UserAgentSelector will pick a single ua
            and stick with it, even when multiple user-agents are defined
            (from file or HTTP)

    """

    # best penalty ever
    DEFAULT_UA = "https://www.youtube.com/watch?v=Ln45vQv8Lbk"

    HTTP_URL = "http://techblog.willshouse.com/2012/01/03/most-common-user-agents/"

    def __init__(self, user_agent=None, user_agent_file=None, http_mode=False, single_ua=False):
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

        self._user_agent = None
        self._user_agent_list = []

        if isinstance(user_agent, basestring) and user_agent:
            self._user_agent = user_agent

        if isinstance(user_agent_file, basestring):
            self._append_to_ua_list(load_from_file(user_agent_file))

        if http_mode:
            self._append_to_ua_list(self._get_from_http())

        if single_ua:
            self._user_agent = self.get_useragent()

        # Set default useragent
        if self._user_agent is None and not self._user_agent_list:
            self._user_agent = self.DEFAULT_UA

        self.logger.debug("User-agent: %r", self._user_agent)
        self.logger.debug("User-agent list size: (%s)", len(self._user_agent_list))
        self.logger.debug("User-agent file: %r", user_agent_file)
        self.logger.debug("HTTP mode: %r", http_mode)
        self.logger.debug("SINGLE-UA mode: %r", single_ua)

    def get_useragent(self):
        """Returns a user-agent to the user."""
        self.logger.info("Retrieving user-agent")

        if self._user_agent is not None:
            return self._user_agent

        if self._user_agent_list:
            return random.choice(self._user_agent_list)

        return None

    def _append_to_ua_list(self, ua_list):
        """Append items from the given list to self._user_agent_list."""
        if ua_list is not None:
            for user_agent in ua_list:
                if user_agent and user_agent not in self._user_agent_list:
                    self._user_agent_list.append(user_agent)

    def _get_from_http(self):
        """Retrieves a list of user-agents from the internet.

        It tries to retrieve a list of user-agents from the target that
        HTTP_URL points to, so its closely related to the format of the remote
        data it tries to parse.

        Returns:
            A list with user-agents if successful else None

        """
        self.logger.info("Retrieving user-agents by HTTP")

        reply = None

        try:
            # The default user-agent from urllib is blocked
            reply = make_request(self.HTTP_URL, [("User-Agent", self.DEFAULT_UA)])
        except (HTTPError, URLError, IOError) as error:
            self.logger.error("Error %s", error)

        if reply is not None:
            data = parse_reply(reply)

            #print data
            # Quick dirty filter to get the user-agents
            user_agents = data.split("textarea")[1].split('>')[1][:-2]

            return [user_agent for user_agent in user_agents.split('\n')]

        return reply
