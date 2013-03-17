import unittest
import time

from epc.utils.io import IoService, localhost
from epc.procedures.mme.s11 import S11CreateSessionRequestProcedureHandler as MmeCreateSessionHandler
from epc.procedures.sgwpgw.s11 import S11CreateSessionRequestProcedureHandler as SgwPgwCreateSessionHandler
from epc.procedures.sgwpgw.s11 import BearerResourceHandler as SgwPgwBearerResourceHandler

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

    def tearDown(self):
        self.sgwPgwIoService.stop()
        self.mmeIoService.stop()

    def __mmeCreateSessionCompleteCallback__(self, result):
        self.mmeResult = result

    def __sgwPgwCreateSessionCompleteCallback__(self, result, sgwContextInfo=None):
        self.sgwPgwResult = result
        self.sgwContextInfo = sgwContextInfo
        # print sgwContextInfo

    def test_noCreateSessionResponseReceived(self):
        self.mmeResult = None
        mmeCreateSessionHandler = MmeCreateSessionHandler((localhost(), 9002), self.mmeIoService, 0.5, 3, self.__mmeCreateSessionCompleteCallback__)
        self.mmeIoService.addIncomingMessageCallback(mmeCreateSessionHandler.handleIncomingMessage)
        imsi = "35353"
        createSessionRequestParameters = \
            {"pgwS5S8AddressForContolPlane": {"interfaceType": "ipv4", "teid": 0, 
                                              "address": localhost()}, 
             "pdnAddressAllocation": {"pdnType": "ipv4", "pdnAddressAndPrefix": "0.0.0.0"},
             "bearerContextsToBeCreated": [{"epsBearerId": 0, 
                                           "s1uEnbFteid": {"interfaceType": "ipv4", "teid": 45, "address": localhost()}, 
                                           "bearerLevelQos": None}]
            }
        mmeCreateSessionHandler.execute(imsi, createSessionRequestParameters)
        time.sleep(0.5*3 + 0.2)
        self.assertEqual(self.mmeResult,
            MmeCreateSessionHandler.ErrorNoCreateSessionResponse)
   
    def test_CreateSessionProcedureSuccess(self):
        mmeCreateSessionHandler = MmeCreateSessionHandler((localhost(), 9000), self.mmeIoService, 0.5, 3, self.__mmeCreateSessionCompleteCallback__)
        self.mmeIoService.addIncomingMessageCallback(mmeCreateSessionHandler.handleIncomingMessage)        
        sgwPgwBearerResourceHandler = SgwPgwBearerResourceHandler(localhost(), localhost())
        sgwPgwCreateSessionHandler = SgwPgwCreateSessionHandler((localhost(), 9001), localhost(), self.sgwPgwIoService, 
                                                          sgwPgwBearerResourceHandler, self.__sgwPgwCreateSessionCompleteCallback__)
        self.sgwPgwIoService.addIncomingMessageCallback(sgwPgwCreateSessionHandler.handleCreateSessionRequestMessage)
        createSessionRequestParameters = \
            {"pgwS5S8AddressForContolPlane": {"interfaceType": "ipv4", "teid": 0, 
                                              "address": localhost()}, 
             "pdnAddressAllocation": {"pdnType": "ipv4", "pdnAddressAndPrefix": "0.0.0.0"},
             "bearerContextsToBeCreated": [{"epsBearerId": 0, 
                                           "bearerLevelQos": None}]
            }
        imsi = "35353"
        mmeCreateSessionHandler.execute(imsi, createSessionRequestParameters)
        time.sleep(1.0)
        self.assertEqual(self.mmeResult, MmeCreateSessionHandler.Success)
        self.assertEqual(self.sgwPgwResult, SgwPgwCreateSessionHandler.Success)

#    def test_nCreateSessionProcedureSuccess(self):
#        n = 100
#        visitedPlmnId = "28603"
#        mmeAuthProcHandler = MmeAuthProcedureHandler((localhost(), 9000), self.mmeIoService, self.__mmeAuthCompleteCallback__)
#        self.mmeIoService.addIncomingMessageCallback(mmeAuthProcHandler.handleIncomingMessage)
#        hssAuthProcHandler = HssAuthProcedureHandler(self.hssIoService, self.__hssAuthCompleteCallback__)
#        self.hssIoService.addIncomingMessageCallback(hssAuthProcHandler.handleIncomingMessage)
#        for _ in range(n):
#            randomImsi = visitedPlmnId + "".join([str(random.randrange(0, 10)) for __ in range(10)])
#            mmeAuthProcHandler.execute(randomImsi, visitedPlmnId)
#        time.sleep(1.0)
#        self.assertEqual(self.mmeSuccess, n)
#        self.assertEqual(self.hssSuccess, n)


if __name__ == "__main__":
    unittest.main()