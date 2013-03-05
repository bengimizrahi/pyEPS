from ...messages.s1ap import s1SetupRequest

class S1SetupProcedure(object):

    (ProgressSuccess, ProgressWaitForNextAttempt, ProgressFailedWithCauseUnknownPlmn,
     ProgressFailedWithCauseUnspecified) = range(4)

    def __init__(self, s1SetupRequestParameters, mmeAddress, ioService, procedureProgressCallback):
        self.s1SetupRequestParameters = s1SetupRequestParameters
        self.mmeAddress = mmeAddress
        self.ioService = ioService
        self.procedureProgressCallback = procedureProgressCallback
        self.nextAttemptTimerRunning = False

    def execute(self):
        requiredParameters = ("globalEnbId", "enbName", "supportedTas", "csgIdList", "defaultPagingDrx")
        missingParameters = filter(lambda p: p not in self.s1SetupRequestParameters, requiredParameters)
        if missingParameters:
            raise Exception("Missing S1 Setup parameters: {}".format(missingParameters))
        self.ioService.addIncomingMessageCallback(self.__incomingMessageCallback__)
        self.__sendS1SetupRequest__()

    def terminate(self):
        if self.nextAttemptTimerRunning:
            self.ioService.cancelTimer("waitForNextAttempt")
        self.ioService.removeIncomingMessageCallback(self.__incomingMessageCallback__)

    def __sendS1SetupRequest__(self):
        self.ioService.sendMessage(self.mmeAddress, *s1SetupRequest(**self.s1SetupRequestParameters))

    def __resendS1SetupRequest__(self, _=None):
        self.nextAttemptTimerRunning = False
        self.__sendS1SetupRequest__()

    def __incomingMessageCallback__(self, source, interface, channelInfo, message):
        mapping = {
            ("s1Setup", "successfulOutcome"): self.__handleS1SetupResponse__,
            ("s1Setup", "unsuccessfulOutcome"): self.__handleS1SetupFailure__,
        }
        procedureCode = message["messageType"]["procedureCode"]
        typeOfMessage = message["messageType"]["typeOfMessage"]
        assert mapping.get((procedureCode, typeOfMessage), "Cannot handle message: {}".format(message))
        mapping[procedureCode, typeOfMessage](message)

    def __handleS1SetupResponse__(self, s1SetupResponse):
        # Assume S1 Setup Response is processed successfully
        s1SetupResponseParameters = {}
        self.procedureProgressCallback(self.ProgressSuccess, s1SetupResponseParameters)

    def __handleS1SetupFailure__(self, s1SetupFailure):
        assert not s1SetupFailure["criticalityDiagnostics"], \
            "Don't know how to handle CriticalityDiagnostics IE in an S1 Setup Failure"
        timeToWait = s1SetupFailure["timeToWait"]
        if timeToWait:
            self.ioService.startTimer("waitForNextAttempt", timeToWait, self.__resendS1SetupRequest__)
            self.nextAttemptTimerRunning = True
            self.procedureProgressCallback(self.ProgressWaitForNextAttempt)
            return
        progress = (s1SetupFailure["cause"] == "unknownPlmn" and self.ProgressFailedWithCauseUnknownPlmn or
            self.ProgressFailedWithCauseUnspecified)
        self.__notifyProcedureProgress__(progress)
