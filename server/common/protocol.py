import socket
import logging
import threading
from .protocol_parser import ProtocolParser
from .utils import store_bets

class ServerProtocol:
    def __init__(self, socket: socket.socket):
        # Initialize socket
        self._socket = socket
        
        self._running = True
        self._parser = ProtocolParser()
        
        self._mutex = threading.Lock()
        
    def run(self):
        while self._running:
            try:
                client_sock, _ = self._socket.accept()
                self._handle_client_connection(client_sock)
            except OSError as e:
                # socket was closed
                continue
            except Exception as e:
                logging.error(f'action: server_loop | result: fail | error: {e}')
                continue
            
        logging.info('action: shutdown | result: success')

    def shutdown(self):
        logging.info('action: shutdown | result: in_progress')
        with self._mutex:
            self._running = False
            self._socket.close()

    def recv_message(self):
        try:
            # Read message in chunks until we get EOF
            chunks = []
            received_eof = False
            with self._mutex:
                while not received_eof:
                    chunk = self._socket.recv(1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    if b'\0' in chunk:
                        received_eof = True
                        chunks[-1] = chunks[-1].rstrip(b'\0')

            raw_msg = b''.join(chunks)
            
            addr = self._socket.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | raw_msg: {raw_msg}')
            
            return self._parser.parse(raw_msg)            
        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")

    def send_message(self, message: any):        
        try:
            msg = f"{message}\0".encode('utf-8')
            total_sent = 0
            with self._mutex:
                while total_sent < len(msg):
                    sent = self._socket.send(msg[total_sent:])
                    if sent == 0:
                        raise OSError("Socket connection broken")
                    total_sent += sent
            
            logging.info(f"action: send_message | result: success | msg: {message}")
        except OSError as e:
            # socket closing isn't necessary an error, so it gets logged as a warning
            logging.warning(f"action: send_message | result: fail | error: {e}")
            raise e
        except Exception as e:
            logging.error(f"action: send_message | result: fail | error: {e}")
            raise e
