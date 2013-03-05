from ...messages.rrc import randomAccessRequest, rrcConnectionRequest, rrcConnectionSetupComplete

class RrcConnectionEstablishmentProcedure(object):
    
    Success, ErrorNoRandomAccessResponse, ErrorNoContentionResolutionIdentity, ErrorNoRrcConnectionSetup = range(4)
    
    def __init__(self, procedureParameters, enbAddress, ioService, procedureCompleteCallback):
        self.procedureParameters = procedureParameters
        self.enbAddress = enbAddress
        self.ioService = ioService
        self.procedureCompleteCallback = procedureCompleteCallback
        self.procedureCompleteCallbackExecuted = False
        self.attemptNo = 0
        self.waitForRandomAccessResponseTimer = None
        self.waitForRrcConnectionSetupTimerT300 = None
        self.waitForMacContentionResolutionTimer = None

    def execute(self):
        requiredParameters = ("initialNasMessage", "maxPrachPreambleAttempts", "prachPreambleRepeatDelay",
            "macContentionResolutionTimeout", "rrcConnectionSetupTimeoutT300")
        missingParameters = filter(lambda p: p not in self.procedureParameters, requiredParameters)
        if missingParameters:
            raise Exception("Missing RRC Connection Setup Procedure parameters: {}".format(missingParameters))
        self.ioService.addIncomingMessageCallback(self.__incomingMessageCallback__)
        self.__sendPrachPreamble__()

    def terminate(self):
        self.ioService.removeIncomingMessageCallback(self.__incomingMessageCallback__)

    def __notifyProcedureCompletion__(self, result):
        self.procedureCompleteCallback(result)

    def __cancelAllTimers__(self):
        for t in (self.waitForRandomAccessResponseTimer,
                self.waitForRrcConnectionSetupTimerT300, self.waitForMacContentionResolutionTimer):
            if t: t.cancel()

    def __incomingMessageCallback__(self, source, interface, channelInfo, message):
        if message["messageName"] == "randomAccessResponse":
            # assume Random Access Response is processed successfully
            self.waitForRandomAccessResponseTimer.cancel()
            self.__sendRrcConnectionRequest__()
        if message["messageName"] == "contentionResolutionIdentity":
            # assume MAC Contention Resolution Identity is processed successfully
            self.waitForMacContentionResolutionTimer.cancel()
        if message["messageName"] == "rrcConnectionSetup":
            # assume RRC Connection Setup is processed successfully
            self.waitForRrcConnectionSetupTimerT300.cancel()
            self.__sendRrcConnectionSetupComplete__()
            if not self.procedureCompleteCallbackExecuted:
                self.__notifyProcedureCompletion__(self.Success)
                self.procedureCompleteCallbackExecuted = True
        
    def __sendPrachPreamble__(self):
        self.attemptNo += 1
        self.ioService.sendMessage(self.enbAddress, *randomAccessRequest(1, 12))
        self.waitForRandomAccessResponseTimer = self.ioService.createTimer(
            self.procedureParameters["prachPreambleRepeatDelay"], self.__onRandomAccessResponseTimeout__)
        self.waitForRandomAccessResponseTimer.start()

    def __onRandomAccessResponseTimeout__(self):
        if self.attemptNo < self.procedureParameters["maxPrachPreambleAttempts"]:
            self.__sendPrachPreamble__()
        else:
            self.__notifyProcedureCompletion__(self.ErrorNoRandomAccessResponse)

    def __sendRrcConnectionRequest__(self):
        self.ioService.sendMessage(self.enbAddress, *rrcConnectionRequest(34343, "randomValue", 9989982, "moSignalling"))
        self.waitForRrcConnectionSetupTimerT300 = self.ioService.createTimer(
            self.procedureParameters["rrcConnectionSetupTimeoutT300"], self.__onRrcConnectionSetupTimeout__)
        self.waitForRrcConnectionSetupTimerT300.start()
        self.waitForMacContentionResolutionTimer = self.ioService.createTimer(
            self.procedureParameters["macContentionResolutionTimeout"], self.__onContentionResolutionTimeout__)
        self.waitForMacContentionResolutionTimer.start()
    
    def __onRrcConnectionSetupTimeout__(self):
        self.__cancelAllTimers__()
        self.__notifyProcedureCompletion__(self.ErrorNoRrcConnectionSetup)

    def __onContentionResolutionTimeout__(self):
        self.__cancelAllTimers__()
        self.__notifyProcedureCompletion__(self.ErrorNoContentionResolutionIdentity)
    
    def __sendRrcConnectionSetupComplete__(self):
        self.ioService.sendMessage(self.enbAddress,
            *rrcConnectionSetupComplete(5656, "2323", self.procedureParameters["initialNasMessage"]))
