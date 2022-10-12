from socket import AF_INET, SOCK_STREAM, socket
from socketserver import BaseRequestHandler, TCPServer

import cbus

CBUS_HOST, CBUS_PORT = "localhost", 5550


class CBusTCPHandler(BaseRequestHandler):
    # def setup(self) -> None:
    #     # TODO No debería porque se genera cada vez
    #     self._cs_socket = socket(AF_INET, SOCK_STREAM)
    #     self._cs_socket.connect((CS_HOST, CS_PORT))

    def handle(self):
        self.data = self.request.recv(32).strip()
        if len(self.data) == 0:
            # client disconnect
            pass
        else:
            print(self.data)
            frame = cbus.NetworkFrame.parse(self.data)
            print(frame)
            if frame._message.opcode.is_dcc:
                self._cs_socket.sendall(self.data)


if __name__ == "__main__":
    with TCPServer((CBUS_HOST, CBUS_PORT), CBusTCPHandler) as server:
        server.serve_forever(poll_interval=10)
