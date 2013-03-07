import random
import time
from collections import Counter

from ..procedures.enb.rrc import RrcConnectionEstablishmentProcedure
from ..messages.rrc import randomAccessResponse


class Enb(object):

    def __init__(self, ioService):
        self.ioService = ioService
        self.ueContext = {}
        self.numRrcEstablishmentsHandled = 0
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

    def execute(self):
        self.ioService.addIncomingMessageCallback(self.__incomingMessageCallback__)

    def __incomingMessageCallback__(self, source, interface, channelInfo, message):
        if message["messageName"] == "randomAccessRequest":
            self.kpis["numRandomAccessRequestsReceived"] += 1
            temporaryCrnti = self.__generateTemporaryCrnti__()
            uplinkGrant = self.__generateUplinkGrant__()
            self.__sendRandomAccessResponse__(source, interface, channelInfo, message, temporaryCrnti, uplinkGrant)
        if message["messageName"] == "rrcConnectionRequest":
            self.kpis["numRrcConnectionRequestsReceived"] += 1
            cRnti = channelInfo["cRnti"]
            rrcTransactionIdentifier = self.__generateRrcTransactionIdentifier__()
            self.rrcTransactionIdToCrntiMapping[rrcTransactionIdentifier] = cRnti
            self.ongoingRrcEstablishmentProcedures[cRnti] = RrcConnectionEstablishmentProcedure(3, 0.5, 
                self.ioService, self.__rrcProcedureCompleteCallback__)
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

    def __sendRandomAccessResponse__(self, receivedSource, receivedInterface,
            receivedChannelInfo, receivedMessage, temporaryCrnti, uplinkGrant):
        raRnti = receivedChannelInfo["raRnti"]
        rapid = receivedMessage["rapid"]
        self.ioService.sendMessage(receivedSource, *randomAccessResponse(
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

    def __rrcProcedureCompleteCallback__(self, result, cRnti, rrcTransactionIdentifier, args=None):
        kpiName = (result == RrcConnectionEstablishmentProcedure.Success and
            "numRrcConnectionEstablishmentSuccesses" or
            "numRrcConnectionEstablishmentFailures")
        self.kpis[kpiName] += 1
        if result == RrcConnectionEstablishmentProcedure.Success:
            if not cRnti in self.ueContext:
                self.ueContext[cRnti] = args
        time.sleep(0.5) # wait for another RRC complete if outstanding
        del self.rrcTransactionIdToCrntiMapping[rrcTransactionIdentifier]
        del self.ongoingRrcEstablishmentProcedures[cRnti]