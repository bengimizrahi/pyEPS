import unittest
import time

from epc.utils.io import IoService, localhost
from epc.procedures.enb.rrc import RrcConnectionEstablishmentProcedure as EnbRrcConnectionEstablishmentProcedure
from epc.messages.rrc import rrcConnectionRequest, rrcConnectionSetupComplete


class TestEnbRrcConnectionProcedure(unittest.TestCase):

    def setUp(self):
        self.enbIoService = IoService("enb", 9000)
        self.ueIoService = IoService("ue", 9001)
        [s.start() for s in self.enbIoService, self.ueIoService]
        self.enbProcedure = EnbRrcConnectionEstablishmentProcedure(3, 0.5, self.enbIoService, 
            self.__procedureEnbCompleteCallback__)

    def tearDown(self):
        [s.stop() for s in self.enbIoService, self.ueIoService]

    def __procedureEnbCompleteCallback__(self, result, addr, a, b, args=None):
        self.enbResult = result

    def test_noRrcConnectionSetupCompleteReceived(self):
        self.enbResult = None
        temporaryCrnti = 0
        uplinkGrant = 34
        rrcTransactionIdentifier = 0
        interface, channelInfo, message = rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling")
        self.enbProcedure.handleRrcEstablishmentMessage((localhost(), 9001),  interface, channelInfo, message, {
            "temporaryCrnti": temporaryCrnti,
            "uplinkGrant": uplinkGrant, 
            "rrcTransactionIdentifier": rrcTransactionIdentifier
        })
        time.sleep(1.7) # more than 3 * 0.5 = 1.5 seconds
        self.assertEqual(self.enbResult,
            EnbRrcConnectionEstablishmentProcedure.ErrorNoRrcConnectionCompleteMessage)

    def test_rrcConnectionEstablishmentSuccess(self):
        self.enbResult = None
        temporaryCrnti = 0
        uplinkGrant = 34
        rrcTransactionIdentifier = 0
        interface, channelInfo, message = rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling")
        self.enbProcedure.handleRrcEstablishmentMessage((localhost(), 9001),  interface, channelInfo, message, {
            "temporaryCrnti": temporaryCrnti,
            "uplinkGrant": uplinkGrant, 
            "rrcTransactionIdentifier": rrcTransactionIdentifier
        })
        time.sleep(0.2)
        interface, channelInfo, message = rrcConnectionSetupComplete(rrcTransactionIdentifier, 28001, {"nasMessageType": "attachRequest"})
        self.enbProcedure.handleRrcEstablishmentMessage((localhost(),9001),  interface, channelInfo, message)
        self.assertEqual(self.enbResult,
            EnbRrcConnectionEstablishmentProcedure.Success)

    def test_rrcConnectionEstablishmentSuccessSubsequentRrcCompleteIgnored(self):
        self.enbResult = None
        temporaryCrnti = 0
        uplinkGrant = 34
        rrcTransactionIdentifier = 0
        interface, channelInfo, message = rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling")
        self.enbProcedure.handleRrcEstablishmentMessage((localhost(), 9001),  interface, channelInfo, message, {
            "temporaryCrnti": temporaryCrnti,
            "uplinkGrant": uplinkGrant, 
            "rrcTransactionIdentifier": rrcTransactionIdentifier
        })
        time.sleep(0.2)
        interface, channelInfo, message = rrcConnectionSetupComplete(rrcTransactionIdentifier, 28001, {"nasMessageType": "attachRequest"})
        self.enbProcedure.handleRrcEstablishmentMessage((localhost(), 9001),  interface, channelInfo, message)
        self.assertEqual(self.enbResult, EnbRrcConnectionEstablishmentProcedure.Success)
        time.sleep(0.2)
        self.enbResult = None
        self.enbProcedure.handleRrcEstablishmentMessage((localhost(), 9001),  interface, channelInfo, message)
        time.sleep(0.2)
        self.assertEqual(self.enbResult, None)


if __name__ == "__main__":
    unittest.main()