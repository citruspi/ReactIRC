class Config(dict):

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
