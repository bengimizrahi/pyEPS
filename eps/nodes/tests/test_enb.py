import unittest
import time

from eps.utils.io import IoService, localhost
from eps.utils.config import ConfigPath
from eps.messages.rrc import rrcConnectionRequest, rrcConnectionSetupComplete
from eps.nodes.enb.enb import Enb
from eps.nodes.mme.mme import Mme

import logging
msgTraceLogger = logging.getLogger("msgTrace")
msgTraceLogger.addHandler(logging.StreamHandler())
#msgTraceLogger.setLevel(logging.DEBUG)

class TestEnbRrcConnectionEstablishment(unittest.TestCase):

    def setUp(self):
        self.mme = Mme("mme", 8999, {
            "system": {
                "mmeName": "Istanbul",
                "servedGummeis": [
                    (("28603", "28604"), (0, 1, 2), (23, 58, 127)),
                    (("00108"), (0,), (12, 13, 14)),
                ],
                "maximumEnbsAllowed": 2,
            },
            "s1": {
                "s1SetupTimeToWait": 1,
            },
        })
        self.mme.execute()
        self.enb = Enb("enb", 9000, {
            "control": {
                "adminState": True,
            },
            "system": {
                "globalEnbId": 345,
                "enbName": "Taksim",
                "supportedTas": [
                    (127, ("28603", "28604")),
                ],
                "csgIdList": [],
                "defaultPagingDrx": [32, 64, 128],
            },
            "rrc": {
                "maxRrcConnectionSetupAttempts": 5,
                "rrcConnectionSetupTimeout": 0.7,
            },
            "mme": {
                "address": (localhost(), 8999),
                "s1SetupParameters": ConfigPath("system"),
                "properties": None,
            },
        })
        self.enb.execute()
        self.numUes = 5
        self.ueIoServices = [IoService(str(i), 9001 + i) for i in range(self.numUes)]
        [s.start() for s in self.ueIoServices]

    def tearDown(self):
        [n.terminate() for n in (self.enb, self.mme)]
        [s.stop() for s in self.ueIoServices]

    def test_noRrcConnectionSetupCompleteReceived(self):
        time.sleep(0.1)
        temporaryCrnti = 0
        self.ueIoServices[0].sendMessage((localhost(), 9000), *rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling"))
        time.sleep(2.5) # more than 3* 0.5 = 1.5 seconds  + 0.5 seconds
        #self.assertEqual(self.handler.kpis["numRrcConnectionEstablishmentFailures"], 1)

    def test_singleUeRrcEstablishmentSuccess(self):
        time.sleep(0.1)
        temporaryCrnti = 0
        rrcTransactionIdentifier = 0
        self.ueIoServices[0].sendMessage((localhost(), 9000), *rrcConnectionRequest(
            temporaryCrnti, "randomValue", 3434, "moSignaling"))
        self.ueIoServices[0].sendMessage((localhost(), 9000), *rrcConnectionSetupComplete(
            rrcTransactionIdentifier, 28001, {"nasMessageType": "attachRequest"}))
        time.sleep(0.1) # ensure the enb call back is not waiting for rrc complete
        self.assertEqual(self.enb.state.uePool.numUes(), 1)

    def test_nUeRrcEstablishmentSuccess(self):
        time.sleep(0.1)
        for temporaryCrnti, s in enumerate(self.ueIoServices):
            s.sendMessage((localhost(), 9000), *rrcConnectionRequest(
                temporaryCrnti, "randomValue", 3434, "moSignaling") )
            time.sleep(0.1)  # need this to solve issue of synch
        for rrcTransactionIdentifier, s in enumerate(self.ueIoServices):
            s.sendMessage((localhost(), 9000), *rrcConnectionSetupComplete(
                rrcTransactionIdentifier, 28001, {"nasMessageType": "attachRequest"}))
            time.sleep(0.1)
        time.sleep(0.1) # need this to solve issue of synch
        self.assertEqual(self.enb.state.uePool.numUes(), self.numUes)


if __name__ == "__main__":
    unittest.main()
