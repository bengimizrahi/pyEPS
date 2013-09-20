from eps.messages.gtpc import createSessionResponse

class S11CreateSessionRequestProcedureHandler(object):

    Success, ErrorDuplicateCreateSessionRequest, ErrorDuplicateCreateSessionRequestwMismatchSequenceNumber, ErrorBearerResourcesNotAllocated = range(4)

# to dos:
#       1. handling of duplicate create session request to TEID 0 in header. From 29.274:
#          If the new Create Session Request message is received with TEID 0 in the header 
#          for an existing active PDN connection context, this Create Session Request message 
#          shall be treated as a request for a new session. 
#          The existing PDN connection context should be deleted locally, before a new session is created.

    def __init__(self, mmeAddressPort, sgwAddress, ioService, bearerResourceHandler, procedureCompletionCallback):
        self.mmeAddressPort = mmeAddressPort
        self.sgwAddress = sgwAddress
        self.ioService = ioService
        self.bearerResourceHandler = bearerResourceHandler
        self.procedureCompletionCallback = procedureCompletionCallback
        self.nextSgwFteidForControlPlane = 0
        self.nextPgwFteidForControlPlane = 0
        self.establishedS11SessionContexts = {}

    def handleCreateSessionRequestMessage(self, source, interface, channelInfo, message):     
        self.result = None
        self.inputMessage = message
        self.imsi = message["imsi"]
        self.mmeFteidForControlPlane = message["senderFteidForControlPlane"]
        self.pgwAddress = message["pgwS5S8AddressForContolPlane"]["address"]
        self.gtpcHeaderSequenceNumber = channelInfo["sequenceNumber"]
        if self.imsi in self.establishedS11SessionContexts:
            if self.establishedS11SessionContexts[self.imsi]["gtpcHeaderSequenceNumber"] == channelInfo["sequenceNumber"] and \
                                    channelInfo["headerTeid"] == 0 :
                self.__sendCreateSessionResponseMessage__("requestAccepted")                 # this is a duplicate request, send previous response
                self.result = self.ErrorDuplicateCreateSessionRequest
                self.__notifyProcedureCompletion__()
                return
            elif self.establishedS11SessionContexts[self.imsi]["gtpcHeaderSequenceNumber"] != channelInfo["sequenceNumber"] and \
                                    channelInfo["headerTeid"] == 0 :
                # Handling of duplicate create session request to TEID 0 in header. From 29.274:
                #          If the new Create Session Request message is received with TEID 0 in the header 
                #          for an existing active PDN connection context, this Create Session Request message 
                #          shall be treated as a request for a new session. 
                #          The existing PDN connection context should be deleted locally, before a new session is created.
                del self.establishedS11SessionContexts[self.imsi]
                self.bearerResourceHandler.deleteBearerResources(self.imsi)
            else:
                raise Exception("Duplicate Create Session Request sent to tunnel id not equal to 0")
        self.__allocatePdnConnectionIpAddress__(self.imsi, message["pdnAddressAllocation"])
        self.bearerResourceHandler.allocateBearerResources(self.imsi, message["bearerContextsToBeCreated"], self.__handleBearerResourcesAllocated__)

    def __allocatePdnConnectionIpAddress__(self, imsi, pdnAddressAllocation):
        dhcpAllocatedAddress = "0.0.0.0" # DHCP should be used, hence returned address is 0.0.0.0
        self.pdnAddressAllocation = {"pdnType": "ipv4", "pdnAddressAndPrefix": dhcpAllocatedAddress}
   
    def __handleBearerResourcesAllocated__(self, result, bearerContexts=None):
        if result == self.bearerResourceHandler.Success:
            imsi = self.imsi
            self.establishedS11SessionContexts[imsi] = \
                {"imsi": imsi,
                 "mmeFteidForControlPlane": self.mmeFteidForControlPlane,
                 "sgwFteidForControlPlane": {"interfaceType": "ipv4", "teid": self.nextSgwFteidForControlPlane, "address": self.sgwAddress},
                 "pgwS5S8FteidForContolPlane": {"interfaceType": "ipv4", "teid": self.nextPgwFteidForControlPlane, "address": self.pgwAddress},
                 "bearerContexts": bearerContexts,
                 "pdnAddressAllocation": self.pdnAddressAllocation,
                 "gtpcHeaderSequenceNumber": self.gtpcHeaderSequenceNumber
                }
            self.nextSgwFteidForControlPlane += 1
            self.nextPgwFteidForControlPlane += 1
            self.__sendCreateSessionResponseMessage__("requestAccepted")
            self.result = self.Success
        else:
            self.__sendCreateSessionResponseMessage__("requestRejected")           
            self.result = self.ErrorBearerResourcesNotAllocated
            del  self.establishedS11SessionContexts[imsi]
        self.__notifyProcedureCompletion__()
 
    def __sendCreateSessionResponseMessage__(self, cause):
        imsi = self.imsi
        if cause != "requestAccepted":
            message = {"cause": cause,
                       "imsi": imsi
                       }
        else:
            message = \
                {"cause": cause,
                 "imsi": imsi, 
                 "senderFteidForControlPlane": self.establishedS11SessionContexts[imsi]["sgwFteidForControlPlane"], 
                 "pgwS5S8FteidForContolPlane": self.establishedS11SessionContexts[imsi]["pgwS5S8FteidForContolPlane"], 
                 "pdnAddressAllocation": self.establishedS11SessionContexts[imsi]["pdnAddressAllocation"],
                 "bearerContextsCreated": self.establishedS11SessionContexts[imsi]["bearerContexts"]
                 }
        self.ioService.sendMessage(self.mmeAddressPort, *createSessionResponse(
                "s11", "eutranInitialAttach", self.establishedS11SessionContexts[imsi]["mmeFteidForControlPlane"]["teid"], 
                self.gtpcHeaderSequenceNumber,
                message))

    def __notifyProcedureCompletion__(self):
        if self.result == self.Success:
            self.procedureCompletionCallback(self.result, self.establishedS11SessionContexts[self.imsi])
        else:
            self.procedureCompletionCallback(self.result)


class BearerResourceHandler(object):
        
    Success, ErrorDuplicateBearerIdsInRequest, ErrorPreExistingBearerContext = range(3)

    def __init__(self, sgwAddress, pgwAddress):
        self.sgwAddress = sgwAddress
        self.pgwAddress = pgwAddress
        self.nextS1uSgwFteid = 0
        self.nextS5S8uPgwFteid = 0
        self.bearerContexts = {}
                
    def allocateBearerResources(self, imsi, bearerContextsToBeSetup, procedureCompletionCallback):
        self.procedureCompletionCallback = procedureCompletionCallback
        result = False
        #ia: should create another test to see if there are no duplicate bearer ids in
        #    the contexts to be setup
        #    [delet comment when such a test is added]
        existingBearerIds = []
        if imsi in self.bearerContexts:
            for bearer in self.bearerContexts[imsi]:
                existingBearerIds.append(bearer["epsBearerId"])
        requestedBearerIds = []
        for bearer in bearerContextsToBeSetup:
            requestedBearerIds.append(bearer["epsBearerId"])
        overlapBearerIds = set.intersection(set(existingBearerIds), set(requestedBearerIds))
        if overlapBearerIds:
            result = self.ErrorPreExistingBearerContext
            self.__notifyProcedureCompletion__(result)
            return
        if imsi not in self.bearerContexts:
            self.bearerContexts[imsi] = []
        self.bearerContextsCreated = []
        for bearer in bearerContextsToBeSetup:
            self.bearerContextsCreated.append({"epsBearerId": bearer["epsBearerId"], 
                                          "s1uSgwFteid": {"interfaceType": "ipv4", "teid": self.nextS1uSgwFteid, "address": self.sgwAddress},
                                          "s5S8uPgwFteid": {"interfaceType": "ipv4", "teid": self.nextS5S8uPgwFteid, "address": self.pgwAddress}
                                          }) 
            self.bearerContexts[imsi].append({"epsBearerId": bearer["epsBearerId"], 
                                              "s1uSgwFteid": {"interfaceType": "ipv4", "teid": self.nextS1uSgwFteid, "address": self.sgwAddress},
                                              "s5S8uPgwFteid": {"interfaceType": "ipv4", "teid": self.nextS5S8uPgwFteid, "address": self.pgwAddress},
                                              "bearerLevelQos": bearer["bearerLevelQos"]
                                             })
            self.nextS1uSgwFteid += 1
            self.nextS5S8uPgwFteid += 1
        result = self.Success
        self.__notifyProcedureCompletion__(result)

    def deleteBearerResources(self, imsi):
        if imsi not in self.bearerContexts:
            raise Exception("Request to delete bearer resource when no bearer resource exist for imsi: {}".format(imsi))
        del self.bearerContexts[imsi]

    def __notifyProcedureCompletion__(self,result):        
        if result == self.Success:
            self.procedureCompletionCallback(result, self.bearerContextsCreated)
        else:
            self.procedureCompletionCallback(result)
        return   
        