from eps.messages.s1ap import s1SetupRequest


class S1SetupProcedure(object):

    (ProgressSuccess, ProgressWaitForNextAttempt, ProgressFailedWithCauseUnknownPlmn,
     ProgressFailedWithCauseUnspecified) = range(4)

    def __init__(self, s1SetupRequestParameters, mmeAddress, ioService, procedureProgressCallback):
        self.s1SetupRequestParameters = s1SetupRequestParameters
        self.mmeAddress = mmeAddress
        self.ioService = ioService
        self.procedureProgressCallback = procedureProgressCallback
        self.waitForNextAttemptTimer = None

    def execute(self):
        requiredParameters = ("globalEnbId", "enbName", "supportedTas", "csgIdList", "defaultPagingDrx")
        missingParameters = set(requiredParameters) - set(self.s1SetupRequestParameters)
        if missingParameters:
            raise Exception("Missing S1 Setup parameters: {}".format(missingParameters))
        self.__sendS1SetupRequest__()

    def terminate(self):
        if self.waitForNextAttemptTimer:
            self.waitForNextAttemptTimer.cancel()

    def __sendS1SetupRequest__(self):
        self.ioService.sendMessage(self.mmeAddress, *s1SetupRequest(**self.s1SetupRequestParameters))

    def __resendS1SetupRequest__(self):
        self.waitForNextAttemptTimer = None
        self.__sendS1SetupRequest__()

    def handleIncomingMessage(self, source, interface, channelInfo, message):
        def handleS1SetupResponse(s1SetupResponse):
            mmeProperties = {
                "name": s1SetupResponse["mmeName"],
                "servedGummeis": s1SetupResponse["servedGummeis"],
                "relativeMmeCapacity": s1SetupResponse["relativeMmeCapacity"],
                "criticalityDiagnostics": s1SetupResponse["criticalityDiagnostics"]
            }
            self.procedureProgressCallback(self.ProgressSuccess, mmeProperties)

        def handleS1SetupFailure(s1SetupFailure):
            assert not s1SetupFailure["criticalityDiagnostics"], \
                "Don't know how to handle CriticalityDiagnostics IE in an S1 Setup Failure"
            timeToWait = s1SetupFailure["timeToWait"]
            if timeToWait:
                self.waitForNextAttemptTimer = self.ioService.createTimer(timeToWait, self.__resendS1SetupRequest__)
                self.waitForNextAttemptTimer.start()
                self.procedureProgressCallback(self.ProgressWaitForNextAttempt)
                return
            progress = (s1SetupFailure["cause"] == "unknownPlmn" and self.ProgressFailedWithCauseUnknownPlmn or
                self.ProgressFailedWithCauseUnspecified)
            self.__notifyProcedureProgress__(progress)
        mapping = {
            ("s1Setup", "successfulOutcome"): handleS1SetupResponse,
            ("s1Setup", "unsuccessfulOutcome"): handleS1SetupFailure,
        }
        procedureCode = message["messageType"]["procedureCode"]
        typeOfMessage = message["messageType"]["typeOfMessage"]
        assert mapping.get((procedureCode, typeOfMessage), "Cannot handle message: {}".format(message))
        mapping[procedureCode, typeOfMessage](message)
