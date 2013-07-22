import unittest
import time

from eps.utils.io import IoService, localhost
from eps.procedures.mme.s11 import S11CreateSessionRequestProcedureHandler as MmeCreateSessionHandler
from eps.procedures.sgwpgw.s11 import S11CreateSessionRequestProcedureHandler as SgwPgwCreateSessionHandler
from eps.procedures.sgwpgw.s11 import BearerResourceHandler as SgwPgwBearerResourceHandler

class TestBearerResourcehandler(unittest.TestCase):
    
    def setUp(self):
        self.result = None

    def __bearerResourceCompletionCallback__(self, result, bearerContexts=None):
        self.result = result
        
    def test1_singleBearerContextCreation(self):
        bearerResourceHandler = SgwPgwBearerResourceHandler(localhost(),localhost())
        imsi = "2323"
        bearerContextsToBeCreated = [{"epsBearerId": 0, "bearerLevelQos": None}]
        bearerResourceHandler.allocateBearerResources(imsi, bearerContextsToBeCreated, self.__bearerResourceCompletionCallback__)
        self.assertEqual(self.result, SgwPgwBearerResourceHandler.Success)

    def test2_twoBearerContextCreation(self):
        bearerResourceHandler = SgwPgwBearerResourceHandler(localhost(), localhost())
        imsi = "2323"
        bearerContextsToBeCreated = [{"epsBearerId": 0, "bearerLevelQos": None},
                                     {"epsBearerId": 1, "bearerLevelQos": None}]
        bearerResourceHandler.allocateBearerResources(imsi, bearerContextsToBeCreated, self.__bearerResourceCompletionCallback__)
        self.assertEqual(self.result, SgwPgwBearerResourceHandler.Success)
        # print bearerResourceHandler.bearerContexts[imsi]

    def test3_duplicateBearerContextCreationFailure(self):
        bearerResourceHandler = SgwPgwBearerResourceHandler(localhost(),localhost())
        imsi = "2323"
        bearerContextsToBeCreated = [{"epsBearerId": 0, "bearerLevelQos": None},
                                     {"epsBearerId": 1, "bearerLevelQos": None}]
        bearerResourceHandler.allocateBearerResources(imsi, bearerContextsToBeCreated, self.__bearerResourceCompletionCallback__)
        self.assertEqual(self.result, SgwPgwBearerResourceHandler.Success)
        bearerContextsToBeCreated = [{"epsBearerId": 0, "bearerLevelQos": None},
                                     {"epsBearerId": 1, "bearerLevelQos": None}]
        bearerResourceHandler.allocateBearerResources(imsi, bearerContextsToBeCreated, self.__bearerResourceCompletionCallback__)
        self.assertEqual(self.result, SgwPgwBearerResourceHandler.ErrorPreExistingBearerContext)

class TestGtpcCreateSessionProcedureHandler(unittest.TestCase):

    def setUp(self):
        self.sgwPgwIoService = IoService("sgwPgw", 9000)
        self.sgwPgwIoService.start()
        self.mmeIoService = IoService("mme", 9001)
        self.mmeIoService.start()
        self.mmeResult, self.sgwPgwResult = 0, 0
        self.mmeSuccessCount, self.mmeFailureCount = 0, 0

    def tearDown(self):
        self.sgwPgwIoService.stop()
        self.mmeIoService.stop()

    def __mmeCreateSessionCompleteCallback__(self, result, responseMessageCause=None):
        self.mmeResult = result
        if result == MmeCreateSessionHandler.Success:
            self.mmeSuccessCount += 1
        else:
            self.mmeFailureCount += 1

    def __sgwPgwCreateSessionCompleteCallback__(self, result, sgwContextInfo=None):
        self.sgwPgwResult = result
        self.sgwContextInfo = sgwContextInfo
        # print sgwContextInfo

    def test_noCreateSessionResponseReceived(self):
        self.mmeResult = None
        mmeCreateSessionHandler = MmeCreateSessionHandler((localhost(), 9002), self.mmeIoService, 0.5, 3, self.__mmeCreateSessionCompleteCallback__)
        self.mmeIoService.addIncomingMessageCallback(mmeCreateSessionHandler.handleIncomingMessage)
        imsi = "35353"
        createSessionRequestMessage = \
            {"imsi": imsi,
             "pgwS5S8AddressForContolPlane": {"interfaceType": "ipv4", "teid": 0, 
                                              "address": localhost()}, 
             "senderFteidForControlPlane": {"interfaceType": "ipv4", "teid": 45, "address": localhost()},
             "pdnAddressAllocation": {"pdnType": "ipv4", "pdnAddressAndPrefix": "0.0.0.0"},
             "bearerContextsToBeCreated": [{"epsBearerId": 0, 
                                           "s1uEnbFteid": {"interfaceType": "ipv4", "teid": 45, "address": localhost()}, 
                                           "bearerLevelQos": None}]
            }
        mmeCreateSessionHandler.execute(imsi, createSessionRequestMessage)
        time.sleep(0.5*3 + 0.2)
        self.assertEqual(self.mmeResult,
            MmeCreateSessionHandler.ErrorNoCreateSessionResponse)
   
    def test_nNoCreateSessionResponseReceived(self):
        self.mmeResult = None
        mmeCreateSessionHandler = MmeCreateSessionHandler((localhost(), 9002), self.mmeIoService, 0.5, 3, self.__mmeCreateSessionCompleteCallback__)
        self.mmeIoService.addIncomingMessageCallback(mmeCreateSessionHandler.handleIncomingMessage)
        for i in range(100):
            imsi = "2867" + str(i)
            createSessionRequestMessage = \
                {"imsi": imsi,
                 "senderFteidForControlPlane": {"interfaceType": "ipv4", "teid": i, "address": localhost()},
                 "pgwS5S8AddressForContolPlane": {"interfaceType": "ipv4", "teid": 0, 
                                                  "address": localhost()}, 
                 "pdnAddressAllocation": {"pdnType": "ipv4", "pdnAddressAndPrefix": "0.0.0.0"},
                 "bearerContextsToBeCreated": [{"epsBearerId": 0, 
                                               "s1uEnbFteid": {"interfaceType": "ipv4", "teid": 45, "address": localhost()}, 
                                               "bearerLevelQos": None}]
                }
            mmeCreateSessionHandler.execute(imsi, createSessionRequestMessage)
        time.sleep(0.5*3 + 0.5)
        self.assertEqual(self.mmeFailureCount, 100)

    def test_CreateSessionProcedureSuccess(self):
        mmeCreateSessionHandler = MmeCreateSessionHandler((localhost(), 9000), self.mmeIoService, 0.5, 3, self.__mmeCreateSessionCompleteCallback__)
        self.mmeIoService.addIncomingMessageCallback(mmeCreateSessionHandler.handleIncomingMessage)        
        sgwPgwBearerResourceHandler = SgwPgwBearerResourceHandler(localhost(), localhost())
        sgwPgwCreateSessionHandler = SgwPgwCreateSessionHandler((localhost(), 9001), localhost(), self.sgwPgwIoService, 
                                                          sgwPgwBearerResourceHandler, self.__sgwPgwCreateSessionCompleteCallback__)
        self.sgwPgwIoService.addIncomingMessageCallback(sgwPgwCreateSessionHandler.handleCreateSessionRequestMessage)
        imsi = "35353"
        createSessionRequestMessage = \
            {"imsi": imsi,
             "senderFteidForControlPlane": {"interfaceType": "ipv4", "teid": 45, "address": localhost()},
             "pgwS5S8AddressForContolPlane": {"interfaceType": "ipv4", "teid": 0, 
                                              "address": localhost()}, 
             "pdnAddressAllocation": {"pdnType": "ipv4", "pdnAddressAndPrefix": "0.0.0.0"},
             "bearerContextsToBeCreated": [{"epsBearerId": 0, 
                                           "bearerLevelQos": None}]
            }
        mmeCreateSessionHandler.execute(imsi, createSessionRequestMessage)
        time.sleep(1.0)
        self.assertEqual(self.mmeResult, MmeCreateSessionHandler.Success)
        self.assertEqual(self.sgwPgwResult, SgwPgwCreateSessionHandler.Success)

    def test_DuplicateCreateSessionRequestProcedureSuccess(self):
        mmeCreateSessionHandler = MmeCreateSessionHandler((localhost(), 9000), self.mmeIoService, 0.5, 3, self.__mmeCreateSessionCompleteCallback__)
        self.mmeIoService.addIncomingMessageCallback(mmeCreateSessionHandler.handleIncomingMessage)        
        sgwPgwBearerResourceHandler = SgwPgwBearerResourceHandler(localhost(), localhost())
        sgwPgwCreateSessionHandler = SgwPgwCreateSessionHandler((localhost(), 9001), localhost(), self.sgwPgwIoService, 
                                                          sgwPgwBearerResourceHandler, self.__sgwPgwCreateSessionCompleteCallback__)
        self.sgwPgwIoService.addIncomingMessageCallback(sgwPgwCreateSessionHandler.handleCreateSessionRequestMessage)
        imsi = "35353"
        createSessionRequestMessage = \
            {"imsi": imsi,
             "senderFteidForControlPlane": {"interfaceType": "ipv4", "teid": 45, "address": localhost()},
             "pgwS5S8AddressForContolPlane": {"interfaceType": "ipv4", "teid": 0, 
                                              "address": localhost()}, 
             "pdnAddressAllocation": {"pdnType": "ipv4", "pdnAddressAndPrefix": "0.0.0.0"},
             "bearerContextsToBeCreated": [{"epsBearerId": 0, 
                                           "bearerLevelQos": None}]
            }
        mmeCreateSessionHandler.execute(imsi, createSessionRequestMessage)
        time.sleep(1.0)
        self.assertEqual(self.mmeResult, MmeCreateSessionHandler.Success)
        self.assertEqual(self.sgwPgwResult, SgwPgwCreateSessionHandler.Success)
        mmeCreateSessionHandler.execute(imsi, createSessionRequestMessage)  # send duplicate message but with a new sequence number
        time.sleep(1.0)
        self.assertEqual(self.mmeResult, MmeCreateSessionHandler.Success)
        self.assertEqual(self.sgwPgwResult, SgwPgwCreateSessionHandler.Success)

    def test_nCreateSessionProcedureSuccess(self):
        mmeCreateSessionHandler = MmeCreateSessionHandler((localhost(), 9000), self.mmeIoService, 0.5, 3, self.__mmeCreateSessionCompleteCallback__)
        self.mmeIoService.addIncomingMessageCallback(mmeCreateSessionHandler.handleIncomingMessage)        
        sgwPgwBearerResourceHandler = SgwPgwBearerResourceHandler(localhost(), localhost())
        sgwPgwCreateSessionHandler = SgwPgwCreateSessionHandler((localhost(), 9001), localhost(), self.sgwPgwIoService, 
                                                          sgwPgwBearerResourceHandler, self.__sgwPgwCreateSessionCompleteCallback__)
        self.sgwPgwIoService.addIncomingMessageCallback(sgwPgwCreateSessionHandler.handleCreateSessionRequestMessage)
        imsiArray = []
        for i in range(100):
            imsi = "2867" + str(i)
            imsiArray.append(imsi)
            createSessionRequestMessage = \
                {"imsi": imsi,
                 "senderFteidForControlPlane": {"interfaceType": "ipv4", "teid": i, "address": localhost()},
                 "pgwS5S8AddressForContolPlane": {"interfaceType": "ipv4", "teid": 0, 
                                                  "address": localhost()}, 
                 "pdnAddressAllocation": {"pdnType": "ipv4", "pdnAddressAndPrefix": "0.0.0.0"},
                 "bearerContextsToBeCreated": [{"epsBearerId": 0, 
                                               "bearerLevelQos": None}]
                }
            mmeCreateSessionHandler.execute(imsi, createSessionRequestMessage)
            time.sleep(0.01)
        time.sleep(1.0)
        self.assertEqual(self.mmeSuccessCount, 100)
        self.assertEqual(set(sgwPgwCreateSessionHandler.establishedS11SessionContexts), set(imsiArray))
        mmeTeidsForControlPlane = []
        for i in range(100):
            imsi = "2867" + str(i)
            mmeTeidsForControlPlane.append(sgwPgwCreateSessionHandler.establishedS11SessionContexts[imsi]["mmeFteidForControlPlane"]["teid"])
        self.assertEqual(set(mmeTeidsForControlPlane), set(range(100)))

if __name__ == "__main__":
    unittest.main()