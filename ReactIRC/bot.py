# -*- coding: utf-8 -*-

"""
ReactIRC.bot
~~~~~~~~~~~~

:copyright: (c) 2014 by Mihir Singh (@citruspi)
:license: MIT, see LICENSE for more details.
"""

from web import Web
from connection import Connection
from irc import IRC

class Bot(object):

    __web = None
    __irc = None
    __connection = None

    __irc_config = {}

    context = {}
    request = None

    def __init__(self):

        self.__web = Web(self)
        self.web = self.__web.add

        self.__irc = IRC(self, self.__connection)
        self.on = self.__irc.add

    def __setup_irc(self):

        """Sets up the connection to the IRC server given the configuration.
        If the port is normally used for SSL, the socket will be wrapped in
        SSL. It then connects to the server, sets up the nick and user
        information, and then joins any specified channels.
        """

        config = self.__irc_config

        self.verbose = config['verbose']
        self.debug= config['debug']

        self.__connection = Connection(config['server'], config['port'])


        self.__connection.send('NICK %s\r\n' % config['nick'])
        self.__connection.send('USER %(n)s %(n)s %(n)s :%(n)s\r\n' %
                                {
                                    'n':config['nick']
                                })

        # Join each of the specified channels
        for channel in config['channels']:

            self.join(channel)

    def speak(self, target, message):

        """Send a message to user or a channel."""

        self.__connection.send("PRIVMSG %s :%s\r\n" % (target, message))

    def join(self, channel):

        """Join a channel. The channel name should be passed without the #."""

        self.__connection.send('JOIN #%s\r\n' % channel)

    def part(self, channel):

        """Leave a channel. The channel name should be passed without the #."""

        self.__connection.send('PART #%s\r\n' % channel)

    def quit(self):

        """Disconnect from the server."""

        self.__connection.send('QUIT\r\n')

    def add_hook(self, rule, function, search=False):

        """Allow for the addition of existing functions without using the
        decorator pattern
        """

        self.__irc_hooks.append({
            'rule': re.compile(rule),
            'search': search,
            'function': function
        })

    def monitor(self, **kwargs):

        """Determine the configuration, setup the connection, and then listen
        for data from the server. PONG when a PING is recieved. Otherwise
        iterate over the functions and check if the rule matches the message.
        If so, call the function with the context and the result of the
        matching.
        """

        # Set defaults for the IRC port and server
        config = {
            'port': 6667,
            'server': 'chat.freenode.com',\
            'debug': False,
            'verbose': False
        }

        # Set the nick and channels
        config['nick'] = kwargs['nick']
        config['channels'] = kwargs['channels'].split(',')

        # Determine if the port or server was overridden
        for key in ['port', 'server', 'debug', 'verbose']:

            if key in kwargs.keys():

                config[key] = kwargs[key]

        self.__irc_config = config

        # Setup the connection
        self.__setup_irc()

        # Listen for data forever

        self.__irc.config = config
        self.__irc.connection = self.__connection

        self.__irc.monitor()
        self.__web.monitor()

        while True:

            pass
