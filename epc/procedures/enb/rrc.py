import time
import random
from collections import Counter

from ...messages.rrc import contentionResolutionIdentity, rrcConnectionSetup, randomAccessResponse


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
            self.procedureCompleteCallback(result, self.cRnti, self.rrcTransactionIdentifier, {
                "cRnti": self.cRnti,
                "rrcTransactionIdentifier": self.rrcTransactionIdentifier,
                "ueIdentity": self.ueIdentity,
                "rrcEstablishmentCause": self.rrcEstablishmentCause,
                "selectedPlmnIdentity": self.ueSelectedPlmnIdentity,
                "dedicatedInfoNas": self.ueDedicatedInfoNas
            })
        else:
            self.procedureCompleteCallback(result, self.cRnti, self.rrcTransactionIdentifier)

    def handleRrcEstablishmentMessage(self, source, interface, channelInfo, message, args=None):
        if message["messageName"] == "rrcConnectionRequest":
            self.rrcTransactionIdentifier = args["rrcTransactionIdentifier"]        
            self.ueAddress = source
            self.cRnti = channelInfo["cRnti"]
            self.ueIdentity = message["ueIdentity"]
            self.rrcEstablishmentCause = message["rrcEstablishmentCause"]
            self.__sendContentionResolutionIdentity__(message)
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
            self.cRnti, messageRrcConnectionRequest))

    def __sendRrcConnectionSetup__(self):
        self.attemptNo += 1
        self.ioService.sendMessage(self.ueAddress,
            *rrcConnectionSetup(self.cRnti, self.rrcTransactionIdentifier))
        self.rrcConnectionSetupTimer = self.ioService.createTimer(
            self.rrcConnectionSetupTimeout, self.__onRrcConnectionSetupTimeout__)
        self.rrcConnectionSetupTimer.start()

    def __onRrcConnectionSetupTimeout__(self):
        if self.attemptNo < self.maxRrcConnectionSetupAttempts:
            self.__sendRrcConnectionSetup__()
        else:
            self.__notifyProcedureCompletion__(self.ErrorNoRrcConnectionCompleteMessage)
            # bm: Should we not set precedureCompleteCallbackExecuted to True
            #     [Remove comment after read]

    def returnRrcTransactionIdentifier(self):
        return self.rrcTransactionIdentifier


class RrcConnectionEstablishmentProcedureHandler(object):

    def __init__(self, maxRrcConnectionSetupAttempts, rrcConnectionSetupTimeout, ioService, onNewRrcConnectionEstablishmentCallback):
        self.maxRrcConnectionSetupAttempts = maxRrcConnectionSetupAttempts;
        self.rrcConnectionSetupTimeout = rrcConnectionSetupTimeout
        self.ioService = ioService
        self.newRrcConnectionEstablishmentCallback = onNewRrcConnectionEstablishmentCallback
        self.ongoingRrcEstablishmentProcedures = {}
        self.rrcTransactionIdToCrntiMapping = {}
        self.rrcTransIdIndex = 0
        self.cRntiIndex = 0
        self.kpis = Counter(
            numRandomAccessRequestsReceived = 0,
            numRrcConnectionRequestsReceived = 0,
            numRrcConnectionSetupCompletesReceived = 0,
            numRrcConnectionEstablishmentFailures = 0,
            numRrcConnectionEstablishmentSuccesses = 0
        )

    def __sendRandomAccessResponse__(self, destination, raRnti, rapid,
            temporaryCrnti, uplinkGrant):
        self.ioService.sendMessage(destination, *randomAccessResponse(
            raRnti, rapid, temporaryCrnti, uplinkGrant))

    def __generateTemporaryCrnti__(self):
        # need to update this routine to select appropriate cRnti
        self.cRntiIndex += 1
        return ((self.cRntiIndex - 1)  % 256)

    def __generateUplinkGrant__(self):
        # need to create a routine to generate uplink grant
        return random.randint(100,400)

    def __generateRrcTransactionIdentifier__(self):
        # need to create a routine to generate transaction id
        self.rrcTransIdIndex += 1
        return ((self.rrcTransIdIndex - 1) % 256)

    def __procedureCompleteCallback__(self, result, cRnti, rrcTransactionIdentifier, args=None):
        kpiName = (result == RrcConnectionEstablishmentProcedure.Success and
            "numRrcConnectionEstablishmentSuccesses" or "numRrcConnectionEstablishmentFailures")
        self.kpis[kpiName] += 1
        if result == RrcConnectionEstablishmentProcedure.Success:
            self.newRrcConnectionEstablishmentCallback(args)
        del self.rrcTransactionIdToCrntiMapping[rrcTransactionIdentifier]
        del self.ongoingRrcEstablishmentProcedures[cRnti]

    def handleIncomingMessage(self, source, interface, channelInfo, message):
        if message["messageName"] == "randomAccessRequest":
            self.kpis["numRandomAccessRequestsReceived"] += 1
            temporaryCrnti = self.__generateTemporaryCrnti__()
            uplinkGrant = self.__generateUplinkGrant__()
            raRnti = channelInfo["raRnti"]
            rapid = message["rapid"]
            self.__sendRandomAccessResponse__(source, raRnti, rapid, temporaryCrnti, uplinkGrant)
        if message["messageName"] == "rrcConnectionRequest":
            self.kpis["numRrcConnectionRequestsReceived"] += 1
            cRnti = channelInfo["cRnti"]
            rrcTransactionIdentifier = self.__generateRrcTransactionIdentifier__()
            self.rrcTransactionIdToCrntiMapping[rrcTransactionIdentifier] = cRnti
            self.ongoingRrcEstablishmentProcedures[cRnti] = RrcConnectionEstablishmentProcedure(3, 0.5,
                self.ioService, self.__procedureCompleteCallback__)
            self.ongoingRrcEstablishmentProcedures[cRnti].handleRrcEstablishmentMessage(source, interface,
                channelInfo, message, {"rrcTransactionIdentifier": rrcTransactionIdentifier})
        if message["messageName"] == "rrcConnectionSetupComplete":
            self.kpis["numRrcConnectionSetupCompletesReceived"] += 1
            rrcTransactionIdentifier = message["rrcTransactionIdentifier"]
            if rrcTransactionIdentifier in self.rrcTransactionIdToCrntiMapping:
                cRnti = self.rrcTransactionIdToCrntiMapping[rrcTransactionIdentifier]
                self.ongoingRrcEstablishmentProcedures[cRnti].handleRrcEstablishmentMessage(source, interface,
                    channelInfo, message)
            else:
                print "Transaction Identifier {} not provided by this eNB. Message ignored:{}".format(rrcTransactionIdentifier, message)