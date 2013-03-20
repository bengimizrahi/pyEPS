class ConfigPath(str):
    pass


class Configuration(object):

    def __init__(self, content, ioService):
        self.content = content
        self.ioService = ioService
        self.listeners = []

    def addListener(self, path, callback):
        if isinstance(path, str):
            path = path.split(".")
        self.listeners.append((path, callback))

    def removeListener(self, callback):
        self.listeners.remove(callback)

    def __getValueAtPath__(self, path):
        it = self.content
        for s in path:
            it = it[s]
        if isinstance(it, ConfigPath):
            return self.getValue(it)
        return it

    def setValue(self, path, value):
        if isinstance(path, str) or isinstance(path, ConfigPath):
            path = path.split(".")
        try:
            it = self.__getValueAtPath__(path[:-1])
            it[path[-1]] = value
        except KeyError:
            raise Exception("path '{}' does not exist".format(".".join(path)))
        for p, cb in self.listeners:
            if len(path) < len(p):
                continue
            if not all((a == b for a, b in zip(path, p))):
                continue
            self.ioService.asyncCall(cb, path, value)

    def getValue(self, path):
        if isinstance(path, str) or isinstance(path, ConfigPath):
            path = path.split(".")
        try:
            return self.__getValueAtPath__(path)
        except KeyError:
            raise Exception("path '{}' does not exist".format(".".join(path)))
