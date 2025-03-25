import socket
import logging
import threading
from .protocol_parser import ProtocolParser
from .models import BetRequest
from .utils import store_bets

class ServerProtocol:
    def __init__(self, port, listen_backlog):
        # Initialize socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(('', port))
        self._socket.listen(listen_backlog)
        
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
        self._running = False
        self._socket.close()

    def _handle_client_connection(self, client_sock):
        try:
            # Read message in chunks until we get EOF
            chunks = []
            received_eof = False
            while not received_eof:
                chunk = client_sock.recv(1024)
                if not chunk:
                    break
                chunks.append(chunk)
                if b'\n' in chunk:
                    received_eof = True
                    chunks[-1] = chunks[-1].rstrip(b'\0')

            raw_msg = b''.join(chunks).decode('utf-8')
            
            addr = client_sock.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {raw_msg}')
            
            bet = self._parser.parse(raw_msg)
            with self._mutex:
                # Utils functions are not thread-safe, so we need a lock
                store_bets([bet])
            logging.info(f'action: apuesta_almacenada | result: success | dni: ${bet.document} | numero: ${bet.number}')
            
        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

    def send_message(self, message: any, client_sock: socket.socket):
        try:
            msg = f"{message}\0".encode('utf-8')
            total_sent = 0
            while total_sent < len(msg):
                sent = client_sock.send(msg[total_sent:])
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
        finally:
            client_sock.close()
