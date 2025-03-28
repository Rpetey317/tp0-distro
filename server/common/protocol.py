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

    def recv_messages(self) -> tuple[int, list[Bet]]:
        try:
            agency_id = -1
            bets = []
            while self._socket_open:
                msg_code = self._socket.recv(1)
                
                if msg_code == b'\0':
                    # separator
                    continue
                
                elif msg_code == b'\1':
                    bets.append(self._recv_bet_request(1))
                    logging.info(f'action: apuesta_recibida | result: success | cantidad: 1')
                    
                elif msg_code == b'\2':
                    agency_id, recv_bets = self._recv_bet_request_batch()
                    logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(recv_bets)}')
                    bets.extend(recv_bets)
                elif msg_code == b'\3':
                    terminator = self._socket.recv(1) # null terminator
                    if terminator != b'\0':
                        raise Exception(f"action: recv_bets | result: fail | error: invalid message format. Expected null terminator, got {terminator}")
                    logging.info(f'action: recv_bets | result: success | agency_id: {agency_id}')
                    return agency_id, bets
                
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

    def _recv_bet_request(self, agency_id: int):
        name = self._recv_string()
        surname = self._recv_string()
        doc = self._recv_u32()
        birth_date = self._recv_date()
        number = self._recv_u32()
        return Bet(str(agency_id), name, surname, str(doc), birth_date.strftime('%Y-%m-%d'), str(number))

    def _recv_bet_request_batch(self) -> tuple[int, list[Bet]]:
        n_bets = 0
        try:
            agency_id = self._recv_u16()
            n_bets = self._recv_u16()
            bets = []
            for _ in range(n_bets):
                bets.append(self._recv_bet_request(agency_id))
            return agency_id, bets
        except Exception as e:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {n_bets} | error: {e}")
            raise e

    def send_n_winners(self, n_winners: int):        
        try:
            msg = b'\1' + n_winners.to_bytes(4, byteorder='big')
            total_sent = self._socket.send(msg)
            if total_sent != len(msg):
                raise OSError("Socket connection broken")
            
            logging.info(f"action: send_message | result: success | n_winners: {n_winners}")
        except OSError as e:
            # socket closing isn't necessarily an error, so it gets logged as a warning
            logging.warning(f"action: send_message | result: fail | error: {e}")
            raise e
        except Exception as e:
            logging.error(f"action: send_message | result: fail | error: {e}")
            raise e
