import unittest
import time

from epc.utils.io import IoService, localhost
from epc.procedures.ue.rrc import RrcConnectionEstablishmentProcedure as UeRrcConnectionEstablishmentProcedure
from epc.procedures.mme.s1ap import S1SetupProcedureHandler as MmeS1SetupProcedureHandler
from epc.nodes.enb.enb import Enb

class TestUe2EnbRrcEstablishment(unittest.TestCase):

    def setUp(self):
        self.mmeIoService = IoService("mme", 8999)
        self.mmeIoService.start()
        self.enb = Enb("enb", 9000, {
            "control": {
                "adminState": True,
            },
            "rrc": {
                "maxRrcConnectionSetupAttempts": 5,
                "rrcConnectionSetupTimeout": 0.7,
            },
            "mme": {
                "address": (localhost(), 8999),
                "s1SetupParameters": {
                    "mmeName": "Istanbul",
                    "servedGummeis": [
                        (("28603", "28604"), (0, 1, 2), (23, 58, 127)),
                        (("00108"), (0,), (12, 13, 14)),
                    ],
                    "timeToWait": 1,
                    "flags": {
                        "rejectS1SetupRequestsFromRegisteredEnbs": True
                    },
                    "criticalityDiagnostics": None,
                },
                "properties": None,
            }
        })
        procedureParameters = {
            "initialNasMessage": {
             "nasMessageType": "attachRequest"
            },
            "maxPrachPreambleAttempts": 5,
            "prachPreambleRepeatDelay": 0.7,
            "macContentionResolutionTimeout": 0.5,
            "rrcConnectionSetupTimeoutT300": 2.0
        }
        args = lambda i: {
            "ueIdentityType": "randomValue",
            "ueIdentityValue": 3434 + i,
            "rrcEstablishmentCause": "moSignaling",
            "selectedPlmnIdentity": 2801
        }
        self.enb.execute()
        mmeParameter = {
            "mmeName": "Istanbul",
            "servedGummeis": [
                (("28603", "28604"), (0, 1, 2), (23, 58, 127)),
                (("00108"), (0,), (12, 13, 14)),
            ],
            "timeToWait": 1,
            "flags": {
                "rejectS1SetupRequestsFromRegisteredEnbs": True
            },
            "criticalityDiagnostics": None,
        }
        self.ueIoServices = [IoService(str(i), 9001 + i) for i in range(20)]
        [s.start() for s in self.ueIoServices]
        self.ueProcedures = [UeRrcConnectionEstablishmentProcedure(procedureParameters, (localhost(), 9000),
            s, self.__procedureCompleteCallback__, args(i)) for i, s in enumerate(self.ueIoServices)]
        self.numSuccess = 0

    def tearDown(self):
        [s.stop() for s in self.ueIoServices]
        self.enbIoService.stop()

    def __procedureCompleteCallback__(self, result):
        self.numSuccess += 1

    def test_singleUeRrcEstablishmentSuccess(self):
        self.enbProcedure.execute()
        self.ueProcedures[0].execute()
        time.sleep(3)
        self.assertEqual(self.numSuccess, 1)
        print "UE context information in eNB"
        print self.enbProcedure.ueContext       

    def test_twoUeRrcEstablishmentSuccess(self):
        self.enbProcedure.execute()
        [p.execute() for p in self.ueProcedures]
        time.sleep(3)
        self.assertEqual(self.numSuccess, 2)
        print "UE context information in eNB"
        print self.enbProcedure.ueContext       


if __name__ == "__main__":
    unittest.main()