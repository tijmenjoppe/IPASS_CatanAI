import struct
import jsonpickle
import jsonpickle.ext.numpy as jsonpickle_numpy
jsonpickle_numpy.register_handlers()

# Reworked this with some help from https://stackoverflow.com/a/17668009/12892735


def recvall(sock, n) -> bytearray:
    """Sticks the buffer pieces of a large message together."""
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        data.extend(packet)
    return data


class NetworkBasis:
    """The network basis to send and receive python dictionaries, to make communicating easier."""
    def __init__(self, socket):
        self.socket = socket

    def send(self, message: dict) -> dict:
        out_data = bytes(jsonpickle.encode(message, keys=True), 'UTF-8')
        message_size = len(out_data)
        print(f"send size: {message_size}")
        self.socket.sendall(struct.pack('>I', message_size) + out_data)

    def receive(self) -> dict:
        raw_msglen = recvall(self.socket, 4)
        message_size = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return jsonpickle.decode(recvall(self.socket, message_size).decode(), keys=True)
