import unittest
import time

from epc.utils.io import IoService, localhost


class TestIoServiceAssertions(unittest.TestCase):
    
    def setUp(self):
        self.ioservice = IoService("service", 9000)
    
    def test_funcStop(self):
        with self.assertRaises(RuntimeError):
            self.ioservice.stop()
    
    def test_funcStartTimer(self):
        with self.assertRaises(RuntimeError):
            foo = self.ioservice.createTimer(1.0, lambda: None)
            foo.start()
    
    def test_funcSendMessage(self):
        with self.assertRaises(RuntimeError):
            self.ioservice.sendMessage((localhost(), 9000), "interface", "channelInfo", {"key": "value"})


class TestIoServiceTimers(unittest.TestCase):
    
    def setUp(self):
        self.ioservice = IoService("timer", 9000)
        self.ioservice.start()

    def test_startTimer(self):
        def onSuccess():
            self.successful = True
        self.successful = False
        foo = self.ioservice.createTimer(0.1, onSuccess)
        foo.start()
        time.sleep(0.2)
        self.assertTrue(self.successful)
        
    def test_startTimerWithArguments(self):
        def onSuccess(*args, **kwargs):
            self.assertEqual(args, (1, 2, 3))
            self.assertEqual(kwargs, {"kwargOne": 4, "kwargTwo": 5, "kwargThree": 6})
            self.successful = True
        self.successful = False
        foo = self.ioservice.createTimer(0.1, onSuccess, 1, 2, 3, kwargOne=4, kwargTwo=5, kwargThree=6)
        foo.start()
        time.sleep(0.2)
        self.assertTrue(self.successful)
    
    def test_cancelTimer(self):
        def onExpiration():
            self.expired = True
        self.expired = False
        foo = self.ioservice.createTimer(0.2, onExpiration)
        foo.start()
        time.sleep(0.1)
        foo.cancel()
        time.sleep(0.2)
        self.assertFalse(self.expired)

    def test_restartTimer(self):
        def onExpiration():
            self.count += 1
            if self.count < 2:
                foo = self.ioservice.createTimer(0.05, onExpiration)
                foo.start()
        self.count = 0
        foo = self.ioservice.createTimer(0.05, onExpiration)
        foo.start()
        time.sleep(0.2)
        self.assertEqual(self.count, 2)

    def test_restartCanceledTimer(self):
        def onExpiration():
            self.successful = True
        foo = self.ioservice.createTimer(0.1, onExpiration)
        foo.start()
        time.sleep(0.05)
        foo.cancel()
        foo = self.ioservice.createTimer(0.1, onExpiration)
        foo.start()
        time.sleep(0.2)
        self.assertTrue(self.successful)

    def tearDown(self):
        self.ioservice.stop()


class TestIoService(unittest.TestCase):

    def setUp(self):
        self.ioservices = [IoService(str(i), 9000 + i) for i in range(2)] 

    def test_basicMessaging(self):
        msg0to1 = {
            "content": "Anyone there?",
        }
        msg1to0 = {
            "content": "Yes, there is!",
        }
        def onIncomingMessage0(source, interface, channelInfo, message):
            self.assertEqual(message, msg1to0)
            self.successful = True
        def onIncomingMessage1(source, interface, channelInfo, message):
            self.assertEqual(message, msg0to1)
            self.assertTrue(self.ioservices[1].sendMessage("0", "river", "bottle", msg1to0))
        self.successful = False
        self.ioservices[0].addIncomingMessageCallback(onIncomingMessage0)
        self.ioservices[1].addIncomingMessageCallback(onIncomingMessage1)
        [s.start() for s in self.ioservices]
        self.assertTrue(self.ioservices[0].sendMessage((localhost(), 9001), "air", "smoke", msg0to1))
        time.sleep(0.1)
        self.assertTrue(self.successful)
    
    def test_broadcastMessaging(self):
        msgToAll = {
            "content": "Heeeelp!",
        }
        def onIncomingMessage(source, interface, channelInfo, message):
            self.assertEqual(msgToAll, message)
            self.successful = True
        self.successful = False
        self.ioservices[1].addIncomingMessageCallback(onIncomingMessage)
        [s.start() for s in self.ioservices]
        self.assertTrue(self.ioservices[0].sendMessage(("255.255.255.255", 9001), "sound-waves", "english", msgToAll))
        time.sleep(0.1)
        self.assertTrue(self.successful)
    
    def test_paging(self):
        msgToAll = {
            "type": "paging-request",
            "id": "1",
        }
        def onIncomingMessage(source, interface, channelInfo, message):
            self.assertEqual(message["id"], "1")
            self.successful = True
        self.successful = False
        self.ioservices[1].addIncomingMessageCallback(onIncomingMessage)
        [s.start() for s in self.ioservices]
        for p in range(9001, 9100):
            self.assertTrue(self.ioservices[0].sendMessage((localhost(), p), "pch", None, msgToAll))
        time.sleep(0.1)
        self.assertTrue(self.successful)
    
    def test_noPeerFound(self):
        with self.assertRaises(Exception):
            [s.start() for s in self.ioservices]
            self.ioservices[0].sendMessage(("1", "interface", "channelInfo", {"key": "value"}))

    def tearDown(self):
        [s.stop() for s in self.ioservices]

class TestBulkMessages(unittest.TestCase):

    def setUp(self):
        self.ioservices = [IoService(str(i), 9000 + i) for i in range(2)]
        [s.start() for s in self.ioservices]
        self.numSuccess = 0

    def tearDown(self):
        [s.stop() for s in self.ioservices]

    def test_bulkMessages(self):
        def onIncomingMessage0(source, interface, channelInfo, message):
            self.numSuccess += 1

        def onIncomingMessage1(source, interface, channelInfo, message):
            self.ioservices[1].sendMessage("0", interface, channelInfo, message)

        n = 1000
        [s.addIncomingMessageCallback(cb) for s, cb in zip(self.ioservices, (onIncomingMessage0, onIncomingMessage1))]
        for _ in range(n):
            self.ioservices[0].sendMessage((localhost(), 9001), "udp", None, {"someKey": "someValue"})
        time.sleep(1.0)
        self.assertEqual(self.numSuccess, n)


if __name__ == '__main__':
    unittest.main()

