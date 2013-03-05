import time
import random

from ...messages import randomAccessResponse, contentionResolutionIdentity, rrcConnectionSetup

class EnbMain(object):
    def __init__(self, ioService, procedureCompleteCallback):
        self.ioService = ioService
        self.ueContextInfo = {}
        self.procedureCompleteCallback = procedureCompleteCallback
        self.numRrcEstablishmentPorceduresActive = 0
        self.numRrcEstablishmentsHandled = 0
        self.rrcEstablishmentConclusions = []
        
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
            # should start a thread here and let it handle the RRC establishment 
            # the thread dies either when establishment has completed successfully or failed.
            print "ioService is alive: {}".format(self.ioService.alive)
            self.enbProcedure = EnbRrcConnectionEstablishmentProcedure(3, 0.5, self.ioService, 
                self.__enbRrcProcedureCompleteCallback__)
            self.enbProcedure.execute(source, interface, channelInfo, message, temporaryCrnti, uplinkGrant, rrcTransactionIdentifier)
 
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
        self.enbProcedure.terminate()
        if self.numRrcEstablishmentPorceduresActive == 0:
            self.procedureCompleteCallback(self.rrcEstablishmentConclusions)
    

class EnbRrcConnectionEstablishmentProcedure(object):
    
    Success, ErrorNoRRCConnectionCompleteMessage = range(2)
    
    def __init__(self, maxRrcConnectionSetupAttempts, rrcConnectionSetupTimeout, 
                 ioService, procedureCompleteCallback):
 
        self.maxRrcConnectionSetupAttempts = maxRrcConnectionSetupAttempts # not defined in standards
        self.rrcConnectionSetupTimeout = rrcConnectionSetupTimeout
        self.procedureCompleteCallback = procedureCompleteCallback
        self.ioService = ioService
        self.attemptNo = 0

    def execute(self, source, interface, channelInfo, message, temporaryCrnti, uplinkGrant, rrcTransactionIdentifier):
        self.temporaryCrnti = temporaryCrnti
        self.uplinkGrant = uplinkGrant
        self.rrcTransactionIdentifier = rrcTransactionIdentifier        
        self.ueAddress = source
        self.procedureCompleteCallbackExecuted = False
        self.ioService.addIncomingMessageCallback(self.__enbRrcIncomingMessageCallback__)
        self.__enbRrcIncomingMessageCallback__(source, interface, channelInfo, message)
              
    def terminate(self):
        self.ioService.removeIncomingMessageCallback(self.__incomingMessageCallback__)

    def __notifyProcedureCompletion__(self, result):
        if result == self.Success:
            self.procedureCompleteCallback(result, {"cRnti": self.ueCrnti, "identityType": self.ueIdentityType, 
                "indentityValue": self.ueIdentityValue, "establishmentCause": self.rrcEstablishmentCause, 
                "selectedPlmnIdentity": self.ueSelectedPlmnIdentity, "dedicatedInfoNas": self.uededicatedInfoNas})
        else:
            self.procedureCompleteCallback(result)
            
    def __enbRrcIncomingMessageCallback__(self, source, interface, channelInfo, message):
        if ( (message["messageName"] == "rrcConnectionRequest") and \
                  (channelInfo["cRnti"] == self.temporaryCrnti) ):
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