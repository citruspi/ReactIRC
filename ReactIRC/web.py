import re
import threading
from wsgiref.simple_server import make_server
from . import conf, context

class Web(object):

    hooks = []
    __irc = None

    def __init__ (self, irc):

        self.__irc = irc

    def __404 (self, environ, start_response):

        start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
        return ['Route Not Defined.']

    def __200 (self, environ, start_response):

        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['']

    def __listen (self, environ, start_response):

        matched = False

        for hook in self.hooks:

            match = hook['rule'].search(environ.get('PATH_INFO', ''))

            if match:

                matched = True

                try:
                    body_size = int(environ.get('CONTENT_LENGTH', 0))
                except (ValueError):
                    body_size = 0

                environ['wsgi.input'] = environ['wsgi.input'].read(body_size)

                context = environ
                response = hook['function'](*match.groups())

                if response is not None:

                    if 'targets' not in response.keys():

                        pass

                    else:

                        for target in response['targets']:

                            self.__irc.speak(target, response['message'])

                return self.__200(environ, start_response)

        if not matched:

            return self.__404(environ, start_response)

    def add (self, rule):

        def decorator(function):

            self.hooks.append({
                'rule': re.compile(rule),
                'function': function
            })

            return function

        return decorator

    def __start_web (self):

        server = make_server(conf['web_host'], conf['web_port'], self.__listen)
        server.serve_forever()

    def monitor (self):

        thread = threading.Thread(target=self.__start_web, args=())
        thread.daemon = True
        thread.start()
