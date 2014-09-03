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

    def monitor(self, **kwargs):

        config = {
            'nick': kwargs['nick'],
            'port': kwargs['port'],
            'server': kwargs['server'],
            'channel': kwargs['channel']
        }

        self.socket = socket.socket()

        self.socket.connect((config['server'], config['port']))
        self.socket.send('NICK %s\r\n' % config['nick'])
        self.socket.send('USER %s %s %s :%s\r\n' % (config['nick'], config['nick'], config['nick'], config['nick']))
        self.socket.send('JOIN #%s\r\n' % config['channel'])

        while True:

            content = self.socket.recv(4096)

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
                        self.socket.send("PRIVMSG %s :%s\r\n" % (context['target'], response))
