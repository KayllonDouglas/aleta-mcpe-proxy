import selectors
import socket
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.FileHandler('logs.log'), logging.StreamHandler()])

sel = selectors.DefaultSelector()

addr_list = list()
addr_list.append((socket.gethostbyname(''), 19132))                       # 0
addr_list.append((socket.gethostbyname('dangersky.duckdns.org'), 25592))  # 1

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client_socket.setblocking(False)

client_socket.bind(addr_list[0])

logging.info("Listening on %s" % str(addr_list[0]))

clients = dict()

buff_size = 1024


def is_addr_from_server(addr):
    return addr == addr_list[1]


def handle_socket_events(sock_to_handle, mask_to_handle):
    if mask_to_handle & selectors.EVENT_READ:
        recv_data, recv_addr = sock_to_handle.recvfrom(buff_size)

        if is_addr_from_server(recv_addr):
            original_addr = clients[sock_to_handle.getsockname()]

            client_socket.sendto(recv_data, original_addr)
        else:
            if recv_addr not in clients:
                clients[recv_addr] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                clients[recv_addr].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                clients[recv_addr].setblocking(False)
                clients[recv_addr].connect(addr_list[1])

                sel.register(clients[recv_addr], selectors.EVENT_READ, handle_socket_events)

                clients[clients[recv_addr].getsockname()] = recv_addr

            sock_out = clients[recv_addr]
            sock_out.sendto(recv_data, addr_list[1])


sel.register(client_socket, selectors.EVENT_READ, handle_socket_events)

while True:
    events = sel.select(10)
    for key, mask in events:
        callback = key.data
        callback(key.fileobj, mask)
