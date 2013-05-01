import urlparse

def parse_websocket_url(url):
    parsed = urlparse.urlparse(url)
    if parsed.scheme not in ['ws', 'wss']:
        raise Exception("Not a websocket URL")
    secure = (parsed.scheme == "wss")
    port = parsed.port or (secure and 443 or 80)
    return (parsed.hostname, port, parsed.path, secure)
