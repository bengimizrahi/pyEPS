from eps.messages.s6a import authenticationInformationRequest


class AuthenticationInformationRetrievalProcedureHandler(object):

    Success, Failure = range(2)

    def __init__(self, hssAddress, ioService, procedureCompletionCallback):
        self.hssAddress = hssAddress
        self.ioService = ioService
        self.procedureCompletionCallback = procedureCompletionCallback
        self.nextEndToEndId = 0
        self.outstandingRequests = {}

    def execute(self, imsi, visitedPlmnId):
        self.ioService.sendMessage(self.hssAddress, *authenticationInformationRequest(imsi, visitedPlmnId, self.nextEndToEndId))
        self.outstandingRequests[self.nextEndToEndId] = {"imsi": imsi, "visitedPlmnId": visitedPlmnId}
        self.nextEndToEndId += 1

    def handleIncomingMessage(self, source, interface, channelInfo, message):
        endToEndId = channelInfo["endToEndId"]
        if endToEndId in self.outstandingRequests:
            authContext = self.outstandingRequests[endToEndId]
            if message["resultCode"] == 2001:
                authContext["authenticationInfo"] = message["authenticationInfo"]
                self.procedureCompletionCallback(self.Success, authContext)
            else:
                self.procedureCompletionCallback(self.Failure)
            del self.outstandingRequests[endToEndId]