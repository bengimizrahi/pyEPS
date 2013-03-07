import unittest
import time

from epc.utils.io import IoService, localhost
from epc.procedures.ue.rrc import RrcConnectionEstablishmentProcedure
from epc.procedures.enb.rrc import EnbRrcConnectionEstablishmentProcedure, EnbMain
# bm: For the sake of DRY principle, I believe you should remove the 'Enb' prefix
#     from 'EnbRrcConnectionEstablishmentProcedure' since it resides in
#     epc.procedures.enb package. This, indeed, will cause name clash in this
#     test file. This should not be a problem since in the real use, these will
#     be used by different network nodes. For this test file you can solve the
#     name clash as follows:
#     from epc.procedures.ue.rrc import RrcConnectionEstablishmentProcedure as UeRrcConnectionEstablishmentProcedure
#     from epc.procedures.enb.rrc import RrcConnectionEstablishmentProcedure as EnbRrcConnectionEstablishmentProcedure
#     [remove this comment after the fix]
from epc.messages.rrc import rrcConnectionRequest, rrcConnectionSetupComplete

class Test_1_EnbRrcConnectionProcedure(unittest.TestCase):

    def setUp(self):
        self.enbIoService = IoService("enb", 9000)
        self.ueIoService = IoService("ue", 9001)
        [s.start() for s in self.enbIoService, self.ueIoService]
        self.enbProcedure = EnbRrcConnectionEstablishmentProcedure(3, 0.5, self.enbIoService, 
            self.__procedureEnbCompleteCallback__)

    def tearDown(self):
        [s.stop() for s in self.enbIoService, self.ueIoService]

    def __procedureEnbCompleteCallback__(self, result, a, b, args=None):
        self.enbResult = result

    def test_1_noRRCConnectionSetupCompleteReceived(self):
        self.enbResult = None
        temporaryCrnti = 0
        uplinkGrant = 34
        rrcTransactionIdentifier = 0
        interface, channelInfo, message = rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling")
        self.enbProcedure.handleRrcEstablishmentMessages((localhost(),9001),  interface, channelInfo, message, 
                {"temporaryCrnti": temporaryCrnti, "uplinkGrant": uplinkGrant, 
                 "rrcTransactionIdentifier": rrcTransactionIdentifier})
        time.sleep(1.7) # more than 3* 0.5 = 1.5 seconds
        self.assertEqual(self.enbResult,
            EnbRrcConnectionEstablishmentProcedure.ErrorNoRRCConnectionCompleteMessage)

    def test_2_rrcConnectionEstablishmentSuccess(self):
        self.enbResult = None
        temporaryCrnti = 0
        uplinkGrant = 34
        rrcTransactionIdentifier = 0
        interface, channelInfo, message = rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling")
        self.enbProcedure.handleRrcEstablishmentMessages((localhost(),9001),  interface, channelInfo, message, 
                {"temporaryCrnti": temporaryCrnti, "uplinkGrant": uplinkGrant, 
                 "rrcTransactionIdentifier": rrcTransactionIdentifier})
        time.sleep(0.2)
        interface, channelInfo, message = rrcConnectionSetupComplete(rrcTransactionIdentifier, 28001, {"nasMessageType": "attachRequest"})
        self.enbProcedure.handleRrcEstablishmentMessages((localhost(),9001),  interface, channelInfo, message)
        self.assertEqual(self.enbResult,
            EnbRrcConnectionEstablishmentProcedure.Success)

    def test_3_rrcConnectionEstablishmentSuccessSubsequentRrcCompleteIgnored(self):
        self.enbResult = None
        temporaryCrnti = 0
        uplinkGrant = 34
        rrcTransactionIdentifier = 0
        interface, channelInfo, message = rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling")
        self.enbProcedure.handleRrcEstablishmentMessages((localhost(),9001),  interface, channelInfo, message, 
                {"temporaryCrnti": temporaryCrnti, "uplinkGrant": uplinkGrant, 
                 "rrcTransactionIdentifier": rrcTransactionIdentifier})
        time.sleep(0.2)
        interface, channelInfo, message = rrcConnectionSetupComplete(rrcTransactionIdentifier, 28001, {"nasMessageType": "attachRequest"})
        self.enbProcedure.handleRrcEstablishmentMessages((localhost(),9001),  interface, channelInfo, message)
        self.assertEqual(self.enbResult, EnbRrcConnectionEstablishmentProcedure.Success)
        time.sleep(0.2)
        self.enbResult = None
        self.enbProcedure.handleRrcEstablishmentMessages((localhost(),9001),  interface, channelInfo, message)
        time.sleep(0.2)
        self.assertEqual(self.enbResult, None)

class Test_2_EnbMainProcedure(unittest.TestCase):

    def setUp(self):
        self.enbIoService = IoService("enb", 9000)
        self.ueIoServices = [IoService(str(i), 9001 + i) for i in range(2)]
        self.enbIoService.start()
        [s.start() for s in self.ueIoServices]
        self.enbProcedure = EnbMain(self.enbIoService)

    def tearDown(self):
        [s.stop() for s in self.ueIoServices]
        self.enbIoService.stop()

    def test1_noRRCConnectionSetupCompleteReceived(self):
        temporaryCrnti = 0
        self.enbProcedure.execute()
        interface, channelInfo, message = rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling")
        self.ueIoServices[0].sendMessage((localhost(),9000), interface, channelInfo, message)
        time.sleep(2.5) # more than 3* 0.5 = 1.5 seconds  + 0.5 seconds
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[temporaryCrnti], EnbRrcConnectionEstablishmentProcedure.ErrorNoRRCConnectionCompleteMessage)        

    def test2_singleUeRrcEstablishmentSuccess(self):
        temporaryCrnti = 0
        rrcTransactionIdentifier = 0
        self.enbProcedure.execute()
        interface, channelInfo, message = rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling")
        self.ueIoServices[0].sendMessage((localhost(),9000), interface, channelInfo, message)
        interface, channelInfo, message = rrcConnectionSetupComplete(rrcTransactionIdentifier, 28001, 
                                                                     {"nasMessageType": "attachRequest"})
        self.ueIoServices[0].sendMessage((localhost(),9000), interface, channelInfo, message)
        time.sleep(1.0) # ensure the enb call back is not waiting for rrc complete
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[temporaryCrnti], EnbRrcConnectionEstablishmentProcedure.Success)        
        print "UE context information in eNB"
        print self.enbProcedure.ueContext       

    def test3_twoUeRrcEstablishmentSuccess(self):
        self.ueResult = None
        self.enbResult = None
        self.enbProcedure.execute()
        for i in range(2):
            interface, channelInfo, message = rrcConnectionRequest(i, "randomValue", 3434, "moSignaling")
            self.ueIoServices[0].sendMessage((localhost(),9000), interface, channelInfo, message)
            time.sleep(0.5)
        time.sleep(0.2)
        for i in range(2):
            interface, channelInfo, message = rrcConnectionSetupComplete(i, 28001, 
                                                                     {"nasMessageType": "attachRequest"})
            self.ueIoServices[i].sendMessage((localhost(),9000), interface, channelInfo, message)
            time.sleep(0.2)
        time.sleep(1.0) # ensure the enb call back is not waiting for rrc complete
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[0], EnbRrcConnectionEstablishmentProcedure.Success)        
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[1], EnbRrcConnectionEstablishmentProcedure.Success)        
        print "UE context information in eNB"
        print self.enbProcedure.ueContext

class Test_3_Ue2EnbRrrcEstablishment(unittest.TestCase):

    def setUp(self):
        self.enbIoService = IoService("enb", 9000)
        self.ueIoServices = [IoService(str(i), 9001 + i) for i in range(2)]
        self.enbIoService.start()
        [s.start() for s in self.ueIoServices]
        self.enbProcedure = EnbMain(self.enbIoService)
        self.ueProcedures = {}
        for i in range(2):
            self.ueProcedures[i] = RrcConnectionEstablishmentProcedure(
                {"nasMessageType": "attachRequest"}, 5, 0.7, 0.5, 2.0, (localhost(), 9000),
                self.ueIoServices[i], self.__procedureCompleteCallback__,
                {"ueIdentityType": "randomValue", "ueIdentityValue": 3434*i,
                 "rrcEstablishmentCause": "moSignaling", "selectedPlmnIdentity": 2801})

    def tearDown(self):
        [s.stop() for s in self.ueIoServices]
        self.enbIoService.stop()

    def __procedureCompleteCallback__(self, result):
        self.ueresult = result

    def test1_singleUeRrcEstablishmentSuccess(self):
        self.ueresult = None
        self.enbProcedure.execute()
        self.ueProcedures[0].execute()
        time.sleep(3)
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[0], EnbRrcConnectionEstablishmentProcedure.Success)        
        self.assertEqual(self.ueresult, RrcConnectionEstablishmentProcedure.Success)
        print "UE context information in eNB"
        print self.enbProcedure.ueContext       

    def test2_twoUeRrcEstablishmentSuccess(self):
        self.ueresult = None
        self.enbProcedure.execute()
        self.ueProcedures[0].execute()
        time.sleep(0.6)  # MOTE: This test fails dues to timer error if sleep is less than this value
        # Exception: No running timer named 'randomAccessResponseTimeout' found
        self.ueProcedures[1].execute()
        time.sleep(3)
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[0], EnbRrcConnectionEstablishmentProcedure.Success)        
        self.assertEqual(self.enbProcedure.rrcEstablishmentSuccess[1], EnbRrcConnectionEstablishmentProcedure.Success)        
        self.assertEqual(self.ueresult, RrcConnectionEstablishmentProcedure.Success)
        print "UE context information in eNB"
        print self.enbProcedure.ueContext       


if __name__ == "__main__":
    unittest.main()