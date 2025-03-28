import socket
import logging
import signal
from .protocol import ServerProtocol
from .utils import store_bets
import traceback

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(('', port))
        self._socket.listen(listen_backlog)
        
        self._protocol = None
        self._running = True
        self._sigterm_received = False
        
    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        
        def handle_sigterm(signum, frame):
            if signum == signal.SIGTERM:
                self.shutdown()
                self._sigterm_received = True
            else:
                logging.warning(f'action: handle_signal | result: fail | warning: signal {signum} not handled')
            
        signal.signal(signal.SIGTERM, handle_sigterm)
        
        try:
            client_sock, _ = self._socket.accept()
            self._protocol = ServerProtocol(client_sock)
            bet = self._protocol.recv_messages()
            store_bets([bet])
            logging.info(f'action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}')
        except OSError:
            # socket was closed
            return not self._sigterm_received
        except Exception as e:
            logging.error(f'action: recv_messages | result: fail | error: {e}')
            logging.error(traceback.format_exc())
            
        return not self._sigterm_received

    def shutdown(self):
        logging.info('action: shutdown | result: in_progress')
        self._running = False
        if self._protocol:
            self._protocol.shutdown()
        self._socket.close()
        logging.info('action: shutdown | result: success')