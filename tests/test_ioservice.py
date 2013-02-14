import unittest

from epc.io import IoService

class TestIoService(unittest.TestCase):

    def setUp(self):
        PORT_MIN = 19040
        self.ports = [PORT_MIN+i for i in range(2)]
        self.ioservices = [IoService(p) for p in self.ports]
        [s.start() for s in self.ioservices]

    def test_basicMessaging(self):
        msg1to2 = {
            "source": "1",
            "via": "air",
            "protocol": "smoke",
            "payload": {"type": "text-baloon", "content": "Anyone there?"}
        }
        assert self.ioservices[0].sendMessage(msg1to2, None, ("0", self.ports[1]))
        msg1to2Prime = self.ioservices[1].getIncomingMessageQueue().get()
        assert msg1to2 == msg1to2Prime
        msg2to1 = {
            "source": "2",
            "via": "river",
            "protocol": "bottle",
            "payload": {"type": "paper-text", "content": "Yes, there is!"}
        }
        assert self.ioservices[1].sendMessage(msg2to1, "1")
        msg2to1Prime = self.ioservices[0].getIncomingMessageQueue().get()
        assert msg2to1 == msg2to1Prime
    
    def test_broadcastMessaging(self):
        msgToAll = {
            "source": "someone",
            "via": "sound-waves",
            "protocol": "english",
            "payload": {"type": "question", "content": "Heeeelp!"}
        }
        self.assertTrue(self.ioservices[0].sendMessage(msgToAll, None, ("255.255.255.255", self.ports[1])))
        msgToAllPrime = self.ioservices[1].getIncomingMessageQueue().get()
        self.assertEqual(msgToAll, msgToAllPrime)
    
    def tearDown(self):
        [s.stop() for s in self.ioservices]

if __name__ == '__main__':
    unittest.main()

