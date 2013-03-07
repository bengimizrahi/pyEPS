import unittest
import time

from epc.utils.io import IoService, localhost
from epc.messages.rrc import rrcConnectionRequest, rrcConnectionSetupComplete
from epc.procedures.enb.rrc import RrcConnectionEstablishmentProcedure as EnbRrcConnectionEstablishmentProcedure
from epc.procedures.ue.rrc import RrcConnectionEstablishmentProcedure as UeRrcConnectionEstablishmentProcedure
from epc.nodes.enb import Enb

class TestEnb(unittest.TestCase):

    def setUp(self):
        self.enbIoService = IoService("enb", 9000)
        self.ueIoServices = [IoService(str(i), 9001 + i) for i in range(2)]
        self.enbIoService.start()
        [s.start() for s in self.ueIoServices]
        self.enbProcedure = Enb(self.enbIoService)

    def tearDown(self):
        [s.stop() for s in self.ueIoServices]
        self.enbIoService.stop()

    def test_noRRCConnectionSetupCompleteReceived(self):
        temporaryCrnti = 0
        self.enbProcedure.execute()
        interface, channelInfo, message = rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling")
        self.ueIoServices[0].sendMessage((localhost(), 9000), interface, channelInfo, message)
        time.sleep(2.5) # more than 3* 0.5 = 1.5 seconds  + 0.5 seconds
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[temporaryCrnti], EnbRrcConnectionEstablishmentProcedure.ErrorNoRRCConnectionCompleteMessage)        

    def test_singleUeRrcEstablishmentSuccess(self):
        temporaryCrnti = 0
        rrcTransactionIdentifier = 0
        self.enbProcedure.execute()
        interface, channelInfo, message = rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling")
        self.ueIoServices[0].sendMessage((localhost(), 9000), interface, channelInfo, message)
        interface, channelInfo, message = rrcConnectionSetupComplete(rrcTransactionIdentifier, 28001, 
                                                                     {"nasMessageType": "attachRequest"})
        self.ueIoServices[0].sendMessage((localhost(), 9000), interface, channelInfo, message)
        time.sleep(1.0) # ensure the enb call back is not waiting for rrc complete
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[temporaryCrnti], EnbRrcConnectionEstablishmentProcedure.Success)        
        print "UE context information in eNB"
        print self.enbProcedure.ueContext       

    def test_twoUeRrcEstablishmentSuccess(self):
        self.ueResult = None
        self.enbResult = None
        self.enbProcedure.execute()
        for i in range(2):
            interface, channelInfo, message = rrcConnectionRequest(i, "randomValue", 3434, "moSignaling")
            self.ueIoServices[0].sendMessage((localhost(), 9000), interface, channelInfo, message)
            time.sleep(0.5)
        time.sleep(0.2)
        for i in range(2):
            interface, channelInfo, message = rrcConnectionSetupComplete(i, 28001, 
                                                                     {"nasMessageType": "attachRequest"})
            self.ueIoServices[i].sendMessage((localhost(), 9000), interface, channelInfo, message)
            time.sleep(0.2)
        time.sleep(1.0) # ensure the enb call back is not waiting for rrc complete
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[0], EnbRrcConnectionEstablishmentProcedure.Success)        
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[1], EnbRrcConnectionEstablishmentProcedure.Success)        
        print "UE context information in eNB"
        print self.enbProcedure.ueContext

class TestUe2EnbRrrcEstablishment(unittest.TestCase):

    def setUp(self):
        self.enbIoService = IoService("enb", 9000)
        self.ueIoServices = [IoService(str(i), 9001 + i) for i in range(2)]
        self.enbIoService.start()
        [s.start() for s in self.ueIoServices]
        self.enbProcedure = Enb(self.enbIoService)
        self.ueProcedures = {}
        for i in range(2):
            self.ueProcedures[i] = UeRrcConnectionEstablishmentProcedure(
                {"nasMessageType": "attachRequest"}, 5, 0.7, 0.5, 2.0, (localhost(), 9000),
                self.ueIoServices[i], self.__procedureCompleteCallback__,
                {"ueIdentityType": "randomValue", "ueIdentityValue": 3434 * i,
                 "rrcEstablishmentCause": "moSignaling", "selectedPlmnIdentity": 2801})

    def tearDown(self):
        [s.stop() for s in self.ueIoServices]
        self.enbIoService.stop()

    def __procedureCompleteCallback__(self, result):
        self.ueresult = result

    def test_singleUeRrcEstablishmentSuccess(self):
        self.ueresult = None
        self.enbProcedure.execute()
        self.ueProcedures[0].execute()
        time.sleep(3)
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[0], EnbRrcConnectionEstablishmentProcedure.Success)        
        self.assertEqual(self.ueresult, UeRrcConnectionEstablishmentProcedure.Success)
        print "UE context information in eNB"
        print self.enbProcedure.ueContext       

    def test_twoUeRrcEstablishmentSuccess(self):
        self.ueresult = None
        self.enbProcedure.execute()
        self.ueProcedures[0].execute()
        time.sleep(0.6)  # MOTE: This test fails dues to timer error if sleep is less than this value
        # Exception: No running timer named 'randomAccessResponseTimeout' found
        self.ueProcedures[1].execute()
        time.sleep(3)
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[0], EnbRrcConnectionEstablishmentProcedure.Success)        
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[1], EnbRrcConnectionEstablishmentProcedure.Success)        
        self.assertEqual(self.ueresult, UeRrcConnectionEstablishmentProcedure.Success)
        print "UE context information in eNB"
        print self.enbProcedure.ueContext       


if __name__ == "__main__":
    unittest.main()