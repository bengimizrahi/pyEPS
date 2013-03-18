from ...utils.io import IoService
from ...utils.statemachine import StateMachine
from ...utils.config import Configuration
from ...nodes.enb.states.states import Deregistered

# Configuration data model
#
# {
#  "control": {
#   "adminState": bool(),
#  },
#  "ioService": {
#   "name": str(),
#   "port": int(),
#  }
#  "s1": {
#   "mmeAddress": (str(), int()),
#   "s1SetupParameters": dict(),
#  }
# }

class Enb(StateMachine):

    def __init__(self, configData):
        super(Enb, self).__init__()
        self.config = Configuration(configData)
        ioServiceParameters = self.config.getValue("ioService")
        self.ioService = IoService(*(ioServiceParameters[k] for k in "name", "port"))
        self.state = None

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
