from eps.utils.io import IoService
from eps.utils.statemachine import StateMachine
from eps.utils.config import Configuration
from eps.nodes.enb.states import Deregistered

# Configuration data model
#
# {
#  "control": {
#   "adminState": bool(),
#  },
#  "rrc": {
#   "maxRrcConnectionSetupAttempts": int(),
#   "rrcConnectionSetupTimeout": float(),
#  },
#  "mme": {
#   "address": (str(), int()),
#   "s1SetupParameters": dict(),
#   "properties": None or {
#    "name": str(),
#    "servedGummeis": [((), (), ()), ...],
#    "relativeMmeCapacity": int(),
#    "criticalityDiagnostics": ?
#   }
#  },
# }

class Enb(StateMachine):

    def __init__(self, name, port, configData):
        super(Enb, self).__init__()
        self.ioService = IoService(name, port)
        self.config = Configuration(configData, self.ioService)
        self.setContext({"config": self.config, "ioService": self.ioService})

    def execute(self):
        self.ioService.addIncomingMessageCallback(self.handleIncomingMessage)
        self.ioService.start()
        self.config.addListener("control.adminState", self.__onAdminStateChanged__)
        self.changeState(Deregistered)
        if self.config.getValue("control.adminState"):
            self.handleCommand("register")

    def __onAdminStateChanged__(self, _, adminState):
        mapping = {True: "register", False: "deregister"}
        self.handleCommand(mapping[adminState])

    def terminate(self):
        self.ioService.stop()
