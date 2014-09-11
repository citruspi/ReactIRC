import re
import threading
from . import conf, connection, context

class IRC (object):

    hooks = []

    def add(self, rule):

        """Execute a function when a message on IRC is matched to a regular
        expression (rule).
        """

        def decorator(function):

            # Add the function and the regular expression to the list of
            # functions and expressions to check
            self.hooks.append({
                'rule': re.compile(rule),
                'function': function,
            })

            return function

        return decorator

    def speak(self, target, message):

        """Send a message to user or a channel."""

        connection.send("PRIVMSG %s :%s\r\n" % (target, message))

    def join(self, channel):

        """Join a channel."""

        connection.send('JOIN %s\r\n' % channel)

    def part(self, channel):

        """Leave a channel."""

        connection.send('PART %s\r\n' % channel)

    def quit(self):

        """Disconnect from the server."""

        connection.send('QUIT\r\n')

    def __listen(self):

        while True:

            # Read in some data
            content = connection.receive(4096)

            # If it's a timeout PING...
            if content[0:4] == "PING":

                #... respond with a PONG
                connection.send('PONG %s \r\n' % content.split()[1])
                continue

            # Otherwise, break up the data by line
            for line in content.split('\n'):

                # Strip any unnecessary characters off the ends
                line = str(line).strip()

                if conf['verbose']:

                    print line

                # Break up the line
                parsed = line.split(None, 3)

                if len(parsed) != 4:

                    continue

                # Parse out the sender, type, target, and message body
                context = {
                    'sender': parsed[0][1:].split('!')[0],
                    'type': parsed[1],
                    'target': parsed[2],
                    'message': parsed[3][1:]
                }

                # If it's a private message, set the target to the sender
                if context['target'] == conf['nick']:

                    context['target'] = context['sender']

                # Iterate over the functions with an .on() decorator
                for hook in self.hooks:

                    match = hook['rule'].search(context['message'])

                    if match:

                        if conf['debug']:

                            print '---'
                            print context
                            print match.groups()

                        # Call the function with capture groups as parameters
                        response = hook['function'](*match.groups())

                        # If the function actually returned something print it
                        # to the IRC channel
                        if response is not None:

                            self.speak(context['target'], response)

    def monitor (self):

        connection.send('NICK %s\r\n' % conf['nick'])

        nick = {'n': conf['nick']}
        connection.send('USER %(n)s %(n)s %(n)s :%(n)s\r\n' % nick)

        # Join each of the specified channels
        for channel in conf['channels']:

            self.join(channel)

        irc_thread = threading.Thread(target=self.__listen, args=())
        irc_thread.daemon = True
        irc_thread.start()
