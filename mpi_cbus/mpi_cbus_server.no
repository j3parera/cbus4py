"""
    Net template
"""
from logging import DEBUG, Formatter, getLogger
from logging.handlers import RotatingFileHandler
from socketserver import BaseRequestHandler, TCPServer
from mpi_cbus import Frame

CBUS_HOST, CBUS_PORT = "localhost", 5550


class CBusTCPHandler(BaseRequestHandler):
    """Handler of TCP frames with CBUS message

    Args:
        BaseRequestHandler: the handler
    """

    def setup(self):
        self._logger = getLogger("mpi_cbus")
        self._logger.info("%s:%d connected", *self.client_address)

    def finish(self):
        self._logger.info("%s:%d disconnected", *self.client_address)

    def send(self, frame: Frame):
        """Callback for unexpected output

        Args:
            frame (Frame): Frame to be transmitted
        """
        self._logger.info("OUT: %s", str(frame))
        self.request.sendall(frame.net_encoded_frame)

    def handle(self):
        while True:
            self.data = self.request.recv(32).strip()
            if len(self.data) == 0:
                # disconnect
                break
            req_frames = Frame.parse_from_network(self.data)
            for req_frame in req_frames:
                self._logger.info("IN : %s", str(req_frame))


if __name__ == "__main__":
    handler = RotatingFileHandler("mpi_cbus.log", maxBytes=102400, backupCount=5)
    logger = getLogger("mpi_cbus")
    logger.setLevel(DEBUG)
    bf = Formatter("[{asctime} {name}] {levelname:8s} {message}", datefmt="%Y-%m-%d %H:%M:%S", style="{")
    handler.setFormatter(bf)
    logger.addHandler(handler)
    logger.info("MPI_CS4 start")
    with TCPServer((CBUS_HOST, CBUS_PORT), CBusTCPHandler) as server:
        server.serve_forever(poll_interval=10)
    logger.info("MPI_CS4 end")
