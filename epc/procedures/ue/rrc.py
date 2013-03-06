import random

from ...messages import randomAccessRequest, rrcConnectionRequest, rrcConnectionSetupComplete

class RrcConnectionEstablishmentProcedure(object):
    
    Success, ErrorNoRandomAccessResponse, ErrorNoContentionResolutionIdentity, ErrorNoRrcConnectionSetup = range(4)
    
    def __init__(self, initialNasMessage, maxPrachPreambleAttempts, prachPreambleRepeatDelay, 
                 macContentionResolutionTimeout, rrcConnectionSetupTimeoutT300, enbAddress, ioService,
                 procedureCompleteCallback, args=None):
        self.initialNasMessage = initialNasMessage
        self.maxPrachPreambleAttempts = maxPrachPreambleAttempts # Defined as PREAMBLE_TRANS_MAX in 3GPP, this is actually read from SIB2
        self.prachPreambleRepeatDelay = prachPreambleRepeatDelay
        self.macContentionResolutionTimeout = macContentionResolutionTimeout
        self.rrcConnectionSetupTimeoutT300 = rrcConnectionSetupTimeoutT300
        self.raRnti = self.__generateRarnti__()
        self.rapid = self.__generateRapid__()
        self.enbAddress = enbAddress
        self.ioService = ioService
        self.procedureCompleteCallback = procedureCompleteCallback
        self.ueIdentityType = args["ueIdentityType"]
        self.ueIdentityValue = args["ueIdentityValue"]
        self.rrcEstablishmentCause = args["rrcEstablishmentCause"]
        self.selectedPlmnIdentity = args["selectedPlmnIdentity"]
        self.procedureCompleteCallbackExecuted = False
        self.attemptNo = 0

    def execute(self):
        self.ioService.addIncomingMessageCallback(self.__incomingMessageCallback__)
        self.__sendPrachPreamble__()

    def terminate(self):
        self.ioService.removeIncomingMessageCallback(self.__incomingMessageCallback__)

    def __generateRarnti__(self):
        return random.randint(0,10)
    
    def __generateRapid__(self):
        return random.randint(0,63)
    
    def __notifyProcedureCompletion__(self, result):
        self.procedureCompleteCallback(result)

    def __incomingMessageCallback__(self, source, interface, channelInfo, message):
        if message["messageName"] == "randomAccessResponse":
            if channelInfo["raRnti"] == self.raRnti and \
                    message["rapid"] == self.rapid:
                self.ioService.cancelTimer("randomAccessResponseTimeout")
                self.temporaryCrnti = message["temporaryCrnti"]
                self.__sendRrcConnectionRequest__()
        elif message["messageName"] == "contentionResolutionIdentity":
            # need to check here if the message content is the same as that send in rrc connection request
            message["messageName"] = self.rrcConnectionRequestMessage["messageName"]
            if message == self.rrcConnectionRequestMessage:
                self.ioService.cancelTimer("macContentionResolutionTimeout")
        elif message["messageName"] == "rrcConnectionSetup":
            if channelInfo["puschScramblingInput"] == self.temporaryCrnti:
                self.rrcTransactionIdentifier = message["rrcTransactionIdentifier"]
                self.__sendRrcConnectionSetupComplete__()
                if not self.procedureCompleteCallbackExecuted:
                    self.ioService.cancelTimer("rrcConnectionSetupTimeoutT300")
                    self.__notifyProcedureCompletion__(self.Success)
                    self.procedureCompleteCallbackExecuted = True
    
    def __sendPrachPreamble__(self):
        self.attemptNo += 1
        interface, channelInfo, message = randomAccessRequest(self.raRnti, self.rapid)
        self.ioService.sendMessage(self.enbAddress, interface, channelInfo, message)
        self.ioService.startTimer("randomAccessResponseTimeout", self.prachPreambleRepeatDelay,
            self.__onRandomAccessResponseTimeout__)

    def __onRandomAccessResponseTimeout__(self, _):
        if self.attemptNo < self.maxPrachPreambleAttempts:
            self.__sendPrachPreamble__()
        else:
            self.__notifyProcedureCompletion__(self.ErrorNoRandomAccessResponse)

    def __sendRrcConnectionRequest__(self):
        interface, channelInfo, message = rrcConnectionRequest(self.temporaryCrnti, 
                                            self.ueIdentityType, self.ueIdentityValue, self.rrcEstablishmentCause)
        self.ioService.sendMessage(self.enbAddress, interface, channelInfo, message)
        self.rrcConnectionRequestMessage = message # need to store this to compre with macCRI
        self.ioService.startTimer("rrcConnectionSetupTimeoutT300", self.rrcConnectionSetupTimeoutT300,
            self.__onRrcConnectionSetupTimeout__)
        self.ioService.startTimer("macContentionResolutionTimeout", self.macContentionResolutionTimeout,
            self.__onContentionResolutionTimeout__)
    
    def __onRrcConnectionSetupTimeout__(self, _):
        self.__notifyProcedureCompletion__(self.ErrorNoRrcConnectionSetup)

    def __onContentionResolutionTimeout__(self, _):
        self.__notifyProcedureCompletion__(self.ErrorNoContentionResolutionIdentity)
    
    def __sendRrcConnectionSetupComplete__(self):
        interface, channelInfo, message = rrcConnectionSetupComplete(self.rrcTransactionIdentifier, 
                                                self.selectedPlmnIdentity, self.initialNasMessage)
        self.ioService.sendMessage(self.enbAddress, interface, channelInfo, message)
