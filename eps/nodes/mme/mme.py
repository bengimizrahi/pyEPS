from eps.utils.io import IoService
from eps.utils.statemachine import StateMachine
from eps.utils.config import Configuration
from eps.nodes.mme.states import Default

# Configuration data model
# {
#  "system": {
#   "mmeName": str(),
#   "servedGummeis": [((), (), ()), ...],
#   "maximumEnbsAllowed": int(),
#  },
#  "s1": {
#   "s1SetupTimeToWait": int(),
#  },
# }

class Mme(StateMachine):

    def __init__(self, name, port, configData):
        super(Mme, self).__init__()
        self.ioService = IoService(name, port)
        self.config = Configuration(configData, self.ioService)
        self.setContext({"config": self.config, "ioService": self.ioService})

    def execute(self):
        self.ioService.addIncomingMessageCallback(self.handleIncomingMessage)
        self.ioService.start()
        self.changeState(Default)

    def terminate(self):
        self.ioService.stop()
