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
        
        self._running = True
        self._n_agencies = n_agencies
        
        self._agencies = {}
        self._sigterm_received = False
        
    def run(self) -> bool:
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
        
        processed_agencies = 0
        while self._running and processed_agencies < self._n_agencies:
            try:
                client_sock, _ = self._socket.accept()
                protocol = ServerProtocol(client_sock)
                agency_id = protocol.recv_messages()
                self._agencies[agency_id] = protocol
            except OSError:
                # socket was closed
                continue
            except Exception as e:
                logging.error(f'action: recv_messages | result: fail | error: {e}')
                logging.error(traceback.format_exc())
                continue
            finally:
                processed_agencies += 1
        
        if self._sigterm_received:
            return False
        
        self.draw_lottery()
        return not self._sigterm_received

    def draw_lottery(self):
        try:
            logging.info('action: _sorteo | result: in_progress')
            bets = load_bets()
            winners = [bet for bet in bets if has_won(bet)]
            logging.debug(f'agencias: {self._agencies}')
            for agency_id in self._agencies:
                n_winners = len([bet for bet in winners if bet.agency == agency_id])
                self._agencies[agency_id].send_n_winners(n_winners)
            logging.info('action: sorteo | result: success')
        except OSError:
            # things closed due to sigterm
            return
        except Exception as e:
            logging.error(f'action: sorteo | result: fail | error: {e}')

    def shutdown(self):
        logging.info('action: shutdown | result: in_progress')
        self._running = False
        for protocol in self._agencies.values():
            protocol.shutdown()
        self._socket.close()
        logging.info('action: shutdown | result: success')
