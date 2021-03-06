# -*- coding: utf-8 -*-

"""
ReactIRC.bot
~~~~~~~~~~~~

:copyright: (c) 2014 by Mihir Singh (@citruspi)
:license: MIT, see LICENSE for more details.
"""

from web import Web
from irc import IRC
from . import conf, connection

class Bot(object):

    __web = None
    __irc = None

    def __init__(self):

        self.config = conf

        self.__irc = IRC()
        self.on = self.__irc.add
        self.speak = self.__irc.speak
        self.join = self.__irc.join
        self.part = self.__irc.part
        self.quit = self.__irc.quit

        self.__web = Web(self.__irc)
        self.web = self.__web.add

    def hook(self, source, rule, function):

        """Allow for the addition of existing functions without using the
        decorator pattern
        """

        if source == 'irc':

            self.__irc.hooks.append({
                'rule': re.compile(rule),
                'function': function
            })

        elif source == 'web':

            self.__web.hooks.append({
                'rule': re.compile(rule),
                'function': function
            })

    def monitor(self, **kwargs):

        """Determine the configuration, setup the connection, and then listen
        for data from the server. PONG when a PING is recieved. Otherwise
        iterate over the functions and check if the rule matches the message.
        If so, call the function with the context and the result of the
        matching.
        """

        for key in kwargs.keys():

                conf[key] = kwargs[key]

        conf['channels'] = conf['channels'].split(',')

        connection.connect()

        self.__irc.monitor()
        self.__web.monitor()

        while True:

            pass
