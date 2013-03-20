from ...utils.statemachine import State
from epc.procedures.mme.s1ap import S1SetupProcedureHandler


class MmeState(State):

    def __init__(self, context):
        super(MmeState, self).__init__()
        self.ioService = context["ioService"]
        self.config = context["config"]


class Default(MmeState):

    def __init__(self, context):
        super(Default, self).__init__(context)

    def __enter__(self):
        maxEnbsAllowed = self.config.getValue("system.maximumEnbsAllowed")
        self.mmeServiceArea = self.MmeServiceArea(maxEnbsAllowed)
        s1SetupProcedureParameters = {
            "mmeName": self.config.getValue("system.mmeName"),
            "servedGummeis": self.config.getValue("system.servedGummeis"),
            "timeToWait": self.config.getValue("s1.s1SetupTimeToWait"),
            "flags": {
                "rejectS1SetupRequestsFromRegisteredEnbs": False,
            },
        }
        self.s1SetupProcedureHandler = S1SetupProcedureHandler(
            s1SetupProcedureParameters, self.mmeServiceArea, self.ioService,
            self.__handleNewEnbRegistration__)

    def __handleNewEnbRegistration__(self, address, globalEnbId):
        self.mmeServiceArea.add(address, globalEnbId)

    def handleIncomingMessage(self, source, interface, channelInfo, message):
        def handleS1SetupMessage():
            self.s1SetupProcedureHandler.handleIncomingS1SetupMessage(
                source, interface, channelInfo, message)

        def handleOtherMessages():
            pass
        mapping = {
            "s1Setup": handleS1SetupMessage,
        }
        procedureCode = message["messageType"]["procedureCode"]
        mapping.get(procedureCode, handleOtherMessages)(message)


    class MmeServiceArea(object):

        def __init__(self, maxEnbsAllowed):
            self.maxEnbsAllowed = maxEnbsAllowed
            self.enbs = {}

        def add(self, address, globalEnbId):
            if globalEnbId in self.enbs:
                return
            self.enbs[globalEnbId] = self.Enb(globalEnbId, address)

        def congested(self):
            return not len(self.enbs) < self.maxEnbsAllowed


    class Enb(object):

        def __init__(self, globalEnbId, address):
            self.globalEnbId = globalEnbId
            self.address = address
