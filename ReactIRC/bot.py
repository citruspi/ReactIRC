import socket
import re
import pprint

class Bot(object):

    hooks = []

    def on(self, rule, **options):

        def decorator(f):

            self.hooks.append({
                'rule': re.compile(rule),
                'function': f
            })

            return f

        return decorator

    def __send(self, message):

        self.socket.send(message)

    def __setup(self, config):

        self.socket = socket.socket()

        self.socket.connect((config['server'], config['port']))
        self.__send('NICK %s\r\n' % config['nick'])
        self.__send('USER %s %s %s :%s\r\n' % (config['nick'], config['nick'], config['nick'], config['nick']))
        self.__join(config['channel'])

    def __join(self, channel):

        self.__send('JOIN #%s\r\n' % channel)

    def monitor(self, **kwargs):

        config = {
            'port': 6667,
            'server': 'chat.freenode.com',
        }

        config['nick'] = kwargs['nick']
        config['channel'] = kwargs['channel']

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
                    'sender': parsed[0][1:],
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
                        self.__send("PRIVMSG %s :%s\r\n" % (context['target'], response))
