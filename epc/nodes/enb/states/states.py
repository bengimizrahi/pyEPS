import logging

from ....utils.statemachine import State
from ....procedures.enb.s1ap import S1SetupProcedure
from ....procedures.enb.rrc import RrcConnectionEstablishmentProcedureHandler

assertionLogger = logging.getLogger("assertions")


class Deregistered(State):

    def __init__(self, enb):
        super(Deregistered, self).__init__(enb)

    def register(self):
        self.enb.changeState(Registering)


class Registering(State):

    def __init__(self, enb):
        super(Registering, self).__init__(enb)

    def __enter__(self):
        s1SetupRequestParameters = self.enb.config.getValue("s1.s1SetupParameters")
        mmeAddress = self.enb.config.getValue("s1.mmeAddress")
        self.procedure = S1SetupProcedure(s1SetupRequestParameters, mmeAddress, self.enb.ioService, self.__onS1SetupProgress__)
        self.procedure.execute()

    def handleIncomingMessage(self, *args):
        self.procedure.handleIncomingMessage(*args)

    def __onS1SetupProgress__(self, progress):
        if progress == S1SetupProcedure.ProgressSuccess:
            self.enb.state = Registered(self.enb)


class Registered(State):

    def __init__(self, enb):
        super(Registered, self).__init__(enb)
