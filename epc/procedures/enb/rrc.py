import time
import random

from ...messages import randomAccessResponse, contentionResolutionIdentity, rrcConnectionSetup

class EnbMain(object):
    def __init__(self, ioService):
        self.ioService = ioService
        self.ueContextInfo = {}
        self.numRrcEstablishmentPorceduresActive = 0
        self.numRrcEstablishmentsHandled = 0
        self.rrcEstablishmentConclusions = []
        self.ongoingRrcEstablishmentProcedures = {}
        self.rrcTransactionIdToCrntiMapping = {}
        
    def execute(self):    
        self.ioService.addIncomingMessageCallback(self.__enbIncomingMessageCallback__)
        
    def __enbIncomingMessageCallback__(self, source, interface, channelInfo, message):
        if message["messageName"] == "randomAccessRequest":
            self.__sendRandomAccessResponse__(source, interface, channelInfo, message)
        if message["messageName"] == "rrcConnectionRequest":
            self.numRrcEstablishmentPorceduresActive += 1
            self.numRrcEstablishmentsHandled += 1
            temporaryCrnti = self.__generateTemporaryCrnti__()
            uplinkGrant = self.__generateUplinkGrant__()
            rrcTransactionIdentifier = self.__generateRrcTrasactionIdentifier__()
            self.rrcTransactionIdToCrntiMapping[rrcTransactionIdentifier] = temporaryCrnti
            # create an object to handle the rrc establishment procedure
            self.ongoingRrcEstablishmentProcedures[temporaryCrnti] = EnbRrcConnectionEstablishmentProcedure(3, 0.5, 
                    self.ioService, self.__enbRrcProcedureCompleteCallback__)
            self.ongoingRrcEstablishmentProcedures[temporaryCrnti].handleRrcConnectionMessages(source, interface, 
                    channelInfo, message, {"temporaryCrnti": temporaryCrnti, 
                                            "uplinkGrant": uplinkGrant, "rrcTransactionIdentifier": rrcTransactionIdentifier})
        if message["messageName"] == "rrcConnectionSetupComplete":
            rrcTransactionIdentifier = message["rrcTransactionIdentifier"]
            if rrcTransactionIdentifier in self.rrcTransactionIdToCrntiMapping:
                temporaryCrnti = self.rrcTransactionIdToCrntiMapping[rrcTransactionIdentifier]
                self.ongoingRrcEstablishmentProcedures[temporaryCrnti].handleRrcConnectionMessages(source, interface, 
                    channelInfo, message)
            else:
                print "Transaction Identifier {} not provided by this eNB. Message ignored:{}".format(rrcTransactionIdentifier, message)
                
    def __sendRandomAccessResponse__(self,receivedSource,receivedInterface,receivedChannelInfo, receivedMessage):
        raRnti = receivedChannelInfo["raRnti"]
        rapid = receivedMessage["rapid"]
        interface, channelInfo, message = randomAccessResponse(raRnti, rapid,self.temporaryCrnti)
        self.ioService.sendMessage(self.ueAddress, interface, channelInfo, message)
        
    def __generateTemporaryCrnti__(self):
        # need to update this routine to select appropriate cRnti
        # return random.randint(1,100)
        return 200  # for testing

    def __generateUplinkGrant__(self):
        # need to create a routine to generate uplink grant
        return random.randint(100,400)

    def __generateRrcTrasactionIdentifier__(self):
        # need to create a routine to generate uplink grant
        # return random.randint(100,400)
        return 20 # for testing

    def __enbRrcProcedureCompleteCallback__(self, result, args=None):
        if result == EnbRrcConnectionEstablishmentProcedure.Success:
            if not args["cRnti"] in self.ueContext:
                self.ueContext[args["cRnti"]] = args  # need to find out how to handle removing the cRnti from args
        self.numRrcEstablishmentPorceduresActive -= 1
        self.rrcEstablishmentConclusions.append(result)
        time.sleep(2)
        rrcTransactionIdentifier = self.ongoingRrcEstablishmentProcedures.returnRrcTransactionIdentifier()
        del self.rrcTransactionIdToCrntiMapping[rrcTransactionIdentifier]
        del self.ongoingRrcEstablishmentProcedures[args["Crnti"]]
   

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
            self.procedureCompleteCallback(result, {"cRnti": self.ueCrnti, "identityType": self.ueIdentityType, 
                "indentityValue": self.ueIdentityValue, "establishmentCause": self.rrcEstablishmentCause, 
                "selectedPlmnIdentity": self.ueSelectedPlmnIdentity, "dedicatedInfoNas": self.uededicatedInfoNas})
        else:
            self.procedureCompleteCallback(result)
            
    def handleRrcEstablishmentMessages(self, source, interface, channelInfo, message, args=None):
        if message["messageName"] == "rrcConnectionRequest":
            self.temporaryCrnti = args["temporaryCrnti"]
            self.uplinkGrant = args["uplinkGrant"]
            self.rrcTransactionIdentifier = args["rrcTransactionIdentifier"]        
            self.ueAddress = source
            self.procedureCompleteCallbackExecuted = False             
            self.ueCrnti = channelInfo["cRnti"]
            self.ueIdentityType = message["ueIdentity"]["type"]
            self.ueIdentityValue = message["ueIdentity"]["value"]
            self.rrcEstablishmentCause = message["establishmentCause"]
            self.__sendContentionResolutionIdentity__()
            time.sleep(0.2) # some delay before sending the next message
            self.__sendRrcConnectionSetup__()
        if ( (message["messageName"] == "rrcConnectionSetupComplete") and \
             (message["rrcTransactionIdentifier"] == self.rrcTransactionIdentifier) ):
            self.ueSelectedPlmnIdentity = message["selectedPlmnIdentity"]
            self.uededicatedInfoNas = message["dedicatedInfoNas"]
            if not self.procedureCompleteCallbackExecuted:
                self.ioService.cancelTimer("rrcConnectionSetupTimeout")
                self.__notifyProcedureCompletion__(self.Success)
                self.procedureCompleteCallbackExecuted = True
    
    def __sendContentionResolutionIdentity__(self):
        interface, channelInfo, message = contentionResolutionIdentity(self.ueCrnti, self.ueIdentityType,
                                                    self.ueIdentityValue, self.rrcEstablishmentCause)
        self.ioService.sendMessage(self.ueAddress, interface, channelInfo, message)
    
    def __sendRrcConnectionSetup__(self):
        interface, channelInfo, message = rrcConnectionSetup(self.ueCrnti, self.rrcTransactionIdentifier)
        self.attemptNo += 1
        self.ioService.sendMessage(self.ueAddress, interface, channelInfo, message)
        self.ioService.startTimer("rrcConnectionSetupTimeout", self.rrcConnectionSetupTimeout,
            self.__onRrcConnectionSetupTimeout__)    
    
    def __onRrcConnectionSetupTimeout__(self, _):
        if self.attemptNo < self.maxRrcConnectionSetupAttempts:
            self.__sendRrcConnectionSetup__()
        else:
            self.__notifyProcedureCompletion__(self.ErrorNoRRCConnectionCompleteMessage)
            
    def returnRrcTransactionIdentifier(self):
        return self.rrcTransactionIdentifier