import socket
import logging

class ServerProtocol:
    def __init__(self, port, listen_backlog):
        # Initialize socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(('', port))
        self._socket.listen(listen_backlog)
        
        self._running = True
        
    def run(self):
        while self._running:
            try:
                client_sock = self._socket.accept()
                self._handle_client_connection(client_sock)
            except OSError as e:
                # socket was closed
                continue
            except Exception as e:
                logging.error(f'action: server_loop | result: fail | error: {e}')
                continue
            
        logging.info('action: shutdown | result: success')

    def shutdown(self):
        logging.info('action: shutdown | result: in_progress')
        self._running = False
        self._socket.close()

    def _handle_client_connection(self, client_sock):
        try:
            # TODO: Modify the receive to avoid short-reads
            msg = client_sock.recv(1024).rstrip().decode('utf-8')
            addr = client_sock.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')
            
            self.send_message("{}\n".format(msg), client_sock)
        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

    def send_message(self, message: any, client_sock: socket.socket):
        try:
            # TODO: Modify the send to avoid short-writes
            client_sock.send("{}\n".format(message).encode('utf-8'))
        except OSError as e:
            logging.error(f"action: send_message | result: fail | error: {e}")
        finally:
            client_sock.close()
