import logging

from ...utils.statemachine import State
from ...messages.rrc import RRC_CONNECTION_SETUP_ESTABLISHMENT_PROCEDURE_MESSAGES
from ...procedures.enb.s1ap import S1SetupProcedure
from ...procedures.enb.rrc import RrcConnectionEstablishmentProcedureHandler

assertionLogger = logging.getLogger("assertions")


class Deregistered(State):

    def __init__(self, context):
        self.context = context

    def register(self):
        self.changeState(Registering)


class Registering(State):

    def __init__(self, context):
        self.context = context

    def __enter__(self):
        s1SetupRequestParameters = self.context["config"].getValue("s1.s1SetupParameters")
        mmeAddress = self.context["config"].getValue("s1.mmeAddress")
        self.procedure = S1SetupProcedure(s1SetupRequestParameters,
            mmeAddress, self.context["ioService"], self.__onS1SetupProgress__)
        self.procedure.execute()

    def handleIncomingMessage(self, *args):
        self.procedure.handleIncomingMessage(*args)

    def __onS1SetupProgress__(self, progress):
        if progress == S1SetupProcedure.ProgressSuccess:
            self.changeState(Registered)


class Registered(State):

    def __init__(self, context):
        self.context = context
        rrcParameters = self.context["config"].getValue("rrc")
        maxRrcConnectionSetupAttempts, rrcConnectionSetupTimeout = \
            [rrcParameters[k] for k in "maxRrcConnectionSetupAttempts", "rrcConnectionSetupTimeout"]
        self.rrcConnectionEstablishmentProcedureHandler =  \
            RrcConnectionEstablishmentProcedureHandler(
            maxRrcConnectionSetupAttempts, rrcConnectionSetupTimeout,
            self.context["ioService"], self.__handleNewRrcConnectionEstablishment__)
        self.ues = {}

    def handleIncomingMessage(self, source, interface, channelInfo, message):
        if interface == "uu":
            if message["messageName"] in RRC_CONNECTION_SETUP_ESTABLISHMENT_PROCEDURE_MESSAGES:
                self.rrcConnectionEstablishmentProcedureHandler.handleIncomingMessage(
                    source, interface, channelInfo, message)
            else:
                assertionLogger.info("Not handling DCH messages yet")
        elif interface == "s1":
            assertionLogger.info("Not handling S1AP messages yet")

    def __onNewRrcConnectionEstablishment__(self, cRnti, args):
        self.ues[cRnti] = args
