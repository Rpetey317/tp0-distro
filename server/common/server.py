import socket
import logging
import signal
import threading
from multiprocessing import Queue
from .protocol import ServerProtocol
from .utils import has_won, BetsMonitor
import traceback

def agency_thread(protocol: ServerProtocol, bets_monitor: BetsMonitor, winners_channel: Queue, done_channel: Queue):
    try:
        agency_id, bets = protocol.recv_messages()
        bets_monitor.add_bets(bets)
        done_channel.put(agency_id)
        
        winners = winners_channel.get()
        protocol.send_n_winners(winners)
        protocol.shutdown()
    except OSError:
        logging.info(f'action: agency_thread | result: success | warning: socket closed')
    except Exception as e:
        logging.error(f'action: agency_thread | result: fail | error: {e}')
        logging.error(traceback.format_exc())
    
class Agency:
    thread: threading.Thread
    protocol: ServerProtocol
    winners_channel: Queue
    done_channel: Queue
    agency_id: int
    
    def __init__(self, thread: threading.Thread, protocol: ServerProtocol, winners_channel: Queue, done_channel: Queue, agency_id: int):
        self.thread = thread
        self.protocol = protocol
        self.winners_channel = winners_channel
        self.done_channel = done_channel
        self.agency_id = agency_id

class Server:
    def __init__(self, port, listen_backlog, n_agencies):
        # Initialize server socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(('', port))
        self._socket.listen(listen_backlog)
        
        self._running = True
        self._n_agencies = n_agencies
        
        self._agencies = []
        self._bets = BetsMonitor()
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
        
        sigterm_received = False
        processed_agencies = 0
        while self._running and processed_agencies < self._n_agencies:
            try:
                client_sock, _ = self._socket.accept()
                protocol = ServerProtocol(client_sock)
                winners_channel = Queue()
                done_channel = Queue()
                agency_t = threading.Thread(target=agency_thread, args=(protocol, self._bets, winners_channel, done_channel))
                agency = Agency(thread=agency_t, protocol=protocol, winners_channel=winners_channel, done_channel=done_channel, agency_id=-1)
                agency_t.start()
                self._agencies.append(agency)
            except OSError:
                # socket was closed
                self.shutdown()
            except Exception as e:
                logging.error(f'action: recv_messages | result: fail | error: {e}')
                logging.error(traceback.format_exc())
                continue
            finally:
                processed_agencies += 1
        
        if self._sigterm_received:
            return False
        
        for agency in self._agencies:
            agency_id = agency.done_channel.get() # wait for every agency to finish
            agency.agency_id = agency_id
        self.draw_lottery()
        return not self._sigterm_received
    
    def draw_lottery(self):
        try:
            logging.info('action: _sorteo | result: in_progress')
            bets = self._bets.get_bets()
            winners = [bet for bet in bets if has_won(bet)]
            for agency in self._agencies:
                agency_winners = [bet for bet in winners if bet.agency == agency.agency_id]
                agency.winners_channel.put(len(agency_winners))
                
            logging.info('action: sorteo | result: success')
        except OSError:
            # things closed
            return
        except Exception as e:
            logging.error(f'action: sorteo | result: fail | error: {e}')

    def shutdown(self):
        logging.info('action: shutdown | result: in_progress')
        self._running = False
        for agency in self._agencies:
            agency.protocol.shutdown()
            agency.winners_channel.close()
            agency.done_channel.close()
            agency.thread.join()
        self._socket.close()
        logging.info('action: shutdown | result: success')
