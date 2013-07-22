import unittest
import time

from ...utils.io import IoService, localhost
from ...messages.rrc import rrcConnectionRequest, rrcConnectionSetupComplete
from ...nodes.enb.enb import Enb

import logging
msgTraceLogger = logging.getLogger("msgTrace")
msgTraceLogger.addHandler(logging.StreamHandler())
#msgTraceLogger.setLevel(logging.DEBUG)

class TestEnbRrcConnectionEstablishment(unittest.TestCase):

    def setUp(self):
        self.enb = Enb("enb", 9000)
        self.handler = self.enb.rrcConnectionEstablishmentProcedureHandler
        self.enb.execute()
        self.numUes = 20
        self.ueIoServices = [IoService(str(i), 9001 + i) for i in range(self.numUes)]
        [s.start() for s in self.ueIoServices]

    def tearDown(self):
        self.enb.terminate()
        [s.stop() for s in self.ueIoServices]

    def test_noRrcConnectionSetupCompleteReceived(self):
        temporaryCrnti = 0
        self.ueIoServices[0].sendMessage((localhost(), 9000), *rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling"))
        time.sleep(2.5) # more than 3* 0.5 = 1.5 seconds  + 0.5 seconds
        self.assertEqual(self.handler.kpis["numRrcConnectionEstablishmentFailures"], 1)

    def test_singleUeRrcEstablishmentSuccess(self):
        temporaryCrnti = 0
        rrcTransactionIdentifier = 0
        self.ueIoServices[0].sendMessage((localhost(), 9000), *rrcConnectionRequest(
            temporaryCrnti, "randomValue", 3434, "moSignaling"))
        self.ueIoServices[0].sendMessage((localhost(), 9000), *rrcConnectionSetupComplete(
            rrcTransactionIdentifier, 28001, {"nasMessageType": "attachRequest"}))
        time.sleep(0.1) # ensure the enb call back is not waiting for rrc complete
        self.assertEqual(self.handler.kpis["numRrcConnectionEstablishmentSuccesses"], 1)

    def test_nUeRrcEstablishmentSuccess(self):
        [s.sendMessage((localhost(), 9000), *rrcConnectionRequest(
                temporaryCrnti, "randomValue", 3434, "moSignaling")
            ) for temporaryCrnti, s in enumerate(self.ueIoServices)]
        [s.sendMessage((localhost(), 9000), *rrcConnectionSetupComplete(
                rrcTransactionIdentifier, 28001, {"nasMessageType": "attachRequest"})
            ) for rrcTransactionIdentifier, s in enumerate(self.ueIoServices)]
        time.sleep(0.1)
        self.assertEqual(len(self.enb.ues), self.numUes)


if __name__ == "__main__":
    unittest.main()
