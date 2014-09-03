import socket
import re
import ssl

class Bot(object):

    hooks = []
    context = {}

    def __setup(self, config):

        """Sets up the connection to the IRC server given the configuration.
        If the port is normally used for SSL, the socket will be wrapped in
        SSL. It then connects to the server, sets up the nick and user
        information, and then joins any specified channels."""

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
        decorator pattern"""

        self.hooks.append({
            'rule': re.compile(rule),
            'search': search,
            'function': function
        })

    def on(self, rule, search=False):

        """Execute a function when a message on IRC is matched to a regular
        expression (rule)."""

        def decorator(function):

            # Add the function and the regular expression to the list of
            # functions and expressions to check
            self.hooks.append({
                'rule': re.compile(rule),
                'function': function,
                'search': search
            })

            return function

        return decorator

    def monitor(self, **kwargs):

        """Determine the configuration, setup the connection, and then listen
        for data from the server. PONG when a PING is recieved. Otherwise
        iterate over the functions and check if the rule matches the message.
        If so, call the function with the context and the result of the
        matching."""

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

        # Setup the connection
        self.__setup(config)

        # Listen for data forever
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
                for hook in self.hooks:

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
