import socket
import logging
import signal
import threading
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
        self._mutex = threading.Lock()
        self._running = True
        
    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        
        def handle_sigterm(signum, frame):
            if signum == signal.SIGTERM:
                logging.info('action: shutdown | result: in_progress')
                with self._mutex:
                    self.shutdown()
                logging.info('action: shutdown | result: success')
                exit(0)
            else:
                logging.warning(f'action: handle_signal | result: fail | warning: signal {signum} not handled')
            
        signal.signal(signal.SIGTERM, handle_sigterm)
        
        while self._running:
            try:
                bets = []
                client_sock, _ = self._socket.accept()
                self._protocol = ServerProtocol(client_sock)
                bets = self._protocol.recv_message()
                with self._mutex:
                    store_bets(bets)
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
            except OSError:
                # socket was closed
                continue
            except Exception:
                logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
                logging.error(traceback.format_exc())
                continue
            
        logging.info('action: shutdown | result: success')

    def shutdown(self):
        logging.info('action: shutdown | result: in_progress')
        self._running = False
        if self._protocol:
            self._protocol.shutdown()
        self._socket.close()
        
