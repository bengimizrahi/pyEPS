def createSessionRequest(interface, procedure, gtpcHeaderTeid, sequenceNumber, message): 
    if (interface == "s11" and procedure == "eutranInitialAttach"):
        requiredIEs = ("imsi", "senderFteidForControlPlane", "pgwS5S8AddressForContolPlane", 
                       "pdnAddressAllocation", "bearerContextsToBeCreated")
        missingIEs = set(requiredIEs) - set(message)
        if missingIEs:
            raise Exception("For Create Session Request on interface {} and procedure {} the following are the missing IEs:{}".format(interface, procedure, missingIEs))
    return (
        interface,
        {
         "messageType": "createSessionRequest",
         "headerTeid": gtpcHeaderTeid,
         "sequenceNumber": sequenceNumber
        },
        message
)

def bearerContextToBeCreatedIE(interface, procedure, messageParameters):
    if (interface == "s11" and procedure == "eutranInitialAttach"):
        requiredIEs = ("epsBearerId", "bearerLevelQoS")
        missingIEs = requiredIEs - set(messageParameters)
        if missingIEs:
            raise Exception("For Bearer Context to be created on interface {} and procedure {} the following are the missing IEs:{}".format(interface, procedure, missingIEs))
    return messageParameters
    
def createSessionResponse(interface, procedure, gtpcHeaderTeid, sequenceNumber, message): 
    if (interface == "s11" and procedure == "eutranInitialAttach"):
        requiredIEs = ("cause", "imsi", "senderFteidForControlPlane", "pgwS5S8FteidForContolPlane", 
                       "pdnAddressAllocation", "bearerContextsCreated")
        missingIEs = set(requiredIEs) - set(message)
        if missingIEs:
            raise Exception("For Create Session Request on interface {} and procedure {} the following are the missing IEs:{}".format(interface, procedure, missingIEs))
    return (
        interface,
        {
         "messageType": "createSessionResponse",
         "headerTeid": gtpcHeaderTeid,
         "sequenceNumber": sequenceNumber,
        },
        message
)    

bearerContextCreatedIE = \
    lambda epsBearerId, cause, s1uSgwFteid, s5s8uPgwFteid: (
        {
         "epsBearerId": epsBearerId,
         "s1uSgwFteid": s1uSgwFteid,
         "s5s8uPgwFteid": s5s8uPgwFteid,
         }
)