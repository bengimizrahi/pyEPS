from ...messages.gtpc import createSessionRequest

class S11CreateSessionRequestProcedureHandler(object):

    Success, ErrorNoCreateSessionResponse = range(2)

    def __init__(self, sgwAddress, ioService, responseTimeoutT3, maxRequestAttemptsN3, procedureCompletionCallback):
        self.sgwAddress = sgwAddress
        self.ioService = ioService
        self.procedureCompletionCallback = procedureCompletionCallback
        self.responseTimeoutT3 = responseTimeoutT3
        self.maxRequestAttempts = maxRequestAttemptsN3
        self.nextGtpcHeaderSequenceNumber = 0
        self.nextSenderTeidForControlPlane = 0
        self.outstandingRequests = {}
        self.establishedS11Sessions = {}
        self.attemptNumber = {}
        self.sequenceNumber = {}
        self.message = {}
        self.waitForResponseTimer = {}

    def execute(self, imsi, createSessionRequestMessage):
        if imsi in self.establishedS11Sessions:
            raise Exception("S11 GTPC Session already established for {}".format(imsi))
        self.attemptNumber[imsi] = 0
        self.sequenceNumber[imsi] = self.nextGtpcHeaderSequenceNumber
        self.outstandingRequests[self.nextGtpcHeaderSequenceNumber] = {"imsi": imsi}
        self.sessionRequestMessage = createSessionRequestMessage
        self.__sendCreateSessionRequest__(imsi)

    def handleIncomingMessage(self, source, interface, channelInfo, message):
        imsi = message["imsi"]
        self.waitForResponseTimer[imsi].cancel()
        self.__notifyProcedureCompletion__(self.Success, message["cause"])

    def __sendCreateSessionRequest__(self, imsi):
        self.attemptNumber[imsi] += 1
        self.ioService.sendMessage(self.sgwAddress, *createSessionRequest("s11","eutranInitialAttach", 0, 
                                                        self.nextGtpcHeaderSequenceNumber, self.sessionRequestMessage))
        self.waitForResponseTimer[imsi] = self.ioService.createTimer(
            self.responseTimeoutT3, self.__onResponseTimeout__, imsi)
        self.waitForResponseTimer[imsi].start()
 
    def __onResponseTimeout__(self, imsi):
        if self.attemptNumber[imsi] < self.maxRequestAttempts:
            self.__sendCreateSessionRequest__(imsi)
        else:
            self.__notifyProcedureCompletion__(self.ErrorNoCreateSessionResponse)

    def __notifyProcedureCompletion__(self, result, responseMessageCause=None):
        self.procedureCompletionCallback(result, responseMessageCause)
        
    