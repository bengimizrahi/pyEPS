from messages import randomAccessRequest, rrcConnectionRequest, rrcConnectionSetupComplete

class RrcConnectionEstablishmentProcedure(object):
    
    Success, ErrorNoRandomAccessResponse, ErrorNoRrcConnectionSetup = range(3)
    
    def __init__(self, maxAttempts, repeatDelay, enbAddress, ioService,
            procedureCompleteCallback):
        self.maxAttempts = maxAttempts # Defined as PREAMBLE_TRANS_MAX in 3GPP, this is actually read from SIB2
        self.repeatDelay = repeatDelay
        self.enbAddress = enbAddress
        self.ioService = ioService
        self.attemptNo = 0
        self.procedureCompleteCallback = procedureCompleteCallback

    def execute(self):
        self.ioService.addIncomingMessageCallback(self.__incomingMessageCallback__)
        self.__sendPrachPreamble__()

    def terminate(self):
        self.ioService.removeIncomingMessageCallback(self.__incomingMessageCallback__)

    def __notifyProcedureCompletion__(self, result):
        self.terminate()
        self.procedureCompleteCallback(result)

    def __incomingMessageCallback__(self, source, interface, channelInfo, message):
        if message["messageName"] == "randomAccessResponse":
            # assume Random Access Response is processed successfully
            self.ioService.cancelTimer("randomAccessResponseTimeout")
            self.__sendRrcConnectionRequest__()
        if message["messageName"] == "rrcConnectionSetup":
            # assume RRC Connection Setup is processed successfully
            self.ioService.cancelTimer("rrcConnectionSetupTimeout")
            self.__sendRrcConnectionSetupComplete__()
        
    def __sendPrachPreamble__(self):
        self.attemptNo += 1
        interface, channelInfo, message = randomAccessRequest(1, 12)
        self.ioService.sendMessage(self.enbAddress, interface, channelInfo, message)
        self.ioService.startTimer("randomAccessResponseTimeout", self.repeatDelay,
            self.__onRandomAccessResponseTimeout__)

    def __onRandomAccessResponseTimeout__(self, _):
        if self.attemptNo < self.maxAttempts:
            self.__sendPrachPreamble__()
        else:
            self.__notifyProcedureCompletion__(self.ErrorNoRandomAccessResponse)

    def __sendRrcConnectionRequest__(self):
        interface, channelInfo, message = rrcConnectionRequest(34343, 9989982, "moSignalling")
        self.ioService.sendMessage(self.enbAddress, interface, channelInfo, message)
        self.ioService.startTimer("rrcConnectionSetupTimeout", 1.0,
            self.__onRccConnectionSetupTimeout__)
    
    def __onRccConnectionSetupTimeout__(self, _):
        self.__notifyProcedureCompletion__(self.ErrorNoRrcConnectionSetup)
    
    def __sendRrcConnectionSetupComplete__(self):
        interface, channelInfo, message = rrcConnectionSetupComplete(5656, "2323", {})
        self.ioService.sendMessage(self.enbAddress, interface, channelInfo, message)
        self.__notifyProcedureCompletion__(self.Success)
