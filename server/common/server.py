import socket
import logging
import signal
import threading
from .protocol import ServerProtocol
from .utils import store_bets, load_bets, has_won
import traceback

class Server:
    def __init__(self, port, listen_backlog, n_agencies):
        # Initialize server socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(('', port))
        self._socket.listen(listen_backlog)
        
        self._protocol = None
        self._mutex = threading.Lock()
        self._running = True
        self._n_agencies = n_agencies
        
        self._agencies = {}
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
        
        processed_agencies = 0
        while self._running and processed_agencies < self._n_agencies:
            try:
                bets = []
                client_sock, _ = self._socket.accept()
                self._protocol = ServerProtocol(client_sock)
                agency_id = self._protocol.recv_messages()
                self._agencies[agency_id] = self._protocol
            except OSError:
                # socket was closed
                self.shutdown()
            except Exception as e:
                logging.error(f'action: recv_messages | result: fail | error: {e}')
                logging.error(traceback.format_exc())
                continue
            finally:
                processed_agencies += 1
                
        self.draw_lottery()
        logging.info('action: shutdown | result: success')

    def draw_lottery(self):
        logging.info('action: sorteo | result: in_progress')
        with self._mutex:
            bets = load_bets()
            for bet in bets:
                if has_won(bet):
                    logging.info(f'action: ganadores | result: success | ganador: {bet.first_name} {bet.last_name} | numero: {bet.number}')
        logging.info('action: sorteo | result: success')

    def shutdown(self):
        logging.info('action: shutdown | result: in_progress')
        self._running = False
        if self._protocol:
            self._protocol.shutdown()
        self._socket.close()
        
