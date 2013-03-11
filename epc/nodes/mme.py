from ..utils.io import IoService, localhost


class Enb(object):

    def __init__(self, globalEnbId):
        self.globalEnbId = globalEnbId


class EnbPool(dict):

    def __init__(self, maxEnbsAllowed):
        self.maxEnbsAllowed = maxEnbsAllowed

    def add(self, globalEnbId):
        if globalEnbId in self:
            del self[globalEnbId]
        self[globalEnbId] = Enb(globalEnbId)

    def congested(self):
        return not len(self) < self.maxEnbsAllowed


# FIXME: This class is incomplete
class Mme(object):

    def __init__(self, name, port, mmeSettings):
        self.name = name
        self.port = port
        self.mmeSettings = mmeSettings
        self.ioService = None

    def execute(self):
        def verifySettings():
            requiredParameters, requiredFlags = (
                ("mmeName", "servedGummeis", "maxNumEnbsServed", "flags"),
                ("rejectS1SetupRequestsFromRegisteredEnbs")
            )
            missingParameters, missingFlags = map(
                lambda items: filter(lambda p: p not in self.mmeSettings, items),
                (requiredParameters, requiredFlags)
            )
            assert not missingParameters, "Missing parameters in mmeSettings: {}".format(missingParameters)
            assert not missingFlags, "Missing flags in mmeSettings['flags']: {}".format(missingFlags)

        def startIoService():
            self.ioService = IoService("mme", (localhost(), self.port))
            self.ioService.addIncomingMessageCallback(self.__incomingMessageCallback__)
            self.ioService.start()
        verifySettings()
        startIoService()

    def terminate(self):
        self.ioService.stop()

    def __incomingMessageCallback__(self, source, interface, channelInfo, message):
        def handleS1SetupRequestMessage(s1SetupRequest):
            globalEnbId = s1SetupRequest["globalEnbId"]

        def handleOtherMessages(message):
            pass
        mapping = {
            ("s1Setup", "initiatingMessage"): handleS1SetupRequestMessage,
        }
        procedureCode = message["messageType"]["procedureCode"]
        typeOfMessage = message["messageType"]["typeOfMessage"]
        mapping.get((procedureCode, typeOfMessage), handleOtherMessages)(message)