import unittest
import time

from eps.utils.io import IoService, localhost
from eps.procedures.ue.rrc import RrcConnectionEstablishmentProcedure as UeRrcConnectionEstablishmentProcedure
from eps.nodes.enb.enb import Enb
from eps.utils.config import ConfigPath
from eps.nodes.mme.mme import Mme

class TestUe2EnbRrcEstablishment(unittest.TestCase):

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
        procedureParameters = {
            "maxPrachPreambleAttempts": 5,
            "prachPreambleRepeatDelay": 0.7,
            "macContentionResolutionTimeout": 0.5,
            "rrcConnectionSetupTimeoutT300": 2.0
        }
        args = lambda i: {
            "ueIdentityType": "randomValue",
            "ueIdentityValue": 3434,
            "rrcEstablishmentCause": "moSignaling",
            "selectedPlmnIdentity": 2801,
            "initialNasMessage": {
                "nasMessageType": "attachRequest"
            },
        }

        self.ueIoServices = [IoService(str(i), 9001 + i) for i in range(20)]
        [s.start() for s in self.ueIoServices]
        self.ueProcedures = [UeRrcConnectionEstablishmentProcedure(procedureParameters, (localhost(), 9000),
            s, self.__procedureCompleteCallback__, args(i)) for i, s in enumerate(self.ueIoServices)]
        self.numSuccess = 0

    def tearDown(self):
        [s.stop() for s in self.ueIoServices]
        [n.terminate() for n in (self.enb, self.mme)]
        
    def __procedureCompleteCallback__(self, result):
        self.numSuccess += 1

    def test_singleUeRrcEstablishmentSuccess(self):
        time.sleep(0.1) # Wait for S1 Setup
        self.ueProcedures[0].execute()
        time.sleep(3)
        self.assertEqual(self.numSuccess, 1)

    def test_multipleUeRrcEstablishmentSuccess(self):
        time.sleep(0.1) # Wait for S1 Setup
        [p.execute() for p in self.ueProcedures]
        time.sleep(3)
        self.assertEqual(self.numSuccess, 20)

if __name__ == "__main__":
    unittest.main()