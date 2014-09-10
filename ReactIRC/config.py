class Config(dict):

    def __init__ (self):

        self['server'] = 'chat.freenode.com'
        self['port'] = 6667
        self['debug'] = False
        self['verbose'] = False
        self['web_host'] = '0.0.0.0'
        self['web_port'] = 8080

    def __getattr__(self, attr):

        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError(item)

    def __setattr__ (self, attr, value):

        if self.__dict__.has_key(item):       # any normal attributes are handled normally
            dict.__setattr__(self, attr, value)
        else:
            self.__setitem__(attr, value)
