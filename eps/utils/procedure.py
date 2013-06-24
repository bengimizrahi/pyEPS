class TwoWayProcedureA(object):

    Success, Failure = range(2)

    def __init__(self, request, responses, completionCallback, isTransportReliable=True):
        self.request = request
        self.responses = responses
        self.completionCallback = completionCallback
        self.isTransportReliable = isTransportReliable
        self.completionCallbackParameters = None

    def handleSuccessfulResponseMessage(self, *args):
        raise Exception("Not implemented")

    def handleFailureResponseMessage(self, *args):
        raise Exception("Not Implemented")

    def setCompletionCallbackParameters(self, *args, **kwargs):
        self.completionCallbackParameters = args, kwargs

    def handleIncomingMessage(self, source, interface, channelInfo, message):
        def handleUnknownMessage(*args):
            return False
        mapping = dict(zip(self.responses, (self.handleSuccessfulResponseMessage, self.handleFailureResponseMessage)))
        messageType = message["messageType"]
        retVal = mapping.get(messageType, handleUnknownMessage)(source, interface, channelInfo, message)
        self.completionCallback(self.completionCallbackParameters)
        