import random

from ...messages.rrc import randomAccessRequest, rrcConnectionRequest, rrcConnectionSetupComplete

class RrcConnectionEstablishmentProcedure(object):
    
    Success, ErrorNoRandomAccessResponse, ErrorNoContentionResolutionIdentity, ErrorNoRrcConnectionSetup = range(4)
    
    def __init__(self, procedureParameters, enbAddress, ioService, procedureCompleteCallback, args=None):
        # bm: I gathered all the parameters into 'procedureParameters',
        #     looks like you also gathered the rest into 'args'. You might
        #     want to either:
        #     -  Group them all into one dictionary, or
        #     -  Redistribute the items inside 'procedureParameters' and 'args'
        #        so that the groups make sense. Ex: seems like 'initialNasMessage'
        #        should be moved to 'args'. After that you might also want to
        #        rename 'procedureParameters' & 'args' to something else that makes
        #        it more self-documented (optional).
        #     [remove this comment after done]
        self.procedureParameters = procedureParameters
        self.enbAddress = enbAddress
        self.ioService = ioService
        self.procedureCompleteCallback = procedureCompleteCallback
        self.ueIdentityType = args["ueIdentityType"]
        self.ueIdentityValue = args["ueIdentityValue"]
        self.rrcEstablishmentCause = args["rrcEstablishmentCause"]
        self.selectedPlmnIdentity = args["selectedPlmnIdentity"]
        self.procedureCompleteCallbackExecuted = False
        self.attemptNo = 0
        self.waitForRandomAccessResponseTimer = None
        self.waitForRrcConnectionSetupTimerT300 = None
        self.waitForMacContentionResolutionTimer = None
        self.raRnti = self.__generateRarnti__()
        self.rapid = self.__generateRapid__()

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

    def __generateRarnti__(self):
        return random.randint(0,10)
    
    def __generateRapid__(self):
        return random.randint(0,63)
    
    def __notifyProcedureCompletion__(self, result):
        self.procedureCompleteCallback(result)

    def __cancelAllTimers__(self):
        for t in (self.waitForRandomAccessResponseTimer,
                self.waitForRrcConnectionSetupTimerT300, self.waitForMacContentionResolutionTimer):
            if t: t.cancel()

    def __incomingMessageCallback__(self, source, interface, channelInfo, message):
        if message["messageType"] == "randomAccessResponse":
            if channelInfo["raRnti"] == self.raRnti and \
                    message["rapid"] == self.rapid:
                self.waitForRandomAccessResponseTimer.cancel()
                self.temporaryCrnti = message["temporaryCrnti"]
                self.__sendRrcConnectionRequest__()
        elif message["messageType"] == "contentionResolutionIdentity":
            # need to check here if the message content is the same as that send in rrc connection request
            message["messageType"] = self.rrcConnectionRequestMessage["messageType"]
            if message == self.rrcConnectionRequestMessage:
                self.waitForMacContentionResolutionTimer.cancel()
        elif message["messageType"] == "rrcConnectionSetup":
            if channelInfo["puschScramblingInput"] == self.temporaryCrnti:
                self.rrcTransactionIdentifier = message["rrcTransactionIdentifier"]
                self.__sendRrcConnectionSetupComplete__()
                if not self.procedureCompleteCallbackExecuted:
                    self.waitForRrcConnectionSetupTimerT300.cancel()
                    self.__notifyProcedureCompletion__(self.Success)
                    self.procedureCompleteCallbackExecuted = True
    
    def __sendPrachPreamble__(self):
        self.attemptNo += 1
        self.ioService.sendMessage(self.enbAddress, *randomAccessRequest(self.raRnti, self.rapid))
        self.waitForRandomAccessResponseTimer = self.ioService.createTimer(
            self.procedureParameters["prachPreambleRepeatDelay"], self.__onRandomAccessResponseTimeout__)
        self.waitForRandomAccessResponseTimer.start()

    def __onRandomAccessResponseTimeout__(self):
        if self.attemptNo < self.procedureParameters["maxPrachPreambleAttempts"]:
            self.__sendPrachPreamble__()
        else:
            self.__notifyProcedureCompletion__(self.ErrorNoRandomAccessResponse)

    def __sendRrcConnectionRequest__(self):
        interface, channelInfo, message = rrcConnectionRequest(34343, "randomValue", 9989982, "moSignalling")
        self.ioService.sendMessage(self.enbAddress, interface, channelInfo, message)
        self.rrcConnectionRequestMessage = message # need to store this to compre with macCRI
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
        self.ioService.sendMessage(self.enbAddress, *rrcConnectionSetupComplete(self.rrcTransactionIdentifier, 
            self.selectedPlmnIdentity, self.procedureParameters["initialNasMessage"]))
