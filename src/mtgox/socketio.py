from threading import Thread
from mtgox.event import Event
import urllib
import urllib2
import re
import time
from mtgox.websocket.websocket import WebSocket
import traceback
from mtgox.logger import log

class SocketIO:
    """ SocketIO implementation ( websocket Transport ) 
    
        spec : https://github.com/LearnBoost/socket.io-spec
    """
    MSG_DISCONNECTED = "0"
    MSG_CONNECTED = "1"
    MSG_HEARTBEAT = "2"
    MSG_MESSAGE = "3"
    MSG_JSON_MESSAGE = "4"
    MSG_EVENT = "5"
    MSG_ACK = "6"
    MSG_ERROR = "7"
    MSG_NOP = "8"

    CONNECTED, CONNECTING, DISCONNECTED, DISCONNECTING = STATES = range(4)
    RECONNECT_INTERVAL = 5 #seconds
    def __init__(self, host, namespace, protocol_version, params):
        self.host = host # socketio.mtgox.com
        self.namespace = namespace # socket.io
        self.protocol_version = protocol_version # 1
        self.params = params
        self.shuttingdown = False
        self.keep_alive_thread = Thread(target = self.keep_alive)
        self.keep_alive_thread.daemon = True
        self.state = SocketIO.DISCONNECTED#
        self.EVENT_CONNECTED_SOCKETIO = Event()
        self.EVENT_CONNECTED_ENDPOINT = Event()
        self.EVENT_JSON_MESSAGE = Event()
        self.EVENT_DISCONNECTED_SOCKETIO = Event()
        
    def start(self):
        self.keep_alive_thread.start()
            
    def connect_socketio(self):
        data = urllib.urlencode({})
        req = urllib2.Request("https://" + self.host + "/" + self.namespace + "/" + self.protocol_version + "/" + self.params, data)
        response = urllib2.urlopen(req)
        response_params = response.read().split(':')
        self.id, heartbeat_interval_str, shutdown_interval_str, supported_transports_str = response_params
        self.heartbeat_interval = int(heartbeat_interval_str)
        supported_transports = supported_transports_str.split(',')
        if not 'websocket' in supported_transports:
            raise Exception("Websocket tranport not supported")
        self.websocket = WebSocket(self.host, 443, "/" + self.namespace + "/" + self.protocol_version + "/websocket/" + self.id)
        self.websocket.EVENT_FRAME.subscribe(self.on_frame)
        self.websocket.EVENT_DISCONNECTED.subscribe(self.on_disconnected)

    def on_disconnected(self, event):
        self.EVENT_DISCONNECTED_SOCKETIO.fire()
        log.debug("disconnected!")
        self.state = SocketIO.DISCONNECTED
                
    def connect(self, endpoint):
        self.websocket.send_message('1::/' + endpoint)

    def on_frame(self, event):
        msg_type, msg_id, msg_endpoint, msg_data = re.match("([0-9]):([^:]*):([^:]*):?(.*)", event.frame).groups()
        if msg_type == SocketIO.MSG_CONNECTED:
            if msg_endpoint == "":
                self.state = SocketIO.CONNECTED
                self.EVENT_CONNECTED_SOCKETIO.fire()
            else:
                self.EVENT_CONNECTED_ENDPOINT.fire(endpoint=msg_endpoint, data=msg_data)
        elif msg_type == SocketIO.MSG_JSON_MESSAGE:
            self.EVENT_JSON_MESSAGE.fire(data=msg_data, endpoint=msg_endpoint)
        else:
            log.debug("Unhandled message %s %s" % (msg_type, msg_data))

    def stop(self):
        self.shuttingdown = True
        self.heartbeat_thread.join(timeout=1)

    def send_json_message(self, endpoint, message):
        self.websocket.send_message("4::" + endpoint + ":" + message)
       
    def keep_alive(self):
        next_heartbeat = time.time()
        try:
            while not self.shuttingdown:
                t =  time.time()
                if self.state == SocketIO.DISCONNECTED:
                    try:
                        self.state = SocketIO.CONNECTING
                        self.connect_socketio()
                    except Exception as e:
                        self.state = SocketIO.DISCONNECTED
                        log.debug(traceback.format_exc())
                        log.warning("Error connecting : " + str(e))
                        time.sleep(SocketIO.RECONNECT_INTERVAL)
                if self.state == SocketIO.CONNECTED and t >= next_heartbeat:
                    # Send heartbeat
                    log.debug("Send heartbeat")
                    self.websocket.send_message('2::')
                    next_heartbeat = t + self.heartbeat_interval - 10
                time.sleep(1)
        except:
            traceback.print_exc()
