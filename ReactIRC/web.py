import re
from wsgiref.simple_server import make_server

class Web(object):

    __hooks = []
    __connection = None

    def __init__ (self, connection):

        self.__connection = connection

    def __404 (self, environ, start_response):

        start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
        return ['Route Not Defined.']

    def __200 (self, environ, start_response):

        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['']

    def __listen (self, environ, start_response):

        matched = False

        for hook in self.__hooks:

            match = hook['rule'].search(environ.get('PATH_INFO', ''))

            if match:

                matched = True

                try:
                    body_size = int(environ.get('CONTENT_LENGTH', 0))
                except (ValueError):
                    body_size = 0

                environ['wsgi.input'] = environ['wsgi.input'].read(body_size)

                self.__connection.request = environ
                response = hook['function'](*match.groups())

                if response is not None:

                    if 'targets' not in response.keys():

                        pass

                    else:

                        for target in response['targets']:

                            self.__connection.speak(target, response['message'])

                return self.__200(environ, start_response)

        if not matched:

            return self.__404(environ, start_response)

    def add (self, rule):

        def decorator(function):

            self.__hooks.append({
                'rule': re.compile(rule),
                'function': function
            })

            return function

        return decorator

    def monitor (self):

        server = make_server('0.0.0.0', 8080, self.__listen)
        server.serve_forever()
