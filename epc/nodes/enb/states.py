import logging

from ...utils.statemachine import State
from ...utils.helpers import idGenerator
from ...messages.rrc import RRC_CONNECTION_SETUP_ESTABLISHMENT_PROCEDURE_MESSAGES, rrcDlInformationTransfer
from ...messages.s1ap import initialUeMessage, uplinkNasTransport
from ...procedures.enb.s1ap import S1SetupProcedure
from ...procedures.enb.rrc import RrcConnectionEstablishmentProcedureHandler

assertionLogger = logging.getLogger("assertions")


class EnbState(State):

    def __init__(self, context):
        super(EnbState, self).__init__()
        self.ioService = context["ioService"]
        self.config = context["config"]


class Deregistered(EnbState):

    def __init__(self, context):
        super(Deregistered, self).__init__(context)

    def register(self):
        self.changeState(Registering)


class Registering(EnbState):

    def __init__(self, context):
        super(Registering, self).__init__(context)

    def __enter__(self):
        s1SetupRequestParameters = self.config.getValue("mme.s1SetupParameters")
        mmeAddress = self.config.getValue("mme.address")
        self.procedure = S1SetupProcedure(s1SetupRequestParameters,
            mmeAddress, self.ioService, self.__onS1SetupProgress__)
        self.procedure.execute()

    def handleIncomingMessage(self, *args):
        self.procedure.handleIncomingMessage(*args)
        return True

    def __onS1SetupProgress__(self, progress, mmeProperties=None):
        if progress == S1SetupProcedure.ProgressSuccess:
            self.config.setValue("mme.properties", mmeProperties)
            self.changeState(Registered)


class Registered(EnbState):

    def __init__(self, context):
        super(Registered, self).__init__(context)

    def __enter__(self):
        rrcParameters = self.config.getValue("rrc")
        maxRrcConnectionSetupAttempts, rrcConnectionSetupTimeout = \
            [rrcParameters[k] for k in "maxRrcConnectionSetupAttempts", "rrcConnectionSetupTimeout"]
        self.rrcConnectionEstablishmentProcedureHandler =  \
            RrcConnectionEstablishmentProcedureHandler(
            maxRrcConnectionSetupAttempts, rrcConnectionSetupTimeout,
            self.ioService, self.__onNewRrcConnectionEstablishment__)
        self.mmeAddress = self.config.getValue("mme.address")
        self.enbUeS1apIdGenerator = idGenerator(2**24)
        self.uePool = self.UePool()

    def handleIncomingMessage(self, source, interface, channelInfo, message):
        def handleRrcConnectionSetupEstablishmentProcedureMessages():
            self.rrcConnectionEstablishmentProcedureHandler.handleIncomingMessage(
                source, interface, channelInfo, message)

        def handleUlInformationTransferMessage():
            nasPdu = message["dedicatedInfoNas"]
            ue = self.uePool.ueByCrnti(channelInfo["cRnti"])
            self.ioService.sendMessage(self.mmeAddress, *uplinkNasTransport(
                ue.enbUeS1apId, ue.mmeUeS1apId, nasPdu, None))

        def handleDownlinkNasTransportMessage():
            dedicatedInfoNas = message["nasPdu"]
            ue = self.uePool.ueByEnbUeS1apId(message["enbUeS1apId"])
            self.ioService.sendMessage(ue.address, *rrcDlInformationTransfer(
                dedicatedInfoNas))
        mapping = (
            ("uu", RRC_CONNECTION_SETUP_ESTABLISHMENT_PROCEDURE_MESSAGES, handleRrcConnectionSetupEstablishmentProcedureMessages),
            ("uu", ("rrcUlInformationTransfer",), handleUlInformationTransferMessage),
            ("s1", ("downlinkNasTransport",), handleDownlinkNasTransportMessage),
        )
        for i, m, f in mapping:
            if interface == i and message["messageType"] in m:
                f()
                return True

    def __onNewRrcConnectionEstablishment__(self, address, cRnti, args):
        enbUeS1apId = self.enbUeS1apIdGenerator.next()
        rrcEstablishmentCause = args["rrcEstablishmentCause"]
        ue = self.Ue(address, cRnti, enbUeS1apId, rrcEstablishmentCause)
        self.uePool.addUe(ue)
        nasPdu = args["dedicatedNasInfo"]
        gummei = self.config.getValue["mme.servedGummeis"][0]
        self.ioService.sendMessage(self.mmeAddress, *initialUeMessage(
            enbUeS1apId, nasPdu, None, None, rrcEstablishmentCause, None, None, gummei, None))


    class UePool(object):

        def __init__(self):
            self.uesByCrnti = {}
            self.uesByEnbUeS1apId = {}

        def ueByCrnti(self, cRnti):
            return self.uesByCrnti[cRnti]

        def ueByEnbUeS1apId(self, enbUeS1apId):
            return self.uesByEnbUeS1apId[enbUeS1apId]

        def addUe(self, ue):
            self.uesByCrnti[ue.cRnti] = ue
            self.uesByEnbUeS1apId[ue.enbUeS1apId] = ue

        def removeUe(self, ue):
            del self.uesByCrnti[ue.cRnti]
            del self.uesByEnbUeS1apId[ue.enbUeS1apId]

        def removeUeByCrnti(self, cRnti):
            self.removeUe(self.ueByCrnti[cRnti])

        def removeUeByEnbUeS1apId(self, enbUeS1apId):
            self.removeUe(self.ueByEnbUeS1apId[enbUeS1apId])


    class Ue(object):

        def __init__(self, address, cRnti, enbUeS1apId, rrcEstablishmentCause):
            self.address = address
            self.cRnti = cRnti
            self.enbUeS1apId = enbUeS1apId
            self.mmeUeS1apId = None
            self.rrcEstablishmentCause = rrcEstablishmentCause
