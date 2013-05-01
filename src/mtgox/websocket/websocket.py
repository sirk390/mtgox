import traceback

from mtgox.websocket.keys import WebSocketKeys
from mtgox.websocket.handshake import HandshakeRequestFormater,\
    HandshakeResponseParser, HandshakeResponseIncomplete,\
    WebSocketHandshakeRequest
from mtgox.websocket.frames import read_frames
from mtgox.event import Event
from mtgox.websocket.sslconnection import SSLConnection
from mtgox.logger import log

            
class WebSocket(SSLConnection):
    def __init__(self, hostname, port, resource):
        SSLConnection.__init__(self)
        self.keys = WebSocketKeys()
        self.header_data = ""
        self.read_buffer = ""
        self.out_buffer = ''
        #synchroneous ssl connection 
        self.connect((hostname, port))
        request = WebSocketHandshakeRequest(resource, hostname, port, self.keys.key1, self.keys.key2, self.keys.key3)
        self.send(HandshakeRequestFormater.format(request))
        self.EVENT_HANDSHAKE_COMPLETED = Event()
        self.EVENT_FRAME = Event()
        self.EVENT_DISCONNECTED = Event()
        self.handshake_completed = False
        
    def initiate_send(self):
        num_sent = SSLConnection.send(self, self.out_buffer[:512])
        self.out_buffer = self.out_buffer[num_sent:]

    def handle_write(self):
        self.initiate_send()

    def writable(self):
        return (not self.connected) or len(self.out_buffer)
 
    def readable(self):
        return True

    def send(self, data):
        self.out_buffer = self.out_buffer + data

    def send_message(self, data):
        log.debug("send_message" + data)
        self.send('\x00' + data + '\xff')
        
    def handle_close(self):
        log.debug("handle_close2")
        self.EVENT_DISCONNECTED.fire()
        self.close()
        
    def handle_error(self):
        traceback.print_exc()
        
    def handle_read(self):
        self.read_buffer += self.recv(81920000)
        self.process_readbuffer()

    def process_readbuffer(self):
        if not self.handshake_completed:
            try:
                response, self.read_buffer = HandshakeResponseParser.parse(self.read_buffer)
                self.handshake_completed = True
                self.EVENT_HANDSHAKE_COMPLETED.fire()
            except HandshakeResponseIncomplete:
                pass
        if self.handshake_completed and self.read_buffer:
            frames, self.read_buffer = read_frames(self.read_buffer)
            for frame in frames:
                self.EVENT_FRAME.fire(frame=frame)

if __name__ == "__main__":
    pass
