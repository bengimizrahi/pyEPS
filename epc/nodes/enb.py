import random
import time

from ..procedures.enb.rrc import RrcConnectionEstablishmentProcedure
from ..messages.rrc import randomAccessResponse


class Enb(object):

    def __init__(self, ioService):
        self.ioService = ioService
        self.ueContext = {}
        self.numRrcEstablishmentsHandled = 0
        self.rrcEstablishmentConclusions = []
        self.ongoingRrcEstablishmentProcedures = {}
        self.rrcTransactionIdToCrntiMapping = {}
        self.rrcTransIdIndex = 0
        self.cRntiIndex = 0
        self.rrcEstablishmentSuccess = {}

    def execute(self):
        self.ioService.addIncomingMessageCallback(self.__enbIncomingMessageCallback__)

    def __enbIncomingMessageCallback__(self, source, interface, channelInfo, message):
        if message["messageName"] == "randomAccessRequest":
            temporaryCrnti = self.__generateTemporaryCrnti__()
            uplinkGrant = self.__generateUplinkGrant__()
            self.__sendRandomAccessResponse__(source, interface, channelInfo, message, temporaryCrnti, uplinkGrant)
        if message["messageName"] == "rrcConnectionRequest":
            self.numRrcEstablishmentsHandled += 1
            cRnti = channelInfo["cRnti"]
            rrcTransactionIdentifier = self.__generateRrcTransactionIdentifier__()
            self.rrcTransactionIdToCrntiMapping[rrcTransactionIdentifier] = cRnti
            self.ongoingRrcEstablishmentProcedures[cRnti] = RrcConnectionEstablishmentProcedure(3, 0.5, 
                self.ioService, self.__enbRrcProcedureCompleteCallback__)
            self.ongoingRrcEstablishmentProcedures[cRnti].handleRrcEstablishmentMessage(source, interface,
                channelInfo, message, {"rrcTransactionIdentifier": rrcTransactionIdentifier})
        if message["messageName"] == "rrcConnectionSetupComplete":
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
        interface, channelInfo, message = randomAccessResponse(raRnti, rapid, temporaryCrnti, uplinkGrant)
        self.ioService.sendMessage(receivedSource, interface, channelInfo, message)

    def __generateTemporaryCrnti__(self):
        # need to update this routine to select appropriate cRnti
        self.cRntiIndex += 1
        return ((self.cRntiIndex - 1)  % 256)

    def __generateUplinkGrant__(self):
        # need to create a routine to generate uplink grant
        return random.randint(100,400)

    def __generateRrcTransactionIdentifier__(self):
        # need to create a routine to generate uplink grant
        self.rrcTransIdIndex += 1
        return ((self.rrcTransIdIndex - 1) % 256)

        # return 20 # for testing
        # bm: It is comment still valid?
        #     [remove comment after read]

    def __enbRrcProcedureCompleteCallback__(self, result, cRnti, rrcTransactionIdentifier, args=None):
        if result == RrcConnectionEstablishmentProcedure.Success:
            if not cRnti in self.ueContext:
                self.ueContext[cRnti] = args
        time.sleep(0.5) # wait for another RRC complete if outstanding
        del self.rrcTransactionIdToCrntiMapping[rrcTransactionIdentifier]
        del self.ongoingRrcEstablishmentProcedures[cRnti]
        self.rrcEstablishmentSuccess[cRnti] = result