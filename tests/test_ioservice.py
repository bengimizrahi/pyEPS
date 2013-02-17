import unittest
import time

from epc.io import IoService


class Test_1_IoServiceAssertions(unittest.TestCase):
    
    def setUp(self):
        self.ioservice = IoService("service", 9000)
    
    def test_1_funcStart(self):
        with self.assertRaises(Exception):
            self.ioservice.start()
    
    def test_2_funcStop(self):
        with self.assertRaises(RuntimeError):
            self.ioservice.stop()
    
    def test_3_funcStartTimer(self):
        with self.assertRaises(RuntimeError):
            self.ioservice.startTimer("foo", 1.0, lambda: None)
    
    def test_4_funcCancelTimer(self):
        with self.assertRaises(RuntimeError):
            self.ioservice.cancelTimer("foo")
    
    def test_5_funcSendMessage(self):
        with self.assertRaises(RuntimeError):
            self.ioservice.sendMessage(("", 9000), "via", "protocol", {"key": "value"})

    def tearDown(self):
        pass


class Test_2_IoServiceTimers(unittest.TestCase):
    
    def setUp(self):
        self.ioservice = IoService("timer", 9000, lambda s, v, p, m: None)
        self.ioservice.start()
        
    def test_1_useTimer(self):
        def onSuccess():
            self.successful = True
        self.successful = False
        self.ioservice.startTimer("foo", 0.1, onSuccess)
        time.sleep(0.2)
        self.assertTrue(self.successful)
    
    def test_2_cancelTimer(self):
        def onExpiration():
            self.expired = True
        self.expired = False
        self.ioservice.startTimer("foo", 0.2, onExpiration)
        time.sleep(0.1)
        self.ioservice.cancelTimer("foo")
        time.sleep(0.2)
        self.assertFalse(self.expired)

    def tearDown(self):
        self.ioservice.stop()


class Test_3_IoService(unittest.TestCase):

    def setUp(self):
        self.ioservices = [IoService(str(i), 9000 + i) for i in range(2)] 

    def test_1_basicMessaging(self):
        msg0to1 = {
            "content": "Anyone there?",
        }
        msg1to0 = {
            "content": "Yes, there is!",
        }
        def onIncomingMessage0(source, via, protocol, message):
            self.assertEqual(message, msg1to0)
            self.successful = True
        def onIncomingMessage1(source, via, protocol, message):
            self.assertEqual(message, msg0to1)
            self.assertTrue(self.ioservices[1].sendMessage("0", "river", "bottle", msg1to0))
        self.successful = False
        self.ioservices[0].setIncomingMessageCallback(onIncomingMessage0)
        self.ioservices[1].setIncomingMessageCallback(onIncomingMessage1)
        [s.start() for s in self.ioservices]
        self.assertTrue(self.ioservices[0].sendMessage(("", 9001), "air", "smoke", msg0to1))
        time.sleep(0.1)
        self.assertTrue(self.successful)
    
    def test_2_broadcastMessaging(self):
        msgToAll = {
            "content": "Heeeelp!",
        }
        def onIncomingMessage(source, via, protocol, message):
            self.assertEqual(msgToAll, message)
            self.successful = True
        self.successful = False
        self.ioservices[0].setIncomingMessageCallback(lambda s, v, p, m: None)
        self.ioservices[1].setIncomingMessageCallback(onIncomingMessage)
        [s.start() for s in self.ioservices]
        self.assertTrue(self.ioservices[0].sendMessage(("255.255.255.255", 9001), "sound-waves", "english", msgToAll))
        time.sleep(0.1)
        self.assertTrue(self.successful)
    
    def test_3_paging(self):
        msgToAll = {
            "type": "paging-request",
            "id": "1",
        }
        def onIncomingMessage(source, via, protocol, message):
            self.assertEqual(message["id"], "1")
            self.successful = True
        self.successful = False
        self.ioservices[0].setIncomingMessageCallback(lambda s, p, v, m: None)
        self.ioservices[1].setIncomingMessageCallback(onIncomingMessage)
        [s.start() for s in self.ioservices]
        for p in range(9001, 9100):
            self.assertTrue(self.ioservices[0].sendMessage(("", p), "pch", None, msgToAll))
        time.sleep(0.1)
        self.assertTrue(self.successful)
    
    def test_4_noPeerFound(self):
        with self.assertRaises(Exception):
            self.ioservices[0].setIncomingMessageCallback(lambda s, p, v, m: None)
            self.ioservices[1].setIncomingMessageCallback(lambda s, p, v, m: None)
            [s.start() for s in self.ioservices]
            self.ioservices[0].sendMessage(("1", "via", "protocol", {"key": "value"}))
    def tearDown(self):
        [s.stop() for s in self.ioservices]

if __name__ == '__main__':
    unittest.main()

