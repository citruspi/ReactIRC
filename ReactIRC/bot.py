# -*- coding: utf-8 -*-

"""
ReactIRC.bot
~~~~~~~~~~~~

:copyright: (c) 2014 by Mihir Singh (@citruspi)
:license: MIT, see LICENSE for more details.
"""

import socket
import re
import ssl
import threading

class Bot(object):

    __irc_hooks = []
    __irc_config = {}

    __web_hooks = []

    context = {}
    request = None

    def __setup_irc(self):

        """Sets up the connection to the IRC server given the configuration.
        If the port is normally used for SSL, the socket will be wrapped in
        SSL. It then connects to the server, sets up the nick and user
        information, and then joins any specified channels.
        """

        config = self.__irc_config

        self.verbose = config['verbose']
        self.debug= config['debug']

        self.socket = socket.socket()

        # If the port is used for SSL, wrap the socket in SSL/TLS
        if config['port'] in [6697, 7000, 7070]:

            self.socket = ssl.wrap_socket(self.socket)

        # Initiate a connection to the server and setup the user/nick
        self.socket.connect((config['server'], config['port']))
        self.__send('NICK %s\r\n' % config['nick'])
        self.__send('USER %(n)s %(n)s %(n)s :%(n)s\r\n' % {'n':config['nick']})

        # Join each of the specified channels
        for channel in config['channels']:

            self.join(channel)

    def __send(self, message):

        """Send a string on the socket."""

        self.socket.send(message)

    def speak(self, target, message):

        """Send a message to user or a channel."""

        self.__send("PRIVMSG %s :%s\r\n" % (target, message))

    def join(self, channel):

        """Join a channel. The channel name should be passed without the #."""

        self.__send('JOIN #%s\r\n' % channel)

    def part(self, channel):

        """Leave a channel. The channel name should be passed without the #."""

        self.__send('PART #%s\r\n' % channel)

    def quit(self):

        """Disconnect from the server."""

        self.__send('QUIT\r\n')

    def add_hook(self, rule, function, search=False):

        """Allow for the addition of existing functions without using the
        decorator pattern
        """

        self.__irc_hooks.append({
            'rule': re.compile(rule),
            'search': search,
            'function': function
        })

    def on(self, rule, search=False):

        """Execute a function when a message on IRC is matched to a regular
        expression (rule).
        """

        def decorator(function):

            # Add the function and the regular expression to the list of
            # functions and expressions to check
            self.__irc_hooks.append({
                'rule': re.compile(rule),
                'function': function,
                'search': search
            })

            return function

        return decorator

    def web(self, rule):

        def decorator(function):

            self.__web_hooks.append({
                'rule': re.compile(rule),
                'function': function
            })

            return function

        return decorator

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

        irc_thread = threading.Thread(target=self.__monitor_irc, args=())
        irc_thread.daemon = True
        irc_thread.start()

        from wsgiref.simple_server import make_server
        srv = make_server('0.0.0.0', 8080, self.__monitor_web)
        srv.serve_forever()

        while True:

            pass

    def __web_not_found(self, environ, start_response):

        start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
        return ['Route Not Defined.']

    def __web_success(self, environ, start_response):

        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['']

    def __monitor_web(self, environ, start_response):

        matched = False

        for hook in self.__web_hooks:

            match = hook['rule'].search(environ.get('PATH_INFO', ''))

            if match:

                matched = True

                try:
                    body_size = int(environ.get('CONTENT_LENGTH', 0))
                except (ValueError):
                    body_size = 0

                environ['wsgi.input'] = environ['wsgi.input'].read(body_size)

                self.request = environ
                response = hook['function'](*match.groups())

                if response is not None:

                    if 'targets' not in response.keys():

                        pass

                    else:

                        for target in response['targets']:

                            self.speak(target, response['message'])

                return self.__web_success(environ, start_response)

        if not matched:

            return self.__web_not_found(environ, start_response)

    def __monitor_irc(self):

        config = self.__irc_config

        while True:

            # Read in some data
            content = self.socket.recv(4096)

            # If it's a timeout PING...
            if content[0:4] == "PING":

                #... respond with a PONG
                self.__send('PONG %s \r\n' % content.split()[1])
                continue

            # Otherwise, break up the data by line
            for line in content.split('\n'):

                # Strip any unnecessary characters off the ends
                line = str(line).strip()

                if self.verbose:

                    print line

                # Break up the line
                parsed = line.split(None, 3)

                if len(parsed) != 4:

                    continue

                # Parse out the sender, type, target, and message body
                self.context = {
                    'sender': parsed[0][1:].split('!')[0],
                    'type': parsed[1],
                    'target': parsed[2],
                    'message': parsed[3][1:]
                }

                # If it's a private message, set the target to the sender
                if self.context['target'] == config['nick']:

                    self.context['target'] = self.context['sender']

                # Iterate over the functions with an .on() decorator
                for hook in self.__irc_hooks:

                    # Check if the rule matches the message body
                    if hook['search']:

                        match = hook['rule'].search(self.context['message'])

                    else:

                        match = hook['rule'].match(self.context['message'])

                    if match:

                        if self.debug:

                            print '---'
                            print self.context
                            print match.groups()

                        # Call the function with capture groups as parameters
                        response = hook['function'](*match.groups())

                        # If the function actually returned something print it
                        # to the IRC channel
                        if response is not None:

                            self.speak(self.context['target'], response)
