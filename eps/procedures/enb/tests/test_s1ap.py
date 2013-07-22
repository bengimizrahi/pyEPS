import unittest
import time

from eps.utils.io import IoService, localhost
from eps.procedures.enb.s1ap import S1SetupProcedure
from eps.messages.s1ap import s1SetupResponse, s1SetupFailure


class TestS1apSetupProcedureInitiation(unittest.TestCase):

    def setUp(self):
        self.enbIoService = IoService("enb", 9001)
        self.mmeIoService = IoService("mme", 9000)
        [s.start() for s in self.enbIoService, self.mmeIoService]

    def tearDown(self):
        [s.stop() for s in self.enbIoService, self.mmeIoService]

    def __procedureProgressCallback__(self, progress, args):
        self.progress = progress
        self.args = args

    def test_missingS1SetupRequestParameters(self):
        with self.assertRaises(Exception):
            self.procedure = S1SetupProcedure({}, (localhost(), 9000),
                self.enbIoService, self.__procedureProgressCallback__)
            self.enbIoService.addIncomingMessageCallback(self.procedure.handleIncomingMessage)
            self.procedure.execute()
            self.procedure.terminate()


class TestS1apSetupProcedure(unittest.TestCase):

    def setUp(self):
        self.sampleS1SetupRequestParameters = {
            "globalEnbId": 345,
            "enbName": "Taksim",
            "supportedTas": [
                (41433, ("28603", "28604")),
                (41434, ("28603", "28604")),
            ],
            "csgIdList": [101, 122],
            "defaultPagingDrx": [32, 64, 128],
        }
        self.sampleS1SetupResponseParameters = {
            "mmeName": "Istanbul",
            "servedGummeis": [
                (("28603", "28604"), (0, 1, 2), (23, 58, 127)),
                (("00108"), (0,), (12, 13, 14)),
            ],
            "relativeMmeCapacity": 255,
            "criticalityDiagnostics": None,
        }
        self.enbIoService = IoService("enb", 9001)
        self.mmeIoService = IoService("mme", 9000)
        [s.start() for s in self.enbIoService, self.mmeIoService]
        self.procedure = S1SetupProcedure(self.sampleS1SetupRequestParameters,
            (localhost(), 9000), self.enbIoService, self.__procedureProgressCallback__)
        self.enbIoService.addIncomingMessageCallback(self.procedure.handleIncomingMessage)
        self.progress = None
        self.args = None

    def tearDown(self):
        [s.stop() for s in self.enbIoService, self.mmeIoService]

    def __procedureProgressCallback__(self, progress, args=None):
        self.progress = progress
        self.args = args

    def test_procedureSuccessful(self):
        self.procedure.execute()
        time.sleep(0.1)
        self.mmeIoService.sendMessage("enb", *s1SetupResponse(**self.sampleS1SetupResponseParameters))
        time.sleep(0.1)
        self.assertEqual(self.progress, S1SetupProcedure.ProgressSuccess)
        self.procedure.terminate()

    def test_procedureFirstRejectedThenSuccessful(self):
        self.procedure.execute()
        time.sleep(0.2)
        self.mmeIoService.sendMessage("enb", *s1SetupFailure(**{
            "cause": "congestion",
            "timeToWait": 1,
            "criticalityDiagnostics": None,
        }))
        time.sleep(0.1)
        self.assertEqual(self.progress, S1SetupProcedure.ProgressWaitForNextAttempt)
        time.sleep(1.1) # greater than value of 'Time to wait' IE
        self.mmeIoService.sendMessage("enb", *s1SetupResponse(**self.sampleS1SetupResponseParameters))
        time.sleep(0.1)
        self.assertEqual(self.progress, S1SetupProcedure.ProgressSuccess)
        self.procedure.terminate()
