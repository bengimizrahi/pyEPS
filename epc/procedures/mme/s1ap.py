from ...messages.s1ap import s1SetupResponse, s1SetupFailure

class S1SetupProcedureHandler(object):

    def __init__(self, procedureParameters, enbPool, ioService):
        self.procedureParameters = procedureParameters
        self.enbPoolInsideMme = enbPool
        self.ioService = ioService
    
    def execute(self):
        def verifySettings():
            requiredProcedureParameters, requiredProcedureFlags = (
                ("mmeName", "servedGummeis", "maxNumEnbsServed", "timeToWait", "flags"),
                ("rejectS1SetupRequestsFromRegisteredEnbs")
            )
            missingParameters, missingFlags = \
                map(lambda items, requiredItems:
                    filter(lambda ri: ri not in items, requiredItems), (
                        (self.procedureParameters, requiredProcedureParameters),
                        (self.procedureParameters["flags"], requiredProcedureFlags)
                    )
                )
            assert not missingParameters, "Missing parameters in mmeSettings: {}".format(missingParameters)
            assert not missingFlags, "Missing flags in mmeSettings['flags']: {}".format(missingFlags)
        verifySettings()
    
    def terminate(self):
        self.ioService.stop()
    
    def handleIncomingS1SetupMessage(self, source, interface, channelInfo, message):
        def sendReject(destination, cause, timeToWait):
            self.ioService.sendMessage(destination, *s1SetupFailure(cause, timeToWait, None))
        
        def sendAccept(destination):
            params = (
                self.procedureParameters["mmeName"],
                self.procedureParameters["servedGummeis"],
                self.procedureParameters["relativeMmeCapacity"],
                None
            )
            self.ioService.sendMessage(destination, *s1SetupResponse(*params))       
        if self.enbPoolInsideMme.congested():
            sendReject(source, "congestion", self.procedureParameters["timeToWait"])
            return
        globalEnbId = message["globalEnbId"]
        if globalEnbId in self.enbPoolInsideMme and \
            self.procedureParameters["flags"]["rejectS1SetupRequestsFromRegisteredEnbs"]:
                sendReject(source, "unspecified", None)
                return
        sendAccept(source)
            
        
            