from eps.messages.s6a import authenticationInformationAnswer


class AuthenticationInformationRetrievalProcedureHandler(object):

    Success, Failure = range(2)

    def __init__(self, ioService, procedureCompletionCallback):
        self.ioService = ioService
        self.procedureCompletionCallback = procedureCompletionCallback
        self.nextEndToEndId = 0
        self.outstandingRequests = {}

    def handleIncomingMessage(self, source, interface, channelInfo, message):
        endToEndId = channelInfo["endToEndId"]
        self.ioService.sendMessage(source, *authenticationInformationAnswer(2001, [], endToEndId))
        self.procedureCompletionCallback(self.Success, message["imsi"])
