from ...messages.gtpc import createSessionRequest
from epc.utils.io import localhost

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

    def execute(self, imsi, createSessionRequestParameters):
        requiredCreateSessionRequestParameters = {"pgwS5S8AddressForContolPlane", "pdnAddressAllocation",
                                                  "bearerContextsToBeCreated"}
        missingParameters = set(requiredCreateSessionRequestParameters) - set(createSessionRequestParameters)
        if missingParameters:
            raise Exception("S11 Create Session Request Missing Parameters: {}".format(missingParameters))
        if imsi in self.establishedS11Sessions:
            raise Exception("S11 GTPC Session already established for {}".format(imsi))
        self.createSessionRequestParameters = createSessionRequestParameters
        self.attemptNumber[imsi] = 0
        self.sequenceNumber[imsi] = self.nextGtpcHeaderSequenceNumber
        self.outstandingRequests[self.nextGtpcHeaderSequenceNumber] = {"imsi": imsi}
        self.sessionRequestMessage = \
            {"imsi": imsi,
             "senderFteidForControlPlane" : {"interfaceType": "ipv4", "teid": self.nextSenderTeidForControlPlane, 
                                              "address": localhost()},
             "pgwS5S8AddressForContolPlane": createSessionRequestParameters["pgwS5S8AddressForContolPlane"], 
             "pdnAddressAllocation": createSessionRequestParameters["pdnAddressAllocation"], 
             "bearerContextsToBeCreated": createSessionRequestParameters["bearerContextsToBeCreated"]
            }
        self.__sendCreateSessionRequest__(imsi)

    def handleIncomingMessage(self, source, interface, channelInfo, message):
        imsi = message["imsi"]
        self.waitForResponseTimer.cancel()
        self.__notifyProcedureCompletion__(self.Success)

    def __sendCreateSessionRequest__(self, imsi):
        self.attemptNumber[imsi] += 1
        self.ioService.sendMessage(self.sgwAddress, *createSessionRequest("s11","eutranInitialAttach", 0, 
                                                        self.nextGtpcHeaderSequenceNumber, self.sessionRequestMessage))
        self.waitForResponseTimer = self.ioService.createTimer(
            self.responseTimeoutT3, self.__onResponseTimeout__, imsi)
        self.waitForResponseTimer.start()
 
    def __onResponseTimeout__(self, imsi):
        if self.attemptNumber[imsi] < self.maxRequestAttempts:
            self.__sendCreateSessionRequest__(imsi)
        else:
            self.__notifyProcedureCompletion__(self.ErrorNoCreateSessionResponse)

    def __notifyProcedureCompletion__(self, result):
        self.procedureCompletionCallback(result)
        
    