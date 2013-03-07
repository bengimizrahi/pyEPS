import time

from ...messages.rrc import contentionResolutionIdentity, rrcConnectionSetup


class RrcConnectionEstablishmentProcedure(object):

    Success, ErrorNoRrcConnectionCompleteMessage = range(2)

    def __init__(self, maxRrcConnectionSetupAttempts, rrcConnectionSetupTimeout, 
            ioService, procedureCompleteCallback):
        self.maxRrcConnectionSetupAttempts = maxRrcConnectionSetupAttempts # not defined in standards
        self.rrcConnectionSetupTimeout = rrcConnectionSetupTimeout
        self.procedureCompleteCallback = procedureCompleteCallback
        self.ioService = ioService
        self.attemptNo = 0
        self.rrcConnectionSetupTimer = None
        self.procedureCompleteCallbackExecuted = False

    def __notifyProcedureCompletion__(self, result):
        if result == self.Success:
            self.procedureCompleteCallback(result, self.ueCrnti, self.rrcTransactionIdentifier, {
                "cRnti": self.ueCrnti,
                "ueIdentity": self.ueIdentity,
                "rrcEstablishmentCause": self.rrcEstablishmentCause,
                "selectedPlmnIdentity": self.ueSelectedPlmnIdentity,
                "dedicatedInfoNas": self.ueDedicatedInfoNas
            })
        else:
            self.procedureCompleteCallback(result, self.ueCrnti, self.rrcTransactionIdentifier)

    def handleRrcEstablishmentMessage(self, source, interface, channelInfo, message, args=None):
        if message["messageName"] == "rrcConnectionRequest":
            # self.temporaryCrnti = channelInfo["cRnti"]
            # bm: does this comment still make sense?
            #     [remove bm's comment if so]
            self.rrcTransactionIdentifier = args["rrcTransactionIdentifier"]        
            self.ueAddress = source
            self.procedureCompleteCallbackExecuted = False             
            self.ueCrnti = channelInfo["cRnti"]
            self.ueIdentity = message["ueIdentity"]
            self.rrcEstablishmentCause = message["rrcEstablishmentCause"]
            self.__sendContentionResolutionIdentity__(message)
            time.sleep(0.2) # some delay before sending the next message
            # bm: Why is this 0.2sec delay important?
            #     [remove bm's comment after read]
            self.__sendRrcConnectionSetup__()
        if message["messageName"] == "rrcConnectionSetupComplete":
            assert message["rrcTransactionIdentifier"] == self.rrcTransactionIdentifier
            self.ueSelectedPlmnIdentity = message["selectedPlmnIdentity"]
            self.ueDedicatedInfoNas = message["dedicatedInfoNas"]
            if not self.procedureCompleteCallbackExecuted:
                self.rrcConnectionSetupTimer.cancel()
                self.__notifyProcedureCompletion__(self.Success)
                self.procedureCompleteCallbackExecuted = True

    def __sendContentionResolutionIdentity__(self, messageRrcConnectionRequest):
        messageRrcConnectionRequest["messageName"] = "contentionResolutionIdentity"
        self.ioService.sendMessage(self.ueAddress, *contentionResolutionIdentity(
            self.ueCrnti, messageRrcConnectionRequest))

    def __sendRrcConnectionSetup__(self):
        self.attemptNo += 1
        self.ioService.sendMessage(self.ueAddress,
            *rrcConnectionSetup(self.ueCrnti, self.rrcTransactionIdentifier))
        self.rrcConnectionSetupTimer = self.ioService.createTimer(
            self.rrcConnectionSetupTimeout, self.__onRrcConnectionSetupTimeout__)
        self.rrcConnectionSetupTimer.start()

    def __onRrcConnectionSetupTimeout__(self):
        if self.attemptNo < self.maxRrcConnectionSetupAttempts:
            self.__sendRrcConnectionSetup__()
        else:
            self.__notifyProcedureCompletion__(self.ErrorNoRrcConnectionCompleteMessage)

    def returnRrcTransactionIdentifier(self):
        return self.rrcTransactionIdentifier