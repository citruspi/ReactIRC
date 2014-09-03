import socket
import re
import ssl

class Bot(object):

    hooks = []

    def __setup(self, config):

        """Sets up the connection to the IRC server given the configuration.
        If the port is normally used for SSL, the socket will be wrapped in
        SSL. It then connects to the server, sets up the nick and user
        information, and then joins any specified channels."""

        self.socket = socket.socket()

        if config['port'] in [6697, 7000, 7070]:

            self.socket = ssl.wrap_socket(self.socket)

        self.socket.connect((config['server'], config['port']))
        self.__send('NICK %s\r\n' % config['nick'])
        self.__send('USER %(n)s %(n)s %(n)s :%(n)s\r\n' % {'n':config['nick']})

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

    def on(self, rule):

        """Execute a function when a message on IRC is matched to a regular
        expression (rule)."""

        def decorator(function):

            self.hooks.append({
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
        matching."""

        config = {
            'port': 6667,
            'server': 'chat.freenode.com',
        }

        config['nick'] = kwargs['nick']
        config['channels'] = kwargs['channels'].split(',')

        for key in ['port', 'server']:

            if key in kwargs.keys():

                config[key] = kwargs[key]

        self.__setup(config)

        while True:

            content = self.socket.recv(4096)

            if content[0:4] == "PING":

                self.__send('PONG %s \r\n' % content.split()[1])
                continue

            for line in content.split('\n'):

                line = str(line).strip()

                parsed = line.split(None, 3)

                if len(parsed) != 4:

                    continue

                context = {
                    'sender': parsed[0][1:].split('!')[0],
                    'type': parsed[1],
                    'target': parsed[2],
                    'message': parsed[3][1:]
                }

                if context['target'] == config['nick']:

                    context['target'] = context['sender'].split('!')[0]

                for hook in self.hooks:

                    match = hook['rule'].match(context['message'])

                    if match:

                        response = hook['function'](context, match.groups())

                        if response is not None:

                            self.speak(context['target'], response)
