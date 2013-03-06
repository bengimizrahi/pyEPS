import unittest
import time

from epc.utils.io import IoService, localhost
from epc.procedures.ue.rrc import RrcConnectionEstablishmentProcedure
from epc.messages import randomAccessResponse, contentionResolutionIdentity, rrcConnectionSetup 

class Test_1_RrcConnectionProcedure(unittest.TestCase):

    def setUp(self):
        self.enbIoService = IoService("enb", 9000)
        self.ueIoService = IoService("ue", 9001)
        [s.start() for s in self.enbIoService, self.ueIoService]
        self.procedure = RrcConnectionEstablishmentProcedure(
            {"nasMessageType": "attachRequest"}, 5, 0.7, 0.5, 2.0, (localhost(), 9000),
            self.ueIoService, self.__procedureCompleteCallback__,
            {"ueIdentityType": "randomValue", "ueIdentityValue": 3434,
             "rrcEstablishmentCause": "moSignaling", "selectedPlmnIdentity": 2801})
    
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

    def test_2_noContentionResolutionIdentityReceived(self):
        self.result = None
        self.procedure.execute()
        time.sleep(0.4) # smaller than 0.7
        temporaryCrnti = 43
        uplinkGrant = 12
        interface, channelInfo, message = randomAccessResponse(self.procedure.raRnti, self.procedure.rapid, temporaryCrnti, uplinkGrant)
        self.enbIoService.sendMessage("ue", interface, channelInfo, message)
        time.sleep(2.0) # greater than 0.5
        self.assertEqual(self.result,
            RrcConnectionEstablishmentProcedure.ErrorNoContentionResolutionIdentity)

    def test_3_noRrcConnectionSetupReceived(self):
        self.result = None
        self.procedure.execute()
        time.sleep(0.4) # smaller than 0.7
        temporaryCrnti = 43
        uplinkGrant = 12
        interface, channelInfo, message = randomAccessResponse(self.procedure.raRnti, self.procedure.rapid, temporaryCrnti, uplinkGrant)
        self.enbIoService.sendMessage("ue", interface, channelInfo, message)
        time.sleep(0.2) # smaller than 0.5       
        interface, channelInfo, message = contentionResolutionIdentity(temporaryCrnti,                                                                                        
                                                                    self.procedure.rrcConnectionRequestMessage)
        message["messageName"] = "contentionResolutionIdentity"
        self.enbIoService.sendMessage("ue", interface, channelInfo, message)
        time.sleep(2.5) # greater than 2.0
        self.assertEqual(self.result,
            RrcConnectionEstablishmentProcedure.ErrorNoRrcConnectionSetup)
    
    def test_4_rrcConnectionEstablished(self):
        self.result = None
        self.procedure.execute()
        time.sleep(0.4) # smaller than 0.7
        temporaryCrnti = 43
        uplinkGrant = 12
        interface, channelInfo, message = randomAccessResponse(self.procedure.raRnti, self.procedure.rapid, temporaryCrnti, uplinkGrant)
        self.enbIoService.sendMessage("ue", interface, channelInfo, message)
        time.sleep(0.2) # smaller than 0.5
        interface, channelInfo, message = contentionResolutionIdentity(temporaryCrnti,                                                                                        
                                                                    self.procedure.rrcConnectionRequestMessage)
        message["messageName"] = "contentionResolutionIdentity"
        self.enbIoService.sendMessage("ue", interface, channelInfo, message)
        time.sleep(0.5) # less than 2.0
        rrcTransactionIdentifier = 4
        interface, channelInfo, message = rrcConnectionSetup(temporaryCrnti, rrcTransactionIdentifier)
        self.enbIoService.sendMessage("ue", interface, channelInfo, message)
        time.sleep(0.5)
        self.assertEqual(self.result, RrcConnectionEstablishmentProcedure.Success)

    def test_5_rrcConnectionEstablishedButSubsequentSetupsIgnored(self):
        self.result = None
        self.procedure.execute()
        time.sleep(0.4) # smaller than 0.7
        temporaryCrnti = 43
        uplinkGrant = 12
        interface, channelInfo, message = randomAccessResponse(self.procedure.raRnti, self.procedure.rapid, temporaryCrnti, uplinkGrant)
        self.enbIoService.sendMessage("ue", interface, channelInfo, message)
        time.sleep(0.2) # smaller than 0.5
        interface, channelInfo, message = contentionResolutionIdentity(temporaryCrnti,                                                                                        
                                                                    self.procedure.rrcConnectionRequestMessage)
        message["messageName"] = "contentionResolutionIdentity"
        self.enbIoService.sendMessage("ue", interface, channelInfo, message)
        time.sleep(0.5) # less than 2.0
        rrcTransactionIdentifier = 4
        interface, channelInfo, message = rrcConnectionSetup(temporaryCrnti, rrcTransactionIdentifier)
        self.enbIoService.sendMessage("ue", interface, channelInfo, message)
        time.sleep(0.5)
        self.assertEqual(self.result, RrcConnectionEstablishmentProcedure.Success)
        self.result = None
        self.enbIoService.sendMessage("ue", interface, channelInfo, message)
        time.sleep(0.2)
        self.assertEqual(self.result, None)

if __name__ == "__main__":
    unittest.main()