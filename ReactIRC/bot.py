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

    def configure(self, configuration):

        self.configuration = configuration

    def monitor(self):

        self.socket = socket.socket()

        self.socket.connect((self.configuration['server'], self.configuration['port']))
        self.socket.send('NICK %s\r\n' % self.configuration['username'])
        self.socket.send('USER %s %s %s :%s\r\n' % (self.configuration['username'], self.configuration['username'], self.configuration['username'], self.configuration['username']))
        self.socket.send('JOIN #%s\r\n' % self.configuration['channel'])

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

                for hook in self.hooks:

                	  match = hook['rule'].match(context['message'])

                	  if match:

                	      response = hook['function'](context, match.groups())
                	      self.socket.send("PRIVMSG %s :%s\r\n" % (context['target'], response))
