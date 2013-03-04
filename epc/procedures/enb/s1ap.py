from ...messages.s1ap import s1SetupRequest

class S1SetupProcedure(object):

    (ProgressSuccess, ProgressWaitForNextAttempt, ProgressFailedWithCauseUnknownPlmn,
     ProgressFailedWithCauseUnspecified) = range(4)

    def __init__(self, s1SetupParameters, mmeAddress, ioService, procedureProgressCallback):
        self.s1SetupParameters = s1SetupParameters
        self.mmeAddress = mmeAddress
        self.ioService = ioService
        self.procedureProgressCallback = procedureProgressCallback
        self.nextAttemptTimerRunning = False

    def execute(self):
        assert all((k in self.s1SetupParameters for k in
            "globalEnbId", "enbName", "supportedTas", "csgIdList", "defaultPagingDrx"))
        self.ioService.addIncomingMessageCallback(self.__incomingMessageCallback__)
        self.__sendS1SetupRequest__()

    def terminate(self):
        if self.nextAttemptTimerRunning:
            self.ioService.cancelTimer("waitForNextAttempt")
        self.ioService.removeIncomingMessageCallback(self.__incomingMessageCallback__)

    def __notifyProcedureProgress__(self, progress):
        self.procedureProgressCallback(progress)

    def __sendS1SetupRequest__(self, _=None):
        interface, channelInfo, message = s1SetupRequest(self.s1SetupParameters)
        self.ioService.sendMessage(self.mmeAddress, interface, channelInfo, message)

    def __incomingMessageCallback__(self, source, interface, channelInfo, message):
        if message["messageType"]["procedureCode"] == "s1setup" and \
                message["messageType"]["typeOfMessage"] == "successfulOutcome":
            self.__handleS1SetupResponse__(message)
        elif message["messageType"]["procedureCode"] == "s1setup" and \
                message["messageType"]["typeOfMessage"] == "unsuccessfulOutcome":
            self.__handleS1SetupFailure__(message)

    def __handleS1SetupResponse__(self, s1SetupResponse):
        # Assume S1 Setup Response is processed successfully
        self.__notifyProcedureProgress__(self.ProgressSuccess)

    def __handleS1SetupFailure__(self, s1SetupFailure):
        assert not s1SetupFailure["criticalityDiagnostics"], \
            "Don't know how to handle CriticalityDiagnostics IE in an S1 Setup Failure"
        timeToWait = s1SetupFailure["timeToWait"]
        if timeToWait:
            self.ioService.startTimer("waitForNextAttempt", timeToWait, self.__sendS1SetupRequest__)
            self.nextAttemptTimerRunning = True
            self.__notifyProcedureProgress__(self.ProgressWaitForNextAttempt)
            return
        progress = (s1SetupFailure["cause"] == "unknownPlmn" and self.ProgressFailedWithCauseUnknownPlmn or
            self.ProgressFailedWithCauseUnspecified)
        self.__notifyProcedureProgress__(progress)
