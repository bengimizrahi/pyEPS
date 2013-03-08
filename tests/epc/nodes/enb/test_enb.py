import unittest
import time

from epc.utils.io import IoService, localhost
from epc.messages.rrc import rrcConnectionRequest, rrcConnectionSetupComplete
from epc.procedures.enb.rrc import RrcConnectionEstablishmentProcedure as EnbRrcConnectionEstablishmentProcedure
from epc.nodes.enb import Enb


class TestEnb(unittest.TestCase):

    def setUp(self):
        self.enbIoService = IoService("enb", 9000)
        self.ueIoServices = [IoService(str(i), 9001 + i) for i in range(20)]
        self.enbIoService.start()
        [s.start() for s in self.ueIoServices]
        self.enb = Enb(self.enbIoService)

    def tearDown(self):
        [s.stop() for s in self.ueIoServices]
        self.enbIoService.stop()

    def test_noRrcConnectionSetupCompleteReceived(self):
        temporaryCrnti = 0
        self.enb.execute()
        self.ueIoServices[0].sendMessage((localhost(), 9000), *rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling"))
        time.sleep(2.5) # more than 3* 0.5 = 1.5 seconds  + 0.5 seconds
        self.assertEqual(self.enb.kpis["numRrcConnectionEstablishmentFailures"], 1)

    def test_singleUeRrcEstablishmentSuccess(self):
        temporaryCrnti = 0
        rrcTransactionIdentifier = 0
        self.enb.execute()
        self.ueIoServices[0].sendMessage((localhost(), 9000), *rrcConnectionRequest(
            temporaryCrnti, "randomValue", 3434, "moSignaling"))
        self.ueIoServices[0].sendMessage((localhost(), 9000), *rrcConnectionSetupComplete(
            rrcTransactionIdentifier, 28001, {"nasMessageType": "attachRequest"}))
        time.sleep(1.0) # ensure the enb call back is not waiting for rrc complete
        self.assertEqual(self.enb.kpis["numRrcConnectionEstablishmentSuccesses"], 1)
        print "UE context information in eNB"
        print self.enb.ueContext

    def test_twoUeRrcEstablishmentSuccess(self):
        self.enb.execute()
        [s.sendMessage((localhost(), 9000), *rrcConnectionRequest(
            i, "randomValue", 3434, "moSignaling")) for i, s in enumerate(self.ueIoServices)]
        for i in range(2):
            self.ueIoServices[0]
            time.sleep(0.5)
        time.sleep(0.2)
        for i in range(2):
            interface, channelInfo, message = rrcConnectionSetupComplete(i, 28001, 
                                                                     {"nasMessageType": "attachRequest"})
            self.ueIoServices[i].sendMessage((localhost(), 9000), interface, channelInfo, message)
            time.sleep(0.2)
        time.sleep(1.0) # ensure the enb call back is not waiting for rrc complete
        self.assertEqual(self.enb.rrcEstablishmentSuccess[0], EnbRrcConnectionEstablishmentProcedure.Success)
        self.assertEqual(self.enb.rrcEstablishmentSuccess[1], EnbRrcConnectionEstablishmentProcedure.Success)
        print "UE context information in eNB"
        print self.enbProcedure.ueContext


if __name__ == "__main__":
    unittest.main()