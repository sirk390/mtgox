import asyncore
import json
from mtgox.socketio import SocketIO
from asyncore import socket_map
import time
from mtgox.logger import log
from mtgox.event import Event

class MtGoxStreaming():
    def __init__(self):
        self.socket_io = SocketIO("socketio.mtgox.com", "socket.io", "1", "?Currency=USD")
        self.socket_io.EVENT_CONNECTED_SOCKETIO.subscribe(self.on_connected)
        self.socket_io.EVENT_DISCONNECTED_SOCKETIO.subscribe(self.on_disconnected)
        self.socket_io.EVENT_CONNECTED_ENDPOINT.subscribe(self.on_connected_mtgox)
        self.socket_io.EVENT_JSON_MESSAGE.subscribe(self.on_json_message)
        self.EVENT_TRADE = Event()
        self.EVENT_TICKER_USD = Event()
        self.EVENT_DEPTH_USD = Event()
        self.socket_io.start()
        self.trade =  "dbf1dee9-4f2e-4a08-8cb7-748919a71b21" #Trades
        self.ticker = "d5f06780-30a8-4a48-a2f8-7ed181b4a13f" #Ticker USD
        self.depth =  "24e67e0d-1cad-4cc0-9e7a-f8523ef460fe" #Depth  USD

    def on_connected(self, event):
        self.socket_io.connect("mtgox")
        
    def on_disconnected(self, event):
        log.info("Disconnected")
        
    def on_connected_mtgox(self, event):
        log.info( "Mtgox Connected")
        self.socket_io.send_json_message("/mtgox", '{"channel":"dbf1dee9-4f2e-4a08-8cb7-748919a71b21", "op":"subscribe"}')
        self.socket_io.send_json_message("/mtgox", '{"channel":"d5f06780-30a8-4a48-a2f8-7ed181b4a13f", "op":"subscribe"}')
        self.socket_io.send_json_message("/mtgox", '{"channel":"24e67e0d-1cad-4cc0-9e7a-f8523ef460fe", "op":"subscribe"}')
        
    def on_json_message(self, event):
        message = json.loads(event.data)
        if 'private' in message:
            private = message['private'] #ticker, trade, depth
            if  private=='trade':      
                self.EVENT_TRADE.fire(message=message)
            elif private=='ticker': 
                self.EVENT_TICKER_USD.fire(message=message)
            elif private=='depth':   
                self.EVENT_DEPTH_USD.fire(message=message)
        log.debug(event.endpoint + " " + str(message))
        
    def on_subscribed(self, channel, message):
        channel = message['channel']
        if channel==self.trade:    channel_name = 'trade'
        elif channel==self.ticker: channel_name = 'ticker'
        elif channel==self.depth:  channel_name = 'depth'
        else:                        channel_name = 'unknown'
        log.info( "subscribed to channel " + channel_name)

if __name__ == "__main__":
    mtgox = MtGoxStreaming()
    
    def on_trade(event):
        message = event.message
        log.info(str(message['trade']["price"]) + " " + str(message['trade']["amount"]) + " " + message['trade']["price_currency"] )
    
    mtgox.EVENT_TRADE.subscribe(on_trade)
    
    while True:
        if socket_map:
            asyncore.loop()
        else:
            time.sleep(0.3)
        