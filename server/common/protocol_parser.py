from .utils import Bet
from socket import ntohs
import datetime

class ProtocolParser:
    """
    Helper class to parse messages from and to the client.
    """
    def __init__(self):
        pass

    def parse(self, message: bytes) -> any:
        if len(message) == 0:
            raise ValueError("Message is empty")
        if message[-1] != 0:
            raise ValueError("Message is not null-terminated")
        
        msg_enum = message[0]
        match msg_enum:
            case 0:
                return self._parse_bet_request(message[1:-1])
            case _:
                raise ValueError(f"Invalid message type: {msg_enum}")
            
    def serialize(self, message: any) -> bytes:
        pass
            
    def _parse_string(self, message: bytes, read: int) -> tuple[str, int]:
        length = ntohs(int.from_bytes(message[read:read + 2]))
        read += 2
        return message[read:read + length].decode('utf-8'), read + length
    
    def _parse_u32(self, message: bytes, read: int) -> tuple[int, int]:
        value = ntohs(int.from_bytes(message[read:read + 4]))
        return value, read + 4
    
    def _parse_date(self, message: bytes, read: int) -> tuple[datetime.date, int]:
        year = ntohs(int.from_bytes(message[read:read + 2]))
        month = message[read + 2]
        day = message[read + 3]
        return datetime.date(year, month, day), read + 4
            
    def _parse_bet_request(self, message: bytes) -> Bet:
        read = 0
        nombre, read = self._parse_string(message, read)
        apellido, read = self._parse_string(message, read)
        documento, read = self._parse_u32(message, read)
        nacimiento, read = self._parse_date(message, read)
        numero, read = self._parse_u32(message, read)
        
        return Bet("1", nombre, apellido, str(documento), nacimiento.strftime('%Y-%m-%d'), str(numero))
