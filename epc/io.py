from threading import Thread
from Queue import Queue
import socket
import time
import logging

from .utils.message import verify

msgTraceLogger = logging.getLogger("msgTrace")
assertionLogger = logging.getLogger("assertions")

class IoService(Thread):
    
    def __init__(self, udpPort, incomingMessageQueue=None):
        super(IoService, self).__init__()
        self.udpPort = udpPort
        self.incomingMessageOutputQueue = incomingMessageQueue or Queue()
        self.alive = False
        self.peers = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(0)
        self.sock.bind(("0", self.udpPort))
    
    def sendMessage(self, message, destination=None, addr=None):
        def snd(message, addr):
            successful = self.sock.sendto(str(message), addr) != -1
            return successful
        if (not destination) and (not addr):
            assertionLogger.error("Neither 'destination' nor 'addr' is provided, returning False...")
            return False
        if not verify(message):
            assertionLogger.error("Verification of the message {} failed, ignoring message...".format(message))
            return False
        if (not destination) and addr:
            return snd(message, addr)
        elif destination:
            peerAddr = self.peers.get(destination)
            if not peerAddr:
                assertionLogger.error("No peer found associated with '{}', ignoring message...".format(destination))
                return False
            else:
                return snd(message, peerAddr)

    def getIncomingMessageQueue(self):
        return self.incomingMessageOutputQueue

    def run(self):
        self.alive = True
        while self.alive:
            try:
                msg, addr = self.sock.recvfrom(2048)
            except socket.error:
                time.sleep(0.1)
                continue
            try:
                message = eval(msg)
            except SyntaxError:
                assertionLogger.error("eval({}) raised SyntaxError, ignoring message...".format(msg))
                continue
            if not verify(message):
                assertionLogger.error("Verification of the message {} failed, ignoring message...".format(message))
            msgTraceLogger.info("Incoming message: source({source}), via({via}), protocol({protocol}), message({payload})".format(**message))
            source = message["source"]
            if not self.peers.get(source):
                self.peers[source] = addr
            self.incomingMessageOutputQueue.put(message)
        self.sock.close()
        
    def stop(self):
        self.alive = False
