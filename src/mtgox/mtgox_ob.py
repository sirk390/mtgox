from urllib import urlencode
import urllib2
import time
from hashlib import sha512
from hmac import HMAC
import base64
import json

def get_nonce():
    return int(time.time()*100000)

def sign_data(secret, data):
    return base64.b64encode(str(HMAC(secret, data, sha512).digest()))
      
class MtGoxHttp:
    def __init__(self, auth_key, auth_secret):
        self.auth_key = auth_key
        self.auth_secret = base64.b64decode(auth_secret)
        
    def build_query(self, req={}):
        req["nonce"] = get_nonce()
        post_data = urlencode(req)
        headers = {}
        #headers["User-Agent"] = "trader"
        headers["Rest-Key"] = self.auth_key
        headers["Rest-Sign"] = sign_data(self.auth_secret, post_data)
        return (post_data, headers)
        
    def query(self, path, args):
        data, headers = self.build_query(args)
        req = urllib2.Request("https://mtgox.com/api/1/"+path, data, headers)
        res = urllib2.urlopen(req, data)
        return json.load(res)

if __name__ == '__main__':
    from secret import AUTH_KEY, AUTH_SECRET 
    
    mtgox = MtGoxHttp(AUTH_KEY, AUTH_SECRET )
    print json.dumps(mtgox.query("BTCEUR/public/fulldepth", {}), indent=4)
    
    