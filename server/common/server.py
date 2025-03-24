import socket
import logging
import signal
from .protocol import ServerProtocol
class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._protocol = ServerProtocol(port, listen_backlog)

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
                
                # this check is to avoid race conditions when closing the server shortly after starting it
                if hasattr(self, '_protocol'):
                    self._protocol.shutdown()
                logging.info('action: shutdown | result: success')
                exit(0)
            else:
                logging.warning(f'action: handle_signal | result: fail | warning: signal {signum} not handled')
            
        signal.signal(signal.SIGTERM, handle_sigterm)
        
        self._protocol.run()
