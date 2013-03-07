import unittest
import time

from epc.utils.io import IoService, localhost
from epc.procedures.ue.rrc import RrcConnectionEstablishmentProcedure as UeRrcConnectionEstablishmentProcedure
from epc.nodes.enb import Enb

class TestUe2EnbRrcEstablishment(unittest.TestCase):

    def setUp(self):
        self.enbIoService = IoService("enb", 9000)
        self.ueIoServices = [IoService(str(i), 9001 + i) for i in range(20)]
        self.enbIoService.start()
        [s.start() for s in self.ueIoServices]
        self.enbProcedure = Enb(self.enbIoService)
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
            "ueIdentityValue": 3434 * i,
            "rrcEstablishmentCause": "moSignaling",
            "selectedPlmnIdentity": 2801
        }
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