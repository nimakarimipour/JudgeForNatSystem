import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *
from config import config
from threading import Thread, Condition
import os, socket, SocketServer as socketserver
import time, struct, imp, inspect, select

# ===================================================================================================================================================== #
# ===================================================================================================================================================== #
# ===================================================================================================================================================== #

def add_new_tcp_data(seq, packet_data, expected_seq, out_of_order_data, recv_buff):
    if expected_seq < seq:
        if seq in out_of_order_data:
            if len(out_of_order_data[seq]) < len(packet_data):
                out_of_order_data[seq] = packet_data
        else:
            out_of_order_data[seq] = packet_data
        return (expected_seq, out_of_order_data, recv_buff)
    if seq < expected_seq:
        overlap = expected_seq - seq
        packet_data = packet_data[overlap:]
    recv_buff += packet_data
    expected_seq += len(packet_data)
    for s in sorted(out_of_order_data):
        if expected_seq < s:
            break
        pktdata = out_of_order_data[s]
        if s < expected_seq:
            overlap = expected_seq - s
            pktdata = pktdata[overlap:]
        recv_buff += pktdata
        expected_seq += len(pktdata)
        del out_of_order_data[s]
    return (expected_seq, out_of_order_data, recv_buff)

# ===================================================================================================================================================== #
# ===================================================================================================================================================== #
# ===================================================================================================================================================== #

class PartovServer:
    def __init__(self, client_manager, cwd, judge):
        self.config = config['partov_server']
        self.server_port = self.config['port']
        self.client_manager = client_manager
        self.client_states = {}
        self.cwd = cwd
        self.packets = []
        self.judge = judge
        file = open(os.path.join(self.cwd, 'info.sh'))
        # print('parsing info.sh')
        for line in file.readlines():
            if line.startswith('user'):
                self.user = line[5:-1]
                # print('user: ', self.user)
            if line.startswith('pass'):
                self.password = line[5:-1]
                # print('pass: ', self.password)

    def start(self):
        def sniff_loop():
            sniff(filter = ("tcp and port %d" % self.server_port), prn = lambda x: self.handle_frame(x))

        self.is_alive = True
        self.sniff_thread = Thread(target = sniff_loop)
        self.sniff_thread.daemon = True
        self.sniff_thread.start()

    def stop(self):
        self.is_alive = False

    def disconnect_client(self, client):
        if client in self.client_states:
            del self.client_states[client]

    def get_client(self, port):
        client = self.client_manager.find_client_by_port(port)
        if client in self.client_states:
            client_state = self.client_states[client]
        else:
            client_state = ClientState()
            self.client_states[client] = client_state
        return (client, client_state)

    def handle_frame(self, frame):
        if not self.is_alive:
            return

        tcp = frame.payload.payload
        if type(tcp.payload) == NoPayload:
            return
        if tcp.sport == self.server_port:
            client_port = tcp.dport
        elif tcp.dport == self.server_port:
            client_port = tcp.sport
        else:
            return

        client, client_state = self.get_client(client_port)

        if client == None or not client.started:
            # print "gaaav"
            return
        if tcp.sport == self.server_port:
            self.handle_receive_data(client, client_state, tcp.seq, list(tcp.load))
        elif tcp.dport == self.server_port:
            self.handle_send_data(client, client_state, tcp.seq, list(tcp.load))

    def handle_receive_data(self, client, state, seq = -1, packet_data = None):
        # if self.judge:
        #     print 'handling judge recv frame'
        # else:
        #     print 'handling recv frame'

        if packet_data != None:
            # if (len(packet_data) > 10 and packet_data[:5] == ['\x00', '\x00', '\x00', '\x04', '\x00']):
            #     frame = Ether(''.join(packet_data[10:]))
            #     interface = struct.unpack("!I", ''.join(packet_data[6:10]))[0]
            #     client.put_recv_frame(frame, interface)
            if state.expected_recv_seq == -1:
                state.expected_recv_seq = seq
            state.expected_recv_seq, state.recv_out_of_order, state.recv_buff =\
                    add_new_tcp_data(seq, packet_data,
                            state.expected_recv_seq, state.recv_out_of_order, state.recv_buff)

        if len(state.recv_buff) >= state.recv_pending:
            packet = ''.join(state.recv_buff[:state.recv_pending])
            state.recv_buff = state.recv_buff[state.recv_pending:]
            state.recv_pending = 0

            if state.recv_state == Const.StateInRecv:
                state.recv_state = Const.Nothing
                state.recv_pending = Const.RecvCommandLength
            else:
                command, size = struct.unpack("!IH", packet[0:6])
                if (packet_data != None and len(packet_data) > 10 and packet_data[:5] == ['\x00', '\x00', '\x00', '\x04', '\x00']):
                    frame = Ether(''.join(packet_data[10:]))
                    interface = struct.unpack("!I", ''.join(packet_data[6:10]))[0]
                    client.put_recv_frame(frame, interface)
                if command == Const.RawFrameReceivedNotificationType:
                    state.recv_state = Const.StateInRecv
                    state.recv_pending = size
                else:
                    state.recv_pending = Const.RecvCommandLength
            self.handle_receive_data(client, state)

    def handle_send_data(self, client, state, seq = -1, packet_data = None):
        # if self.judge:
        #     print 'handling judge sent frame'
        # else:
        #     print 'handling sent frame'
        
        if packet_data != None:
            if state.expected_send_seq == -1:
                state.expected_send_seq = seq
            state.expected_send_seq, state.send_out_of_order, state.send_buff =\
                    add_new_tcp_data(seq, packet_data,
                            state.expected_send_seq, state.send_out_of_order, state.send_buff)

        if len(state.send_buff) >= state.send_pending:
            packet = ''.join(state.send_buff[:state.send_pending])
            state.send_buff = state.send_buff[state.send_pending:]
            state.send_pending = 0

            if state.send_state == Const.StateInSendFrame:
                if(len(packet) > 4):
                    frame = Ether(packet)
                    client.put_send_frame(frame, state.send_iface)
                state.send_state = Const.Nothing
                state.send_pending = Const.SendCommandLength
            elif state.send_state == Const.StateInSendData:
                length, iface = struct.unpack("!HI", packet)
                length -= 4
                state.send_state = Const.StateInSendFrame
                state.send_iface = iface
                state.send_pending = length
            else:
                command = struct.unpack("!I", packet[0:4])[0]
                if command == Const.SendFrameCommand:
                    state.started = True
                    state.send_state = Const.StateInSendData
                    state.send_pending = 6
                else:
                    state.send_pending = Const.SendCommandLength

            self.handle_send_data(client, state)

    def get_client_run_command(self, cwd, client_number=0):
        node = "node" + str(client_number)
        command = ''
        if open(os.path.join(cwd, 'run.sh'), 'rb').read().count('java Main'):
            command = "java -classpath %s Main --ip %s --port %d --map %s --node %s --user %s --pass %s --id %s" % \
                (cwd, self.config['ip'], self.config['port'], self.config['map'], node,
                 self.user, self.password, self.user)
        else:
            target = os.path.join(cwd, 'machine.out')
            command = "%s --ip %s --port %d --map %s --node %s --user %s --pass %s --id %s" % \
                (target, self.config['ip'],
                 self.config['port'], self.config['map'], node,
                 self.user, self.password, self.user)
        return command

# ===================================================================================================================================================== #
# ===================================================================================================================================================== #
# ===================================================================================================================================================== #

class Const:
    SendFrameCommand = 1
    RawFrameReceivedNotificationType = 4

    RecvCommandLength = 6
    SendCommandLength = 4

    StateInSendData = 1
    StateInSendFrame = 2
    StateInRecv = 1

    Nothing = -1

# ===================================================================================================================================================== #
# ===================================================================================================================================================== #
# ===================================================================================================================================================== #

class ClientState:
    def __init__(self):
        self.send_buff = []
        self.recv_buff = []
        self.send_out_of_order = {}
        self.recv_out_of_order = {}
        self.send_pending = 4
        self.recv_pending = 6
        self.recv_state = -1
        self.send_state = -1
        self.send_iface = 0
        self.expected_recv_seq = -1
        self.expected_send_seq = -1
        self.started = False

# ===================================================================================================================================================== #
# ===================================================================================================================================================== #
# ===================================================================================================================================================== #