import asyncore
import ssl
import socket
import errno
import traceback
from mtgox.logger import log

class SSLConnection(asyncore.dispatcher):
    """An asyncore.dispatcher subclass supporting TLS/SSL.
    
    Source: Python-2.7/Lib/test/test_ftplib.py"""
    _ssl_accepting = False
    _ssl_closing = False
    
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.del_channel()
        sock = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
        ssl_sock = ssl.wrap_socket(sock, do_handshake_on_connect=False,
                                 ssl_version=ssl.PROTOCOL_SSLv23)
        self.set_socket(ssl_sock)
        self._ssl_accepting = True

    def _do_ssl_handshake(self):
        log.debug( "_do_ssl_handshake")
        try:
            self.socket.do_handshake()
        except ssl.SSLError as err:
            if err.args[0] in (ssl.SSL_ERROR_WANT_READ,
                               ssl.SSL_ERROR_WANT_WRITE):
                return
            elif err.args[0] == ssl.SSL_ERROR_EOF:
                return self.handle_close()
            raise
        except socket.error as err:
            if err.args[0] == errno.ECONNABORTED:
                return self.handle_close()
        else:
            self._ssl_accepting = False

    def _do_ssl_shutdown(self):
        log.debug( "_do_ssl_shutdown")
        self._ssl_closing = True
        try:
            self.socket = self.socket.unwrap()
        except ssl.SSLError as err:
            if err.args[0] in (ssl.SSL_ERROR_WANT_READ,
                               ssl.SSL_ERROR_WANT_WRITE):
                return
        except socket.error as err:
            # Any "socket error" corresponds to a SSL_ERROR_SYSCALL return
            # from OpenSSL's SSL_shutdown(), corresponding to a
            # closed socket condition. See also:
            # http://www.mail-archive.com/openssl-users@openssl.org/msg60710.html
            pass
        self._ssl_closing = False
        asyncore.dispatcher.close(self)

    def handle_read_event(self):
        log.debug( "handle_read_event")
        if self._ssl_accepting:
            self._do_ssl_handshake()
        elif self._ssl_closing:
            self._do_ssl_shutdown()
        else:
            asyncore.dispatcher.handle_read_event(self)

    def handle_write_event(self):
        log.debug( "handle_write_event")
        if self._ssl_accepting:
            self._do_ssl_handshake()
        elif self._ssl_closing:
            self._do_ssl_shutdown()
        else:
            asyncore.dispatcher.handle_write_event(self)

    def send(self, data):
        log.debug("send")
        try:
            return asyncore.dispatcher.send(self,data)
        except ssl.SSLError as err:
            if err.args[0] in (ssl.SSL_ERROR_EOF, ssl.SSL_ERROR_ZERO_RETURN,
                               ssl.SSL_ERROR_WANT_READ,
                               ssl.SSL_ERROR_WANT_WRITE):
                return 0
            raise

    def recv(self, buffer_size):
        log.debug("recv")
        try:
            return asyncore.dispatcher.recv(self, buffer_size)
        except ssl.SSLError as err:
            if err.args[0] in (ssl.SSL_ERROR_WANT_READ,
                               ssl.SSL_ERROR_WANT_WRITE):
                return b''
            if err.args[0] in (ssl.SSL_ERROR_EOF, ssl.SSL_ERROR_ZERO_RETURN):
                self.handle_close()
                return b''
            raise

    def handle_error(self):
        log.debug("handle_error")
        traceback.print_exc()
        #raise

    def close(self):
        log.debug(traceback.format_stack())
        log.debug("close")
        if (isinstance(self.socket, ssl.SSLSocket) and
            self.socket._sslobj is not None):
            self._do_ssl_shutdown()
        else:
            asyncore.dispatcher.close(self)

