import time
import random

from ...messages.rrc import randomAccessResponse, contentionResolutionIdentity, rrcConnectionSetup


class RrcConnectionEstablishmentProcedure(object):

    Success, ErrorNoRRCConnectionCompleteMessage = range(2)

    def __init__(self, maxRrcConnectionSetupAttempts, rrcConnectionSetupTimeout, 
                 ioService, procedureCompleteCallback):

        self.maxRrcConnectionSetupAttempts = maxRrcConnectionSetupAttempts # not defined in standards
        self.rrcConnectionSetupTimeout = rrcConnectionSetupTimeout
        self.procedureCompleteCallback = procedureCompleteCallback
        self.ioService = ioService
        self.attemptNo = 0
        self.procedureCompleteCallbackExecuted = False

    def __notifyProcedureCompletion__(self, result):
        if result == self.Success:
            self.procedureCompleteCallback(result, self.ueCrnti, self.rrcTransactionIdentifier, 
                {"cRnti": self.ueCrnti, "ueIdentity": self.ueIdentity, 
                 "rrcEstablishmentCause": self.rrcEstablishmentCause, 
                "selectedPlmnIdentity": self.ueSelectedPlmnIdentity, "dedicatedInfoNas": self.uededicatedInfoNas})
        else:
            self.procedureCompleteCallback(result, self.ueCrnti, self.rrcTransactionIdentifier)

    def handleRrcEstablishmentMessages(self, source, interface, channelInfo, message, args=None):
        # bm: We should remove the 's' at the end of this function name
        #     We are handling only one message at a time, not a bulk of messages.
        #     [remove this comment after the fix]
        if message["messageName"] == "rrcConnectionRequest":
            # self.temporaryCrnti = channelInfo["cRnti"]
            self.rrcTransactionIdentifier = args["rrcTransactionIdentifier"]        
            self.ueAddress = source
            self.procedureCompleteCallbackExecuted = False             
            self.ueCrnti = channelInfo["cRnti"]
            self.ueIdentity = message["ueIdentity"]
            self.rrcEstablishmentCause = message["rrcEstablishmentCause"]
            self.__sendContentionResolutionIdentity__(message)
            time.sleep(0.2) # some delay before sending the next message
            self.__sendRrcConnectionSetup__()
        if ( (message["messageName"] == "rrcConnectionSetupComplete") and \
             (message["rrcTransactionIdentifier"] == self.rrcTransactionIdentifier) ):
            self.ueSelectedPlmnIdentity = message["selectedPlmnIdentity"]
            self.uededicatedInfoNas = message["dedicatedInfoNas"]
            if not self.procedureCompleteCallbackExecuted:
                self.ioService.cancelTimer('rrcConnectionSetupTimeout' + str(self.ueCrnti))
                self.__notifyProcedureCompletion__(self.Success)
                self.procedureCompleteCallbackExecuted = True

    def __sendContentionResolutionIdentity__(self, messageRrcConnectionRequest):
        messageRrcConnectionRequest["messageName"] = "contentionResolutionIdentity"
        interface, channelInfo, message = contentionResolutionIdentity(self.ueCrnti, messageRrcConnectionRequest)
        self.ioService.sendMessage(self.ueAddress, interface, channelInfo, message)

    def __sendRrcConnectionSetup__(self):
        interface, channelInfo, message = rrcConnectionSetup(self.ueCrnti, self.rrcTransactionIdentifier)
        self.attemptNo += 1
        self.ioService.sendMessage(self.ueAddress, interface, channelInfo, message)
        self.io
        self.ioService.startTimer('rrcConnectionSetupTimeout' + str(self.ueCrnti), self.rrcConnectionSetupTimeout,
            self.__onRrcConnectionSetupTimeout__)    

    def __onRrcConnectionSetupTimeout__(self, _):
        if self.attemptNo < self.maxRrcConnectionSetupAttempts:
            self.__sendRrcConnectionSetup__()
        else:
            self.__notifyProcedureCompletion__(self.ErrorNoRRCConnectionCompleteMessage)

    def returnRrcTransactionIdentifier(self):
        return self.rrcTransactionIdentifier