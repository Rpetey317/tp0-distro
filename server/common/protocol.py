import socket
import logging
import threading
from .utils import Bet
import datetime
import logging

class ServerProtocol:
    def __init__(self, socket: socket.socket):
        # Initialize socket
        self._socket = socket
        self._running = True
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
        logging.info('action: protocol_shutdown | result: in_progress')
        self._running = False
        if self._socket_open:
            self._socket.close()
            self._socket_open = False
        logging.info('action: protocol_shutdown | result: success')

    def recv_messages(self):
        done = False
        bets = []
        try:
            while not done:
                msg_code = self._socket.recv(1)
                if msg_code == b'\0':
                    # separator
                    continue
                elif msg_code == b'\1':
                    bets.append(self._recv_bet_request())
                    logging.info(f'action: apuesta_recibida | result: success | cantidad: 1')
                elif msg_code == b'\2':
                    recv_bets = self._recv_bet_request_batch()
                    bets.extend(recv_bets)
                    logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(recv_bets)}')
                elif msg_code == b'\3':
                    terminator = self._socket.recv(1)
                    if terminator != b'\0':
                        raise Exception(f"action: recv_bets | result: fail | error: invalid message format. Expected null terminator, got {terminator}")                    
                    logging.info(f'action: recv_bets | result: success')
                    done = True
            return bets
        except Exception as e:
            raise e
    
    def _recv_all(self, n_bytes: int):
        data = b''
        while len(data) < n_bytes:
            data += self._socket.recv(n_bytes - len(data))
        return data
    
    def _recv_u8(self):
        return int.from_bytes(self._recv_all(1), byteorder='big')

    def _recv_u16(self):
        return int.from_bytes(self._recv_all(2), byteorder='big')

    def _recv_u32(self):
        return int.from_bytes(self._recv_all(4), byteorder='big')
    
    def _recv_string(self):
        length = self._recv_u16()
        return self._recv_all(length).decode('utf-8')
    
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
        n_bets = 0
        try:
            n_bets = self._recv_u16()
            bets = []
            for _ in range(n_bets):
                bets.append(self._recv_bet_request())
            return bets
        except Exception as e:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {n_bets} | error: {e}")
            raise e

    def send_message(self, message: any):        
        try:
            msg = f"{message}\0".encode('utf-8')
            total_sent = 0
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
