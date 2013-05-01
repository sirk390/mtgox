from mtgox.logger import log

class HandshakeResponseIncomplete(Exception):
    pass

class WebSocketHandshakeRequest(object):
    def __init__(self, resource, hostname, port, key1, key2, key3):
        self.resource = resource
        self.hostname = hostname
        self.port = port
        self.key1 = key1
        self.key2 = key2
        self.key3 = key3
    
class WebSocketHandshakeResponse(object):
    def __init__(self, status, message, headers, challenge_response):
        self.status = status
        self.message = message
        self.headers = headers
        self.challenge_response = challenge_response
    def __str__(self):
        return "HandshakeResponse(status:%s,message:%s,headers:%s,challenge_response:%s" % (self.status, self.message, str(self.headers), self.challenge_response)


class HandshakeResponseParser(object):
    @staticmethod
    def parse_header_challenge(headers, challenge_response):
        headerlines = headers.split("\r\n")
        log.debug("handshake:" + headerlines[0])
        http_ver, status, http_message= headerlines[0].split(" ", 2)
        log.debug("handshake_headers:" + str([header.split(": ")  for header in headerlines[1:]]))
        headers = dict(header.split(": ")  for header in headerlines[1:])
        return WebSocketHandshakeResponse(status, http_message, headers, challenge_response)

    @staticmethod
    def parse(data):
        """ return (HandshakeResponse, remaining) or raise HandshakeDataIncomplete"""
        header_end = "\r\n\r\n"
        challenge_response_size = 16
        if header_end in data:
            idx = data.index(header_end)
            handshake_end = idx + len(header_end) + challenge_response_size
            if len(data) >= handshake_end:
                headers = data[:idx]
                challenge_response = data[idx + len(header_end):handshake_end]
                remaining = data[handshake_end:]
                return (HandshakeResponseParser.parse_header_challenge(headers, challenge_response), remaining)
        raise HandshakeResponseIncomplete()
    
class HandshakeRequestFormater(object):
    @staticmethod
    def format(request):
        host = '%s:%d' % (request.hostname, request.port) if (request.port != 80) else request.hostname
        headers = ['GET %s HTTP/1.1' % (request.resource),
                   'Upgrade: WebSocket',
                   'Connection: Upgrade',
                   'Host: ' + host, 
                   'Origin: ' + host,
                   'Sec-WebSocket-Key1: %s' % (request.key1),
                   'Sec-WebSocket-Key2: %s' % (request.key2)]
        return '\r\n'.join(headers) + "\r\n\r\n" + request.key3 + "\r\n"
        