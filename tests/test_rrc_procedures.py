import unittest
import time

from epc.utils.io import IoService, localhost
from epc.procedures.ue.rrc import RrcConnectionEstablishmentProcedure as UeRrcConnectionEstablishmentProcedure
from epc.procedures.enb.rrc import RrcConnectionEstablishmentProcedure as EnbRrcConnectionEstablishmentProcedure
from epc.nodes.enb import Enb

class TestUe2EnbRrcEstablishment(unittest.TestCase):

    def setUp(self):
        self.enbIoService = IoService("enb", 9000)
        self.ueIoServices = [IoService(str(i), 9001 + i) for i in range(2)]
        self.enbIoService.start()
        [s.start() for s in self.ueIoServices]
        self.enbProcedure = Enb(self.enbIoService)
        self.ueProcedures = [UeRrcConnectionEstablishmentProcedure(
            {"nasMessageType": "attachRequest"},
            5, 0.7, 0.5, 2.0, (localhost(), 9000),
            s, self.__procedureCompleteCallback__, {
                "ueIdentityType": "randomValue",
                "ueIdentityValue": 3434 * i,
                "rrcEstablishmentCause": "moSignaling",
                "selectedPlmnIdentity": 2801
            }) for s in self.ueIoServices]

    def tearDown(self):
        [s.stop() for s in self.ueIoServices]
        self.enbIoService.stop()

    def __procedureCompleteCallback__(self, result):
        self.ueResult = result

    def test_singleUeRrcEstablishmentSuccess(self):
        self.ueResult = None
        self.enbProcedure.execute()
        self.ueProcedures[0].execute()
        time.sleep(3)
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[0], EnbRrcConnectionEstablishmentProcedure.Success)        
        self.assertEqual(self.ueResult, UeRrcConnectionEstablishmentProcedure.Success)
        print "UE context information in eNB"
        print self.enbProcedure.ueContext       

    def test_twoUeRrcEstablishmentSuccess(self):
        self.ueResult = None
        self.enbProcedure.execute()
        self.ueProcedures[0].execute()
        time.sleep(0.6)  # MOTE: This test fails dues to timer error if sleep is less than this value
        # Exception: No running timer named 'randomAccessResponseTimeout' found
        self.ueProcedures[1].execute()
        time.sleep(3)
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[0], EnbRrcConnectionEstablishmentProcedure.Success)        
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[1], EnbRrcConnectionEstablishmentProcedure.Success)        
        self.assertEqual(self.ueResult, UeRrcConnectionEstablishmentProcedure.Success)
        print "UE context information in eNB"
        print self.enbProcedure.ueContext       


if __name__ == "__main__":
    unittest.main()