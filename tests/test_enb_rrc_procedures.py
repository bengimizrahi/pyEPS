import unittest
import time

from epc.utils.io import IoService, localhost
from epc.procedures.ue.rrc import RrcConnectionEstablishmentProcedure
from epc.procedures.enb.rrc import EnbRrcConnectionEstablishmentProcedure, EnbMain
from epc.messages import rrcConnectionRequest, rrcConnectionSetupComplete

class Test_1_EnbRrcConnectionProcedure(unittest.TestCase):

    def setUp(self):
        self.enbIoService = IoService("enb", 9000)
        self.ueIoService = IoService("ue", 9001)
        [s.start() for s in self.enbIoService, self.ueIoService]
        self.enbProcedure = EnbRrcConnectionEstablishmentProcedure(3, 0.5, self.enbIoService, 
            self.__procedureEnbCompleteCallback__)
    
    def tearDown(self):
        [s.stop() for s in self.enbIoService, self.ueIoService]
   
    def __procedureEnbCompleteCallback__(self, result, args=None):
        self.enbResult = result
  
    def test_1_noRRCConnectionSetupCompleteReceived(self):
        self.enbResult = None
        temporaryCrnti = 200
        uplinkGrant = 34
        rrcTransactionIdentifier = 20
        interface, channelInfo, message = rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling")
        #self.ueIoService.sendMessage((localhost(),9000), interface, channelInfo, message)
        # time.sleep(0.2) # wait so that the message is not sent the the enb rrc message handler
        self.enbProcedure.handleRrcEstablishmentMessages((localhost(),9001),  interface, channelInfo, message, 
                {"temporaryCrnti": temporaryCrnti, "uplinkGrant": uplinkGrant, 
                 "rrcTransactionIdentifier": rrcTransactionIdentifier})
        time.sleep(1.7) # more than 3* 0.5 = 1.5 seconds
        self.assertEqual(self.enbResult,
            EnbRrcConnectionEstablishmentProcedure.ErrorNoRRCConnectionCompleteMessage)

    def test_2_rrcConnectionEstablishmentSuccess(self):
        self.enbResult = None
        temporaryCrnti = 200
        uplinkGrant = 34
        rrcTransactionIdentifier = 20
        interface, channelInfo, message = rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling")
        # self.ueIoService.sendMessage((localhost(),9000), interface, channelInfo, message)
        #time.sleep(0.2) # wait so that the message is not sent the the enb rrc message handler
        self.enbProcedure.handleRrcEstablishmentMessages((localhost(),9001),  interface, channelInfo, message, 
                {"temporaryCrnti": temporaryCrnti, "uplinkGrant": uplinkGrant, 
                 "rrcTransactionIdentifier": rrcTransactionIdentifier})
        time.sleep(0.2)
        interface, channelInfo, message = rrcConnectionSetupComplete(rrcTransactionIdentifier, 28001, {"nasMessageType": "attachRequest"})
        # self.ueIoService.sendMessage((localhost(),9000), interface, channelInfo, message)
        # time.sleep(0.2) # more than 3* 0.5 = 1.5 seconds
        self.enbProcedure.handleRrcEstablishmentMessages((localhost(),9001),  interface, channelInfo, message)
        self.assertEqual(self.enbResult,
            EnbRrcConnectionEstablishmentProcedure.Success)
        
    def test_3_rrcConnectionEstablishmentSuccessSubsequentRrcCompleteIgnored(self):
        self.enbResult = None
        temporaryCrnti = 200
        uplinkGrant = 34
        rrcTransactionIdentifier = 20
        interface, channelInfo, message = rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling")
        # self.ueIoService.sendMessage((localhost(),9000), interface, channelInfo, message)
        # time.sleep(0.2) # wait so that the message is not sent the the enb rrc message handler
        self.enbProcedure.handleRrcEstablishmentMessages((localhost(),9001),  interface, channelInfo, message, 
                {"temporaryCrnti": temporaryCrnti, "uplinkGrant": uplinkGrant, 
                 "rrcTransactionIdentifier": rrcTransactionIdentifier})
        time.sleep(0.2)
        interface, channelInfo, message = rrcConnectionSetupComplete(rrcTransactionIdentifier, 28001, {"nasMessageType": "attachRequest"})
        # self.ueIoService.sendMessage((localhost(),9000), interface, channelInfo, message)
        # time.sleep(0.2) # more than 3* 0.5 = 1.5 seconds
        self.enbProcedure.handleRrcEstablishmentMessages((localhost(),9001),  interface, channelInfo, message)
        self.assertEqual(self.enbResult, EnbRrcConnectionEstablishmentProcedure.Success)
        time.sleep(0.2)
        self.enbResult = None
        self.enbProcedure.handleRrcEstablishmentMessages((localhost(),9001),  interface, channelInfo, message)
        time.sleep(0.2)
        self.assertEqual(self.enbResult, None)

#class Test_2_EnbeMainProcedure(unittest.TestCase):
#
#    def setUp(self):
#        self.enbIoService = IoService("enb", 9000)
#        self.ueIoService = IoService("ue", 9001)
#        [s.start() for s in self.enbIoService, self.ueIoService]
#        self.ueProcedure = RrcConnectionEstablishmentProcedure(
#            {"nasMessageType": "attachRequest"}, 5, 0.7, 0.5, 2.0, (localhost(), 9000),
#            self.ueIoService, self.__procedureUeCompleteCallback__)
#        self.enbProcedure = EnbMain(self.enbIoService, self.__procedureEnbCompleteCallback__)
#    
#    def tearDown(self):
#        [s.stop() for s in self.enbIoService, self.ueIoService]
#
#    def __procedureUeCompleteCallback__(self, result):
#        self.ueResult = result
#    
#    def __procedureEnbCompleteCallback__(self, results):
#        self.enbResults = results
#    
#    def test1_singleRrcEstablishmentSuccess(self):
#        self.ueResult = None
#        self.enbResults = None
#        temporaryCrnti = 200
#        rrcTransactionIdentifier = 20
#        self.enbProcedure.execute()
#        interface, channelInfo, message = rrcConnectionRequest(temporaryCrnti, "randomValue", 3434, "moSignaling")
#        self.ueIoService.sendMessage((localhost(),9000), interface, channelInfo, message)
#        time.sleep(0.2)
#        interface, channelInfo, message = rrcConnectionSetupComplete(rrcTransactionIdentifier, 28001, 
#                                                                     {"nasMessageType": "attachRequest"})
#        self.ueIoService.sendMessage((localhost(),9000), interface, channelInfo, message)
#        time.sleep(0.2) # more than 3* 0.5 = 1.5 seconds
#        self.assertEqual(self.enbResults, EnbRrcConnectionEstablishmentProcedure.Success)        
        
        
#    def test_2_noContentionResolutionIdentityReceived(self):
#        self.result = None
#        self.procedure.execute()
#        time.sleep(0.4) # smaller than 0.7
#        self.enbIoService.sendMessage("ue", None, None, {"messageName": "randomAccessResponse"})
#        time.sleep(2.0) # greater than 0.5
#        self.assertEqual(self.result,
#            RrcConnectionEstablishmentProcedure.ErrorNoContentionResolutionIdentity)
#
#    def test_3_noRrcConnectionSetupReceived(self):
#        self.result = None
#        self.procedure.execute()
#        time.sleep(0.4) # smaller than 0.7
#        self.enbIoService.sendMessage("ue", None, None, {"messageName": "randomAccessResponse"})
#        time.sleep(0.2) # smaller than 0.5
#        self.enbIoService.sendMessage("ue", None, None, {"messageName": "contentionResolutionIdentity"})
#        time.sleep(2.5) # greater than 2.0
#        self.assertEqual(self.result,
#            RrcConnectionEstablishmentProcedure.ErrorNoRrcConnectionSetup)
#    
#    def test_4_rrcConnectionEstablished(self):
#        self.result = None
#        self.procedure.execute()
#        time.sleep(0.4) # smaller than 0.7
#        self.enbIoService.sendMessage("ue", None, None, {"messageName": "randomAccessResponse"})
#        time.sleep(0.2) # smaller than 0.5
#        self.enbIoService.sendMessage("ue", None, None, {"messageName": "contentionResolutionIdentity"})
#        time.sleep(0.5) # less than 2.0
#        self.enbIoService.sendMessage("ue", None, None, {"messageName": "rrcConnectionSetup"})
#        time.sleep(0.5)
#        self.assertEqual(self.result, RrcConnectionEstablishmentProcedure.Success)
#
#    def test_5_rrcConnectionEstablishedButSubsequentSetupsIgnored(self):
#        self.result = None
#        self.procedure.execute()
#        time.sleep(0.4) # smaller than 0.7
#        self.enbIoService.sendMessage("ue", None, None, {"messageName": "randomAccessResponse"})
#        time.sleep(0.2) # smaller than 0.5
#        self.enbIoService.sendMessage("ue", None, None, {"messageName": "contentionResolutionIdentity"})
#        time.sleep(0.5) # smaller than 2.0
#        self.enbIoService.sendMessage("ue", None, None, {"messageName": "rrcConnectionSetup"})
#        time.sleep(0.3)
#        self.assertEqual(self.result, RrcConnectionEstablishmentProcedure.Success)
#        self.result = None
#        self.enbIoService.sendMessage("ue", None, None, {"messageName": "rrcConnectionSetup"})
#        time.sleep(0.2)
#        self.assertEqual(self.result, None)

if __name__ == "__main__":
    unittest.main()