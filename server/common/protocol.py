import socket
import logging
import threading
from .utils import Bet, store_bets
import datetime
import logging

class ServerProtocol:
    def __init__(self, socket: socket.socket):
        # Initialize socket
        self._socket = socket
        
        self._running = True
        
        self._mutex = threading.Lock()
        self._socket_open = True

    def shutdown(self):
        logging.info('action: shutdown | result: in_progress')
        self._running = False
        if self._socket_open:
            self._socket.close()
            self._socket_open = False

    def recv_messages(self) -> str:
        try:
            while True:
                msg_code = self._socket.recv(1)
                
                if msg_code == b'\0':
                    # separator
                    continue
                
                elif msg_code == b'\1':
                    bet = self._recv_bet_request(1)
                    separator = self._socket.recv(1)
                    if separator != b'\0':
                        raise Exception(f"action: recv_messages | result: fail | error: invalid message format. Expected null terminator, got {separator}")
                    logging.info(f'action: apuesta_recibida | result: success | cantidad: 1')
                    return bet
                
                else:
                    raise Exception(f"invalid message code: {msg_code}")
                
        except Exception as e:
            raise e
    
    def _recv_u8(self):
        return int.from_bytes(self._socket.recv(1), byteorder='big')

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
