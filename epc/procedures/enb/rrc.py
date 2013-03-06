import time
import random

from ...messages import randomAccessResponse, contentionResolutionIdentity, rrcConnectionSetup

class EnbMain(object):
    def __init__(self, ioService):
        self.ioService = ioService
        self.ueContext = {}
        self.numRrcEstablishmentPorceduresActive = 0
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
            self.numRrcEstablishmentPorceduresActive += 1
            self.numRrcEstablishmentsHandled += 1
            cRnti = channelInfo["cRnti"]
            rrcTransactionIdentifier = self.__generateRrcTrasactionIdentifier__()
            self.rrcTransactionIdToCrntiMapping[rrcTransactionIdentifier] = cRnti
            # create an object to handle the rrc establishment procedure
            self.ongoingRrcEstablishmentProcedures[cRnti] = EnbRrcConnectionEstablishmentProcedure(3, 0.5, 
                    self.ioService, self.__enbRrcProcedureCompleteCallback__)
            self.ongoingRrcEstablishmentProcedures[cRnti].handleRrcEstablishmentMessages(source, interface, 
                    channelInfo, message, {"rrcTransactionIdentifier": rrcTransactionIdentifier})
        if message["messageName"] == "rrcConnectionSetupComplete":
            rrcTransactionIdentifier = message["rrcTransactionIdentifier"]
            if rrcTransactionIdentifier in self.rrcTransactionIdToCrntiMapping:
                cRnti = self.rrcTransactionIdToCrntiMapping[rrcTransactionIdentifier]
                self.ongoingRrcEstablishmentProcedures[cRnti].handleRrcEstablishmentMessages(source, interface, 
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
        # return 200  # for testing

    def __generateUplinkGrant__(self):
        # need to create a routine to generate uplink grant
        return random.randint(100,400)

    def __generateRrcTrasactionIdentifier__(self):
        # need to create a routine to generate uplink grant
        self.rrcTransIdIndex += 1
        return ((self.rrcTransIdIndex - 1) % 256)

        # return 20 # for testing

    def __enbRrcProcedureCompleteCallback__(self, result, cRnti, rrcTransactionIdentifier, args=None):
        if result == EnbRrcConnectionEstablishmentProcedure.Success:
            if not cRnti in self.ueContext:
                self.ueContext[cRnti] = args
        self.numRrcEstablishmentPorceduresActive -= 1
        time.sleep(0.5) # wait for another RRC complete if outstanding        
        del self.rrcTransactionIdToCrntiMapping[rrcTransactionIdentifier]
        del self.ongoingRrcEstablishmentProcedures[cRnti]
        self.rrcEstablishmentSuccess[cRnti] = result

class EnbRrcConnectionEstablishmentProcedure(object):
    
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
        self.ioService.startTimer('rrcConnectionSetupTimeout' + str(self.ueCrnti), self.rrcConnectionSetupTimeout,
            self.__onRrcConnectionSetupTimeout__)    
    
    def __onRrcConnectionSetupTimeout__(self, _):
        if self.attemptNo < self.maxRrcConnectionSetupAttempts:
            self.__sendRrcConnectionSetup__()
        else:
            self.__notifyProcedureCompletion__(self.ErrorNoRRCConnectionCompleteMessage)
            
    def returnRrcTransactionIdentifier(self):
        return self.rrcTransactionIdentifier