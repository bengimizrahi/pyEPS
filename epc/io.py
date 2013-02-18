import threading
from Queue import Queue
import socket
import time
import logging

from .utils.message import verify

msgTraceLogger = logging.getLogger("msgTrace")
assertionLogger = logging.getLogger("assertions")

class IoService(object):
    
    def __init__(self, name, udpPort, incomingMessageCallback=None):
        self.name = name
        self.udpPort = udpPort
        self.eventQueue = Queue()
        self.alive = False
        self.incomingMessageCallback = incomingMessageCallback
        self.timers = {}
    
    def setIncomingMessageCallback(self, callback):
        self.incomingMessageCallback = callback
    
    def start(self):
        if not self.incomingMessageCallback:
            raise Exception("No incoming message callback is set")
        self.ioHandlerThread = threading.Thread(target=self.ioHandlerThreadFunc)
        self.callbackHandlerThread = threading.Thread(target=self.callbackHandlerThreadFunc)
        self.alive = True
        [t.start() for t in (self.ioHandlerThread, self.callbackHandlerThread)]

    def stop(self):
        if not self.alive:
            raise RuntimeError("Thread not started")
        self.alive = False
        self.eventQueue.put(("STOP", None))
        [t.join() for t in (self.ioHandlerThread, self.callbackHandlerThread)]
    
    def startTimer(self, name, duration, callback):
        if not self.alive:
            raise RuntimeError("Thread not started")
        if self.timers.get(name):
            raise Exception("A running timer present for '{}'".format(name))
        timerContext = (threading.Timer(duration, self.onTimerExpiration, args=[name]), callback)
        timerContext[0].start()
        self.timers[name] = timerContext
    
    def cancelTimer(self, name):
        if not self.alive:
            raise RuntimeError("Thread not started")
        if not self.timers.get(name):
            raise Exception("No running timer named '{}' found".format(name))
        self.timers[name][0].cancel()
        del self.timers[name]
    
    def onTimerExpiration(self, name):
        timerContext = self.timers[name]
        self.eventQueue.put(("TIMEOUT", timerContext[1]))
        del self.timers[name]
    
    def sendMessage(self, destination, via, protocol, message):
        if not self.alive:
            raise RuntimeError("Thread not started")
        def snd(message, addr):
            packet = {
                "source": self.name,
                "via": via,
                "protocol": protocol,
                "message": message,
            }
            successful = self.sock.sendto(str(packet), addr) != -1
            return successful
        if isinstance(destination, tuple):
            return snd(message, destination)
        elif isinstance(destination, str):
            peerAddr = self.peers.get(destination)
            if not peerAddr:
                raise Exception("No peer found associated with '{}', ignoring message...".format(destination))
            else:
                return snd(message, peerAddr)

    def ioHandlerThreadFunc(self):
        self.peers = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.settimeout(0.1)
        self.sock.bind(("0", self.udpPort))
        while self.alive:
            try:
                msg, addr = self.sock.recvfrom(2048)
            except socket.timeout:
                continue
            try:
                packet = eval(msg)
            except SyntaxError:
                assertionLogger.error("eval({}) raised SyntaxError, ignoring message...".format(msg))
                continue
            msgTraceLogger.info("Incoming packet: {}".format(packet))
            source = packet["source"]
            if not self.peers.get(source):
                self.peers[source] = addr
            self.eventQueue.put(("PACKET", packet))
        self.sock.close()
    
    def callbackHandlerThreadFunc(self):
        while self.alive:
            event, param = self.eventQueue.get()
            if event == "STOP":
                break
            elif event == "PACKET":
                packet = param
                self.incomingMessageCallback(packet["source"], packet["via"], packet["protocol"], packet["message"])
            elif event == "TIMEOUT":
                timerExpirationCallback = param
                timerExpirationCallback()
        [t.cancel() for t, _ in self.timers.values()]
