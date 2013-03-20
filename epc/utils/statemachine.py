import logging
import pprint

assertionLogger = logging.getLogger("assertions")


class StateMachine(object):

    def __init__(self):
        self.state = None
        self.setContext(None)

    def setContext(self, context):
        self.context = context

    def changeState(self, stateClass):
        if hasattr(self.state, "__exit__"):
            self.state.__exit__()
        self.state = stateClass(self.context)
        self.state.stateMachine = self
        if hasattr(self.state, "__enter__"):
            self.state.__enter__()

    def handleCommand(self, command, *args, **kwargs):
        self.state.handleCommand(command, *args, **kwargs)

    def handleIncomingMessage(self, *args):
        if not self.state.handleIncomingMessage(*args):
            assertionLogger.info("'{}' received unknown message {}".format(
                self.state.__class__.__name__, pprint.pformat(args)))


class State(object):

    def changeState(self, stateClass):
        self.stateMachine.changeState(stateClass)

    def handleCommand(self, command, *args, **kwargs):
        def handleUnknownCommand(self, command, *args, **kwargs):
            assertionLogger.info("'{}' received unknown command: {}".format(
                self.__class__.__name__, pprint.pformat(command, (args, kwargs))))
        getattr(self, command, handleUnknownCommand)(*args, **kwargs)
