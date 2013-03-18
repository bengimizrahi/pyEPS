import threading
from Queue import Queue
import socket
import logging
import sys


msgTraceLogger = logging.getLogger("msgTrace")
assertionLogger = logging.getLogger("assertions")

def localhost():
    return {
        "linux2": "0.0.0.0",
        "darwin": "0.0.0.0",
        "win32": "127.0.0.1",}.get(sys.platform, "0.0.0.0")


class IoService(object):
    
    def __init__(self, name, udpPort):
        self.name = name
        self.udpPort = udpPort
        self.eventQueue = Queue()
        self.alive, self.stopped = False, False
        self.incomingMessageCallback = []
        self.timers = {}

    def __repr__(self):
        return "{}({}, {}, alive={}, stopped={})".format(
            self.__class__.__name__, self.name, self.udpPort, self.alive, self.stopped)

    def addIncomingMessageCallback(self, callback):
        self.incomingMessageCallback.append(callback)
    
    def removeIncomingMessageCallback(self, callback):
        self.incomingMessageCallback.remove(callback)
    
    def start(self):
        self.ioHandlerThread = threading.Thread(target=self.__ioHandlerThreadFunc__)
        self.callbackHandlerThread = threading.Thread(target=self.__callbackHandlerThreadFunc__)
        self.alive = True
        [t.start() for t in (self.ioHandlerThread, self.callbackHandlerThread)]

    def stop(self):
        if self.stopped:
            raise RuntimeError("{} already stopped".format(self))
        if not self.alive:
            raise RuntimeError("{} not started".format(self))
        self.alive, self.stopped = False, True
        self.eventQueue.put(("STOP", None))
        [t.join() for t in (self.ioHandlerThread, self.callbackHandlerThread)]
    
    def createTimer(self, duration, callback, *args, **kwargs):
        if self.stopped:
            raise RuntimeError("{} already stopped".format(self))
        if not self.alive:
            raise RuntimeError("{} not started".format(self))
        return threading.Timer(duration, self.__onTimerExpiration__, args=[callback, args, kwargs])
    
    def __onTimerExpiration__(self, callback, args, kwargs):
        self.eventQueue.put(("TIMEOUT", (callback, args, kwargs)))
    
    def onConfigValueChanged(self, callback, path, value):
        self.eventQueue.put(("CONFIG", (callback, path, value)))

    def sendMessage(self, destination, interface, channelInfo, message):
        if self.stopped:
            raise RuntimeError("{} already stopped".format(self))
        if not self.alive:
            raise RuntimeError("{} not started".format(self))
        def snd(message, addr):
            packet = {
                "source": self.name,
                "interface": interface,
                "channelInfo": channelInfo,
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

    def __ioHandlerThreadFunc__(self):
        self.peers = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.settimeout(0.1)
        self.sock.bind((localhost(), self.udpPort))
        while self.alive:
            try:
                msg, addr = self.sock.recvfrom(2048)
            except socket.timeout:
                continue
            except socket.error:
                continue
            try:
                packet = eval(msg)
            except SyntaxError:
                assertionLogger.error("eval({}) raised SyntaxError, ignoring message...".format(msg))
                continue
            msgTraceLogger.info("Incoming packet to IoService({}, {}): {}".format(self.name, self.udpPort, packet))
            source = packet["source"]
            if not self.peers.get(source):
                self.peers[source] = addr
            self.eventQueue.put(("PACKET", packet))
        self.sock.close()
    
    def __callbackHandlerThreadFunc__(self):
        while self.alive:
            event, param = self.eventQueue.get()
            if event == "STOP":
                break
            elif event == "PACKET":
                packet = param
                for cb in self.incomingMessageCallback:
                    cb(packet["source"], packet["interface"], packet["channelInfo"], packet["message"])
            elif event == "TIMEOUT":
                timerExpirationCallback, args, kwargs = param
                timerExpirationCallback(*args, **kwargs)
            elif event == "CONFIG":
                valueChangedCallback, key, value = param
                valueChangedCallback(key, value)
