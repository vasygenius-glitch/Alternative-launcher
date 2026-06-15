import socket
import json
import struct

def ping_server(ip, port=25565, timeout=3.0):
    """
    Pings a Minecraft server using the Server List Ping protocol.
    Returns a dictionary with status or None if failed.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))

        # Send Handshake
        def write_varint(sock, data):
            while True:
                byte = data & 0x7F
                data >>= 7
                if data:
                    byte |= 0x80
                sock.send(struct.pack('B', byte))
                if not data:
                    break

        # Protocol version, server address, port, next state (1 for status)
        packet_data = b'\x00' # Packet ID 0

        # Protocol version (using 47 for 1.8, most servers respond regardless)
        varint_prot = b'\x2f'

        # Server address
        addr_len = len(ip)
        addr_bytes = struct.pack('B', addr_len) + ip.encode('utf-8')

        # Port
        port_bytes = struct.pack('>H', port)

        # Next state
        state_bytes = b'\x01'

        payload = packet_data + varint_prot + addr_bytes + port_bytes + state_bytes

        # Send length + payload
        write_varint(sock, len(payload))
        sock.send(payload)

        # Request
        write_varint(sock, 1) # Length
        sock.send(b'\x00')    # Packet ID 0

        # Read Response
        def read_varint(sock):
            val = 0
            for i in range(5):
                byte = sock.recv(1)
                if not byte: break
                b = struct.unpack('B', byte)[0]
                val |= (b & 0x7F) << (7 * i)
                if not (b & 0x80):
                    break
            return val

        packet_len = read_varint(sock)
        packet_id = read_varint(sock)

        if packet_id != 0:
            return None

        json_len = read_varint(sock)
        json_data = b""
        while len(json_data) < json_len:
            chunk = sock.recv(json_len - len(json_data))
            if not chunk: break
            json_data += chunk

        sock.close()

        return json.loads(json_data.decode('utf-8'))
    except Exception:
        return None
