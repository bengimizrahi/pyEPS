import unittest
import threading

from epc.io import IoService

def notifyAfterCompletion(condition):
    def newdec(f):
        def newf(*args, **kwargs):
            condition.acquire()
            retval = f(*args, **kwargs)
            condition.notify()
            condition.release()
            return retval
        return newf
    return newdec


class Test_1_IoServiceAssertions(unittest.TestCase):
    
    def setUp(self):
        self.ioservice = IoService(9000)
    
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
            self.ioservice.sendMessage({"message": "hello"}, None, ("", 9000))

    def tearDown(self):
        pass


class Test_3_IoService(unittest.TestCase):

    NUM_IOSERVICES = 2
    PORT_MIN = 9000
    
    def setUp(self):
        self.ports = [self.PORT_MIN+i for i in range(self.NUM_IOSERVICES)]
        self.ioservices = [IoService(p) for p in self.ports]
        self.cond = threading.Condition()

    def test_1_basicMessaging(self):
        msg1to2 = {
            "source": "1",
            "via": "air",
            "protocol": "smoke",
            "payload": {"type": "text-baloon", "content": "Anyone there?"}
        }
        msg2to1 = {
            "source": "2",
            "via": "river",
            "protocol": "bottle",
            "payload": {"type": "paper-text", "content": "Yes, there is!"}
        }
        @notifyAfterCompletion(self.cond)
        def onIncomingMessage0(message):
            self.assertEqual(message, msg2to1)
        def onIncomingMessage1(message):
            self.assertEqual(message, msg1to2)
            self.assertTrue(self.ioservices[1].sendMessage(msg2to1, "1"))
        self.ioservices[0].setIncomingMessageCallback(onIncomingMessage0)
        self.ioservices[1].setIncomingMessageCallback(onIncomingMessage1)
        [s.start() for s in self.ioservices]
        self.cond.acquire()
        self.assertTrue(self.ioservices[0].sendMessage(msg1to2, None, ("0", self.ports[1])))
        self.cond.wait()
    
    def test_2_broadcastMessaging(self):
        msgToAll = {
            "source": "someone",
            "via": "sound-waves",
            "protocol": "english",
            "payload": {"type": "question", "content": "Heeeelp!"}
        }
        @notifyAfterCompletion(self.cond)
        def onIncomingMessage(message):
            self.ioservices[0].cancelTimer("broadcastResponseTimer")
            self.assertEqual(msgToAll, message)
        @notifyAfterCompletion(self.cond)
        def onBroadcastResponseTimeout():
            self.fail("No response received")
        self.ioservices[0].setIncomingMessageCallback(lambda m: None)
        self.ioservices[1].setIncomingMessageCallback(onIncomingMessage)
        [s.start() for s in self.ioservices]
        self.cond.acquire()
        self.ioservices[0].startTimer("broadcastResponseTimer", 1, onBroadcastResponseTimeout)
        self.assertTrue(self.ioservices[0].sendMessage(msgToAll, None, ("255.255.255.255", self.ports[1])))
        self.cond.wait()
    
    def test_3_paging(self):
        msgToAll = {
            "source": "enb",
            "via": "pch",
            "payload": {"type": "paging-request", "id": "ue1"}
        }
        @notifyAfterCompletion(self.cond)
        def onIncomingMessage(message):
            self.ioservices[0].cancelTimer("broadcastResponseTimer")
            self.assertEqual(message["payload"]["id"], "ue1")
        @notifyAfterCompletion(self.cond)
        def onBroadcastResponseTimeout():
            self.fail("No response received")
        self.ioservices[0].setIncomingMessageCallback(lambda m: None)
        self.ioservices[1].setIncomingMessageCallback(onIncomingMessage)
        [s.start() for s in self.ioservices]
        self.cond.acquire()
        for p in range(self.PORT_MIN, self.PORT_MIN+100):
            self.assertTrue(self.ioservices[0].sendMessage(msgToAll, None, ("", p)))
        self.ioservices[0].startTimer("broadcastResponseTimer", 1, onBroadcastResponseTimeout)
        self.cond.wait()
    
    def tearDown(self):
        [s.stop() for s in self.ioservices]

if __name__ == '__main__':
    unittest.main()

