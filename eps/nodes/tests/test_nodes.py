import unittest
import time

from eps.utils.io import IoService, localhost
from eps.utils.config import ConfigPath
from eps.nodes.mme.mme import Mme
from eps.nodes.enb.enb import Enb
from eps.procedures.ue.rrc import RrcConnectionEstablishmentProcedure

import logging
for l in ("msgTrace", "assertions"):
    logger = logging.getLogger(l)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    logger.addHandler(handler)


class TestS1Interface(unittest.TestCase):

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

    def tearDown(self):
        [n.terminate() for n in (self.enb, self.mme)]

    def test_s1SetupSuccessful(self):
        time.sleep(0.1)
        self.assertEqual(self.enb.config.getValue("mme.properties.name"), "Istanbul")

    def test_rrcConnectionSetupProcedureSuccessful(self):
        time.sleep(0.1) # Wait for S1 Setup
        def rrcComplete(result):
            self.result = result
        self.result = None
        ueIoService = IoService("ue", 9001)
        ueIoService.start()
        rrcProcedure = RrcConnectionEstablishmentProcedure({
            "maxPrachPreambleAttempts": 5,
            "prachPreambleRepeatDelay": 0.7,
            "macContentionResolutionTimeout": 0.5,
            "rrcConnectionSetupTimeoutT300": 2.0
        }, (localhost(), 9000), ueIoService, rrcComplete, {
            "ueIdentityType": "randomValue",
            "ueIdentityValue": 3434,
            "rrcEstablishmentCause": "moSignaling",
            "selectedPlmnIdentity": 2801,
            "initialNasMessage": {
                "nasMessageType": "attachRequest"
            },
        })
        rrcProcedure.execute()
        time.sleep(2)
        self.assertEqual(self.result, RrcConnectionEstablishmentProcedure.Success)
        ueIoService.stop()


if __name__ == "__main__":
    unittest.main()
