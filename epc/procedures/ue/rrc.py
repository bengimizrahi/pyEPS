from ...messages import randomAccessRequest, rrcConnectionRequest, rrcConnectionSetupComplete

class RrcConnectionEstablishmentProcedure(object):
    
    Success, ErrorNoRandomAccessResponse, ErrorNoContentionResolutionIdentity, ErrorNoRrcConnectionSetup = range(4)
    
    def __init__(self, initialNasMessage, maxPrachPreambleAttempts, prachPreambleRepeatDelay, 
                 macContentionResolutionTimeout, rrcConnectionSetupTimeoutT300, enbAddress, ioService,
                 procedureCompleteCallback):
        self.initialNasMessage = initialNasMessage
        self.maxPrachPreambleAttempts = maxPrachPreambleAttempts # Defined as PREAMBLE_TRANS_MAX in 3GPP, this is actually read from SIB2
        self.prachPreambleRepeatDelay = prachPreambleRepeatDelay
        self.macContentionResolutionTimeout = macContentionResolutionTimeout
        self.rrcConnectionSetupTimeoutT300 = rrcConnectionSetupTimeoutT300
        self.enbAddress = enbAddress
        self.ioService = ioService
        self.procedureCompleteCallback = procedureCompleteCallback
        self.procedureCompleteCallbackExecuted = False
        self.attemptNo = 0

    def execute(self):
        self.ioService.addIncomingMessageCallback(self.__incomingMessageCallback__)
        self.__sendPrachPreamble__()

    def terminate(self):
        self.ioService.removeIncomingMessageCallback(self.__incomingMessageCallback__)

    def __notifyProcedureCompletion__(self, result):
        self.procedureCompleteCallback(result)

    def __incomingMessageCallback__(self, source, interface, channelInfo, message):
        if message["messageName"] == "randomAccessResponse":
            # assume Random Access Response is processed successfully
            self.ioService.cancelTimer("randomAccessResponseTimeout")
            self.__sendRrcConnectionRequest__()
        if message["messageName"] == "contentionResolutionIdentity":
            # assume RRC Connection Setup is processed successfully
            self.ioService.cancelTimer("macContentionResolutionTimeout")
        if message["messageName"] == "rrcConnectionSetup":
            # assume RRC Connection Setup is processed successfully
            self.ioService.cancelTimer("rrcConnectionSetupTimeoutT300")
            self.__sendRrcConnectionSetupComplete__()
            if not self.procedureCompleteCallbackExecuted:
                self.__notifyProcedureCompletion__(self.Success)
                self.procedureCompleteCallbackExecuted = True
        
    def __sendPrachPreamble__(self):
        self.attemptNo += 1
        interface, channelInfo, message = randomAccessRequest(1, 12)
        self.ioService.sendMessage(self.enbAddress, interface, channelInfo, message)
        self.ioService.startTimer("randomAccessResponseTimeout", self.prachPreambleRepeatDelay,
            self.__onRandomAccessResponseTimeout__)

    def __onRandomAccessResponseTimeout__(self, _):
        if self.attemptNo < self.maxPrachPreambleAttempts:
            self.__sendPrachPreamble__()
        else:
            self.__notifyProcedureCompletion__(self.ErrorNoRandomAccessResponse)

    def __sendRrcConnectionRequest__(self):
        interface, channelInfo, message = rrcConnectionRequest(34343, "randomValue", 9989982, "moSignalling")
        self.ioService.sendMessage(self.enbAddress, interface, channelInfo, message)
        self.ioService.startTimer("rrcConnectionSetupTimeoutT300", self.rrcConnectionSetupTimeoutT300,
            self.__onRrcConnectionSetupTimeout__)
        self.ioService.startTimer("macContentionResolutionTimeout", self.macContentionResolutionTimeout,
            self.__onContentionResolutionTimeout__)
    
    def __onRrcConnectionSetupTimeout__(self, _):
        self.__notifyProcedureCompletion__(self.ErrorNoRrcConnectionSetup)

    def __onContentionResolutionTimeout__(self, _):
        self.__notifyProcedureCompletion__(self.ErrorNoContentionResolutionIdentity)
    
    def __sendRrcConnectionSetupComplete__(self):
        interface, channelInfo, message = rrcConnectionSetupComplete(5656, "2323", self.initialNasMessage)
        self.ioService.sendMessage(self.enbAddress, interface, channelInfo, message)
