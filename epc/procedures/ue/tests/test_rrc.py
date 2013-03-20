import unittest
import time

from epc.utils.io import IoService, localhost
from epc.procedures.ue.rrc import RrcConnectionEstablishmentProcedure
from epc.messages.rrc import randomAccessResponse, contentionResolutionIdentity, rrcConnectionSetup 

class TestRrcConnectionProcedure(unittest.TestCase):

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
        args = {
            "ueIdentityType": "randomValue",
            "ueIdentityValue": 3434,
            "rrcEstablishmentCause": "moSignaling",
            "selectedPlmnIdentity": 2801
        }
        self.procedure = RrcConnectionEstablishmentProcedure(
            procedureParameters, (localhost(), 9000),
            self.ueIoService, self.__procedureCompleteCallback__, args)
    
    def tearDown(self):
        [s.stop() for s in self.enbIoService, self.ueIoService]    

    def __procedureCompleteCallback__(self, result):
        self.result = result
    
    def test_noRandomAccessResponseReceived(self):
        self.result = None
        self.procedure.execute()
        time.sleep(3.7)
        self.assertEqual(self.result,
            RrcConnectionEstablishmentProcedure.ErrorNoRandomAccessResponse)
        self.procedure.terminate()

    def test_noContentionResolutionIdentityReceived(self):
        self.result = None
        self.procedure.execute()
        time.sleep(0.4) # smaller than 0.7
        temporaryCrnti = 43
        uplinkGrant = 12
        # bm: I shorten the code using the '*'. This is called 'unpacking arguments'.
        #     What it basically does is it aligns right part of '*' into argument list
        #     the called function. randomAccessResponse() returns a list of values,
        #     this values are aligned one by one in the called function.
        #     [remove this comment after read]
        self.enbIoService.sendMessage("ue", *randomAccessResponse(
            self.procedure.raRnti, self.procedure.rapid, temporaryCrnti, uplinkGrant))
        time.sleep(2.0) # greater than 0.5
        self.assertEqual(self.result,
            RrcConnectionEstablishmentProcedure.ErrorNoContentionResolutionIdentity)
        self.procedure.terminate()

    def test_noRrcConnectionSetupReceived(self):
        self.result = None
        self.procedure.execute()
        time.sleep(0.4) # smaller than 0.7
        temporaryCrnti = 43
        uplinkGrant = 12
        self.enbIoService.sendMessage("ue", *randomAccessResponse(
            self.procedure.raRnti, self.procedure.rapid, temporaryCrnti, uplinkGrant))
        time.sleep(0.2) # smaller than 0.5       
        interface, channelInfo, message = contentionResolutionIdentity(
            temporaryCrnti, self.procedure.rrcConnectionRequestMessage)
        message["messageType"] = "contentionResolutionIdentity"
        # bm: Why is 'messageType' not entered in message creation function?
        #     [remove this comment after the fix, or immediately if this should be
        #      the way to go]
        self.enbIoService.sendMessage("ue", interface, channelInfo, message)
        time.sleep(2.5) # greater than 2.0
        self.assertEqual(self.result,
            RrcConnectionEstablishmentProcedure.ErrorNoRrcConnectionSetup)
        self.procedure.terminate()
    
    def test_rrcConnectionEstablished(self):
        self.result = None
        self.procedure.execute()
        time.sleep(0.4) # smaller than 0.7
        temporaryCrnti = 43
        uplinkGrant = 12
        self.enbIoService.sendMessage("ue", *randomAccessResponse(
            self.procedure.raRnti, self.procedure.rapid, temporaryCrnti, uplinkGrant))
        time.sleep(0.2) # smaller than 0.5
        interface, channelInfo, message = contentionResolutionIdentity(
            temporaryCrnti, self.procedure.rrcConnectionRequestMessage)
        message["messageType"] = "contentionResolutionIdentity"
        # bm: Why is 'messageType' not entered in message creation function?
        #     [remove this comment after the fix, or immediately if this should be
        #      the way to go]
        self.enbIoService.sendMessage("ue", interface, channelInfo, message)
        time.sleep(0.5) # less than 2.0
        rrcTransactionIdentifier = 4
        interface, channelInfo, message = rrcConnectionSetup(temporaryCrnti, rrcTransactionIdentifier)
        self.enbIoService.sendMessage("ue", interface, channelInfo, message)
        time.sleep(0.5)
        self.assertEqual(self.result, RrcConnectionEstablishmentProcedure.Success)
        self.procedure.terminate()

    def test_rrcConnectionEstablishedButSubsequentSetupsIgnored(self):
        self.result = None
        self.procedure.execute()
        time.sleep(0.4) # smaller than 0.7
        temporaryCrnti = 43
        uplinkGrant = 12
        self.enbIoService.sendMessage("ue", *randomAccessResponse(
            self.procedure.raRnti, self.procedure.rapid, temporaryCrnti, uplinkGrant))
        time.sleep(0.2) # smaller than 0.5
        interface, channelInfo, message = contentionResolutionIdentity(
            temporaryCrnti, self.procedure.rrcConnectionRequestMessage)
        message["messageType"] = "contentionResolutionIdentity"
        # bm: Why is 'messageType' not entered in message creation function?
        #     [remove this comment after the fix, or immediately if this should be
        #      the way to go]
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
        self.procedure.terminate()

if __name__ == "__main__":
    unittest.main()