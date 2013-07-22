import unittest
import time
import random

from ...utils.io import IoService, localhost
from ...procedures.mme.s6a import AuthenticationInformationRetrievalProcedureHandler as MmeAuthProcedureHandler
from ...procedures.hss.s6a import AuthenticationInformationRetrievalProcedureHandler as HssAuthProcedureHandler


class TestS1SetupProcedureHandler(unittest.TestCase):

    def setUp(self):
        self.hssIoService = IoService("hss", 9000)
        self.hssIoService.start()
        self.mmeIoService = IoService("mme", 9001)
        self.mmeIoService.start()
        self.mmeSuccess, self.hssSuccess = 0, 0

    def tearDown(self):
        self.hssIoService.stop()
        self.mmeIoService.stop()

    def __mmeAuthCompleteCallback__(self, result, authContext=None):
        self.mmeSuccess += 1

    def __hssAuthCompleteCallback__(self, result, imsi):
        self.hssSuccess += 1

    def test_nAuthInfoRetrievalProcedureSuccess(self):
        n = 100
        visitedPlmnId = "28603"
        mmeAuthProcHandler = MmeAuthProcedureHandler((localhost(), 9000), self.mmeIoService, self.__mmeAuthCompleteCallback__)
        self.mmeIoService.addIncomingMessageCallback(mmeAuthProcHandler.handleIncomingMessage)
        hssAuthProcHandler = HssAuthProcedureHandler(self.hssIoService, self.__hssAuthCompleteCallback__)
        self.hssIoService.addIncomingMessageCallback(hssAuthProcHandler.handleIncomingMessage)
        for _ in range(n):
            randomImsi = visitedPlmnId + "".join([str(random.randrange(0, 10)) for __ in range(10)])
            mmeAuthProcHandler.execute(randomImsi, visitedPlmnId)
        time.sleep(1.0)
        self.assertEqual(self.mmeSuccess, n)
        self.assertEqual(self.hssSuccess, n)