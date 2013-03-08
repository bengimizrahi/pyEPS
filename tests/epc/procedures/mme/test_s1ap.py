import unittest
import time

from epc.utils.io import IoService, localhost
from epc.procedures.enb.s1ap import S1SetupProcedure as EnbS1SetupProcedure
from epc.procedures.mme.s1ap import S1SetupProcedureHandler as MmeS1SetupProcedureHandler


class TestS1SetupProcedureHandler(unittest.TestCase):

    def setUp(self):
        self.mmeIoService = IoService("mme", (localhost(), 9000))
        self.mmeIoService.start()
        self.enbPoolInsideMme = {}
        self.mmeParameters = lambda maxNumEnbsServed: {
            "mmeName": "Istanbul",
            "servedGummeis": [
                (("28603", "28604"), (0, 1, 2), (23, 58, 127)),
                (("00108"), (0,), (12, 13, 14)),
            ],
            "maxNumEnbsServed": maxNumEnbsServed,
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
        self.enbIoServices = [IoService("enb{}".format(i), (localhost(), 9001 + i)) for i in range(self.numEnbs)]
        self.enbProcedures = [
            EnbS1SetupProcedure(self.enbProcedureParameters(i, "enb{}".format(i)), (localhost(), 9000),
                s, self.__procedureProgressCallback__) for i, s in enumerate(self.enbIoServices)
        ]
        [s.start() for s in self.enbIoServices]
        self.numEnbs = 100
        self.numSuccess, self.numFail = 0, 0

    def tearDown(self):
        self.mmeIoService.stop()
        
    def __procedureProgressCallback__(self, progress, args=None):
        if progress == EnbS1SetupProcedure.ProgressSuccess:
            self.numSuccess += 1
        elif progress == EnbS1SetupProcedure.ProgressFailedWithCauseUnspecified:
            self.numFail += 1
    
    def test_100SuccessfulS1Setups(self):
        self.mmeProcedureHandler = MmeS1SetupProcedureHandler(self.mmeParameters(100), self.enbPoolInsideMme, self.mmeIoService)
        self.mmeIoService.addIncomingMessageCallback(self.mmeProcedureHandler.handleIncomingS1SetupMessage)
        self.mmeProcedureHandler.execute()
        [p.execute() for p in self.enbProcedures]
        time.sleep(1)
        self.assertEqual(self.numSuccess, self.numEnbs)

    def test_90Successful10RejectedS1Setups(self):
        self.mmeProcedureHandler = MmeS1SetupProcedureHandler(self.mmeParameters(90), self.enbPoolInsideMme, self.mmeIoService)
        self.mmeIoService.addIncomingMessageCallback(self.mmeProcedureHandler.handleIncomingS1SetupMessage)
        self.mmeProcedureHandler.execute()
        [p.execute() for p in self.enbProcedures]
        time.sleep(1)
        self.assertTupleEqual((self.numSuccess, self.numFail), (90, 10))
