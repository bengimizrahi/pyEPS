import unittest
import time

from eps.utils.io import IoService, localhost
from eps.procedures.enb.s1ap import S1SetupProcedure as EnbS1SetupProcedure
from eps.procedures.mme.s1ap import S1SetupProcedureHandler as MmeS1SetupProcedureHandler
from eps.nodes.mme.mme.Default import MmeServiceArea

class TestS1SetupProcedureHandler(unittest.TestCase):

    def setUp(self):
        self.mmeIoService = IoService("mme", 9000)
        self.mmeIoService.start()
        self.mmeParameters = {
            "mmeName": "Istanbul",
            "servedGummeis": [
                (("28603", "28604"), (0, 1, 2), (23, 58, 127)),
                (("00108"), (0,), (12, 13, 14)),
            ],
            "timeToWait": 1,
            "flags": {
                "rejectS1SetupRequestsFromRegisteredEnbs": True
            },
            "criticalityDiagnostics": None,
        }
        self.enbProcedureParameters = lambda globalEnbId, enbName, tac: {
            "globalEnbId": globalEnbId,
            "enbName": enbName,
            "supportedTas": [
                (tac, ("28603", "28604")),
            ],
            "csgIdList": [],
            "defaultPagingDrx": [32, 64, 128],
        }
        self.numEnbs = 2
        self.enbIoServices = [IoService("enb{}".format(i), 9001 + i) for i in range(self.numEnbs)]
        self.enbProcedures = [
            EnbS1SetupProcedure(self.enbProcedureParameters(i, "enb{}".format(i), 59900 + i),
                (localhost(), 9000), s, self.__enbS1SetupProcedureProgressCallback__)
            for i, s in enumerate(self.enbIoServices)]
        [s.start() for s in self.enbIoServices]
        self.numSuccess, self.numWaitingForNextAttempt = 0, 0

    def tearDown(self):
        self.mmeProcedureHandler.terminate()
        self.mmeIoService.stop()
        [p.terminate() for p in self.enbProcedures]
        [s.stop() for s in self.enbIoServices]
        
    def __enbS1SetupProcedureProgressCallback__(self, progress, args=None):
        if progress == EnbS1SetupProcedure.ProgressSuccess:
            self.numSuccess += 1
        elif progress == EnbS1SetupProcedure.ProgressWaitForNextAttempt:
            self.numWaitingForNextAttempt += 1
    
    def __mmeOnEnbRegisteredCallback__(self, globalEnbId):
        self.enbPool.add(globalEnbId)

    def test_AllSuccessfulS1Setups(self):
        self.enbPool = MmeServiceArea(self.numEnbs)
        self.mmeProcedureHandler = MmeS1SetupProcedureHandler(self.mmeParameters, self.enbPool, self.mmeIoService,
            self.__mmeOnEnbRegisteredCallback__)
        self.mmeIoService.addIncomingMessageCallback(self.mmeProcedureHandler.handleIncomingS1SetupMessage)
        self.mmeProcedureHandler.execute()
        [p.execute() for p in self.enbProcedures]
        time.sleep(0.9)
        self.assertEqual(self.numSuccess, self.numEnbs)
        self.assertEqual(len(self.enbPool), self.numEnbs)

    def test_AllSuccessfulS1SetupsExceptOne(self):
        self.enbPool = MmeServiceArea(self.numEnbs)
        self.mmeProcedureHandler = MmeS1SetupProcedureHandler(self.mmeParameters, self.enbPool, self.mmeIoService,
            self.__mmeOnEnbRegisteredCallback__)
        self.mmeIoService.addIncomingMessageCallback(self.mmeProcedureHandler.handleIncomingS1SetupMessage)
        self.mmeProcedureHandler.execute()
        [p.execute() for p in self.enbProcedures]
        time.sleep(0.9)
        self.assertEqual(self.numSuccess, self.numEnbs - 1)
        self.assertEqual(self.numWaitingForNextAttempt, 1)
        self.assertEqual(len(self.enbPool), self.numEnbs - 1)