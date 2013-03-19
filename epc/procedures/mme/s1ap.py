from ...messages.s1ap import s1SetupResponse, s1SetupFailure


class S1SetupProcedureHandler(object):

    def __init__(self, procedureParameters, enbPool, ioService, enbRegisteredCallback):
        self.procedureParameters = procedureParameters
        self.enbPool = enbPool
        self.ioService = ioService
        self.enbRegisteredCallback = enbRegisteredCallback
    
    def execute(self):
        def verifySettings():
            requiredProcedureParameters, requiredProcedureFlags = (
                ("mmeName", "servedGummeis", "timeToWait", "flags"),
                ("rejectS1SetupRequestsFromRegisteredEnbs",)
            )
            missingParameters = set(requiredProcedureParameters) - set(self.procedureParameters)
            missingFlags = set(requiredProcedureFlags) - set(self.procedureParameters["flags"])
            assert not missingParameters, "Missing parameters in mmeSettings: {}".format(missingParameters)
            assert not missingFlags, "Missing flags in procedureParameters['flags']: {}".format(missingFlags)
        verifySettings()
    
    def terminate(self):
        pass
    
    def handleIncomingS1SetupMessage(self, source, interface, channelInfo, message):
        def sendReject(destination, cause, timeToWait):
            self.ioService.sendMessage(destination, *s1SetupFailure(cause, timeToWait, None))
        
        def sendAccept(destination):
            params = (
                self.procedureParameters["mmeName"],
                self.procedureParameters["servedGummeis"],
                255, None
            )
            self.ioService.sendMessage(destination, *s1SetupResponse(*params))
        if self.enbPool.congested():
            sendReject(source, "congestion", self.procedureParameters["timeToWait"])
            return
        globalEnbId = message["globalEnbId"]
        if globalEnbId in self.enbPool and \
            self.procedureParameters["flags"]["rejectS1SetupRequestsFromRegisteredEnbs"]:
                sendReject(source, "unspecified", None)
                return
        sendAccept(source)
        self.enbRegisteredCallback(globalEnbId)