import unittest
import time

from epc.utils.io import IoService, localhost
from epc.procedures.ue.rrc import RrcConnectionEstablishmentProcedure

class Test_1_RrcConnectionProcedure(unittest.TestCase):

    def setUp(self):
        self.enbIoService = IoService("enb", 9000)
        self.ueIoService = IoService("ue", 9001)
        [s.start() for s in self.enbIoService, self.ueIoService]
        procedureParameters = {
            "initialNasMessage": {
             "nasMessageType": "attachRequest"
            },
            "maxPrachPreambleAttempts": 5,
            "prachPreambleRepeatDelay": 0.7,
            "macContentionResolutionTimeout": 0.5,
            "rrcConnectionSetupTimeoutT300": 2.0
        }
        self.procedure = RrcConnectionEstablishmentProcedure(procedureParameters, (localhost(), 9000),
            self.ueIoService, self.__procedureCompleteCallback__)
    
    def tearDown(self):
        [s.stop() for s in self.enbIoService, self.ueIoService]    

    def __procedureCompleteCallback__(self, result):
        self.result = result
    
    def test_1_noRandomAccessResponseReceived(self):
        self.result = None
        self.procedure.execute()
        time.sleep(3.7)
        self.assertEqual(self.result,
            RrcConnectionEstablishmentProcedure.ErrorNoRandomAccessResponse)
        self.procedure.terminate()

    def test_2_noContentionResolutionIdentityReceived(self):
        self.result = None
        self.procedure.execute()
        time.sleep(0.4) # smaller than 0.7
        self.enbIoService.sendMessage("ue", None, None, {"messageName": "randomAccessResponse"})
        time.sleep(2.0) # greater than 0.5
        self.assertEqual(self.result,
            RrcConnectionEstablishmentProcedure.ErrorNoContentionResolutionIdentity)
        self.procedure.terminate()

    def test_3_noRrcConnectionSetupReceived(self):
        self.result = None
        self.procedure.execute()
        time.sleep(0.4) # smaller than 0.7
        self.enbIoService.sendMessage("ue", None, None, {"messageName": "randomAccessResponse"})
        time.sleep(0.2) # smaller than 0.5
        self.enbIoService.sendMessage("ue", None, None, {"messageName": "contentionResolutionIdentity"})
        time.sleep(2.5) # greater than 2.0
        self.assertEqual(self.result,
            RrcConnectionEstablishmentProcedure.ErrorNoRrcConnectionSetup)
        self.procedure.terminate()
    
    def test_4_rrcConnectionEstablished(self):
        self.result = None
        self.procedure.execute()
        time.sleep(0.4) # smaller than 0.7
        self.enbIoService.sendMessage("ue", None, None, {"messageName": "randomAccessResponse"})
        time.sleep(0.2) # smaller than 0.5
        self.enbIoService.sendMessage("ue", None, None, {"messageName": "contentionResolutionIdentity"})
        time.sleep(0.5) # less than 2.0
        self.enbIoService.sendMessage("ue", None, None, {"messageName": "rrcConnectionSetup"})
        time.sleep(0.5)
        self.assertEqual(self.result, RrcConnectionEstablishmentProcedure.Success)
        self.procedure.terminate()

    def test_5_rrcConnectionEstablishedButSubsequentSetupsIgnored(self):
        self.result = None
        self.procedure.execute()
        time.sleep(0.4) # smaller than 0.7
        self.enbIoService.sendMessage("ue", None, None, {"messageName": "randomAccessResponse"})
        time.sleep(0.2) # smaller than 0.5
        self.enbIoService.sendMessage("ue", None, None, {"messageName": "contentionResolutionIdentity"})
        time.sleep(0.5) # smaller than 2.0
        self.enbIoService.sendMessage("ue", None, None, {"messageName": "rrcConnectionSetup"})
        time.sleep(0.3)
        self.assertEqual(self.result, RrcConnectionEstablishmentProcedure.Success)
        self.result = None
        self.enbIoService.sendMessage("ue", None, None, {"messageName": "rrcConnectionSetup"})
        time.sleep(0.2)
        self.assertEqual(self.result, None)
        self.procedure.terminate()

if __name__ == "__main__":
    unittest.main()