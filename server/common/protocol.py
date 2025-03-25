import socket
import logging
import threading
from .protocol_parser import ProtocolParser
from .utils import Bet
import datetime

class ServerProtocol:
    def __init__(self, socket: socket.socket):
        # Initialize socket
        self._socket = socket
        
        self._running = True
        self._parser = ProtocolParser()
        
        self._mutex = threading.Lock()
        self._socket_open = True
        
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
            if self._socket_open:
                self._socket.close()
                self._socket_open = False

    def recv_message(self):
        bets = []
        sent_eof = False
        try:
            while not sent_eof:
                msg_code = self._socket.recv(1)
                if msg_code == b'\0':
                    sent_eof = True
                    continue
                elif msg_code == b'\1':
                    return self._recv_bet_request()
                elif msg_code == b'\2':
                    return self._recv_bet_request_batch()
        except OSError:
            # socket was closed
            return bets
        except Exception as e:
            logging.error(f"action: recv_messages | result: fail | error: {e}")
            raise e

    def _recv_u8(self):
        return self._socket.recv(1)

    def _recv_u16(self):
        return int.from_bytes(self._socket.recv(2), byteorder='big')

    def _recv_u32(self):
        return int.from_bytes(self._socket.recv(4), byteorder='big')
    
    def _recv_string(self):
        length = self._recv_u16()
        return self._socket.recv(length).decode('utf-8')
    
    def _recv_date(self):
        year = self._recv_u16()
        month = self._recv_u8()
        day = self._recv_u8()
        return datetime.date(year, month, day)

    def _recv_bet_request(self):
        name = self._recv_string()
        surname = self._recv_string()
        doc = self._recv_u32()
        birth_date = self._recv_date()
        number = self._recv_u32()
        return Bet("1", name, surname, str(doc), birth_date.strftime('%Y-%m-%d'), str(number))

    def _recv_bet_request_batch(self):
        n_bets = self._recv_u16()
        bets = []
        for _ in range(n_bets):
            bets.append(self._recv_bet_request())
        return bets

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
