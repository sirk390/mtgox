import random
from mtgox.logger import log

WEBSOCKET_KEY_MAXINT = (1 << 32) -1
AVAILABLE_KEY_CHARS = range(0x21, 0x2f + 1) + range(0x3a, 0x7e + 1)

class WebSocketKeys():
    def __init__(self):
        self.number_1, self.key1 = self.make_key12()
        self.number_2, self.key2 = self.make_key12()
        self.key3 = self.make_key3()
         
    def make_key12(self):
        nspaces = random.randint(1, 12)
        max_n = WEBSOCKET_KEY_MAXINT / nspaces
        number_n = random.randint(0, max_n)
        product_n = number_n * nspaces
        log.debug("websocket key: %d %d" % (number_n, product_n))
        key_n = str(product_n)
        for i in range(random.randint(1, 12)):
            c = random.choice(AVAILABLE_KEY_CHARS)
            pos = random.randint(0, len(key_n))
            key_n = key_n[0:pos] + chr(c) + key_n[pos:]
        for i in range(nspaces):
            pos = random.randint(1, len(key_n)-1)
            key_n = key_n[0:pos] + " " + key_n[pos:]
        return number_n, key_n
    
    def make_key3(self):
        return "".join([chr(random.randint(0, 255)) for i in range(8)])

