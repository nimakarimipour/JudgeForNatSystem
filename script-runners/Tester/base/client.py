from subprocess import Popen, call, check_output, PIPE, STDOUT
from threading import Thread, Condition
from Queue import Queue,Empty
from logger import logger
from config import config
import os, re, time, signal, sys
import cPickle as pickle
from scapy.all import Ether, wrpcap
# ===================================================================================================================================================== #
# ===================================================================================================================================================== #
# ===================================================================================================================================================== #

class ClientRun:
    def __init__(self, client_number, cwd, server):
        self.client_number = client_number
        self.cwd = cwd
        self.server = server
        self.net_send_queues = {}
        self.net_recv_queues = {}
        self.io_read_queue = Queue()
        self.started = False
        self.start_cond = Condition()
        self.is_alive = True

        self.judge_output = []
        self.client_output = []
        self.judge_recv = {}
        self.client_recv = {}
        self.judge_send = {}
        self.client_send = {}

    def initialize_for_use(self):
        self.find_process_pid()
        self.find_process_port()
        self.start_io_read_thread()

    def set_status(self, status, color="dim"):
        logger.set_test_status("client #%d %s" % (self.client_number, status), color)

    def start_process(self):
        # print 'starting client process #', self.client_number
        DEVNULL = open(os.devnull, 'wb')
        self.set_status("Starting process")
        command = self.server.get_client_run_command(cwd=self.cwd, client_number=self.client_number)
        # command = self.cwd + '/run.sh ' + str(self.client_number)
        self.process = Popen(command, shell=True, executable="/bin/bash", stdin=PIPE, stdout=PIPE, stderr=DEVNULL, preexec_fn=os.setsid)

    def find_process_pid(self):
        self.pid = self.process.pid

    def find_process_port(self):
        lsof = check_output(["lsof", "-i4TCP", "-n", "-P" ])
        lsof = lsof.split("\n")
        try:
            for line in lsof:
                parts = line.split()
                if '->' in line and (parts[1] == str(self.pid)):
                    if not str(self.server.server_port) in parts[8]:
                        continue
                    ports = map(lambda x: x[x.index(":")+1:], parts[8].split("->"))
                    self.port = int(ports[0])
                    return
        except:
            raise ClientRunError("Failed to extract port number for process")

    def start_io_read_thread(self):
        def read_loop():
            while self.is_alive and self.io_read_thread.is_alive():
                s = self.process.stdout.readline()
                if not self.is_alive: break

                if self.started and s is not None:
                    self.io_read_queue.put(s)
                    
                elif not self.started and s is not None:
                    stats = filter(lambda x: s.startswith(x), checkpoint_status_lines)
                    if len(stats) != 0:
                        self.set_status(stats[0])
                    if s.startswith("Simulation started"):
                        self.process.stdout.readline()
                        self.started = True
                        self.start_cond.acquire()
                        self.start_cond.notifyAll()
                        self.start_cond.release()
        self.io_read_thread = Thread(target=read_loop)
        self.io_read_thread.daemon = True
        self.io_read_thread.start()

    def wait_for_start(self, timeout=None):
        if not self.started:
            self.start_cond.acquire()
            self.start_cond.wait(timeout)
            self.start_cond.release()

    def kill(self):
        self.is_alive = False
        os.killpg(self.process.pid, signal.SIGINT)
        self.server.disconnect_client(self)

    def write_io(self, command):
        self.process.stdin.write(command + '\n')
        self.process.stdin.flush()

    def read_io(self, block=True, timeout=None):
        try:
            return self.io_read_queue.get(block=block, timeout=timeout)
        except Empty:
            return None

    def clear_read_queue(self):
        with self.io_read_queue.mutex:
            self.io_read_queue.queue.clear()
        try:
            while True:
                s = self.io_read_queue.get(block=False)
        except Empty: pass

    def put_frame(self, queue_list, frame, iface):
        if iface not in queue_list:
            queue_list[iface] = Queue()
        queue_list[iface].put(frame)

    def get_frame(self, queue_list, iface, block, timeout):
        if iface not in queue_list:
            queue_list[iface] = Queue()
        try:
            return queue_list[iface].get(block=block, timeout=timeout)
        except Empty:
            return None

    def clear_queue(self, queue_list, iface):
        if type(iface) != list:
            iface = [iface]
        for i in iface:
            if i not in queue_list:
                return
            try:
                while True:
                    s = queue_list[i].get(block=False)
            except Empty: pass

    def put_send_frame(self, frame, iface):
        self.set_status('sent frame on iface:' + str(iface))
        self.put_frame(self.net_send_queues, frame, iface)

    def put_recv_frame(self, frame, iface):
        self.set_status('recv frame on iface:' + str(iface))
        self.put_frame(self.net_recv_queues, frame, iface)

    def get_send_frame(self, iface, block=True, timeout=None):
        return self.get_frame(self.net_send_queues, iface, block, timeout)

    def get_recv_frame(self, iface, block=True, timeout=None):
        return self.get_frame(self.net_recv_queues, iface, block, timeout)

    def clear_send_queue(self, iface):
        self.clear_queue(self.net_send_queues, iface)

    def clear_recv_queue(self, iface):
        self.clear_queue(self.net_recv_queues, iface)

    def send_fake_frame(self, iface, frame):
        try:
            self.server.send_frame(client=self, iface=iface, frame=frame)
        except AttributeError:
            error = "Server type '%s' does not support sending frames. Try using the MockServer instead"
            raise ClientRunError(error % type(self.server))

    def load_judge_output(self, path):
        filename = path + '/stdout/' + str(self.client_number) + '.p'
        self.judge_output = pickle.load(open(filename, "rb"))

    def queueToList(self, q):
        out = []
        for i in range(0, q.qsize()):
            out.append(q.get())
        return out

    def mapQueueToMapList(self, mq):
        out = {}
        for (k, q) in mq.iteritems():
            out[k] = []
            for j in range(0, q.qsize()):
                    out[k].append(q.get())
        return out

    def getOriginal(self, ml):
        out = {}
        for (k, l) in ml.iteritems():
            out[k] = []
            for j in range(0, len(l)):
                    out[k].append(l[j].original)
        return out

    def saveFile(self, l, filename):
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except:
                pass
        pickle.dump(l, open(filename, "wb"))

    def save_output(self, path):
        self.set_status('save output node #')
        output = self.client_output
        filename = path + '/stdout/' + str(self.client_number) + ".p"
        self.saveFile(output, filename)

    def load_judge_recv(self, path):
        filename = path + '/recv_frames/' + str(self.client_number) + ".p"
        self.judge_recv = pickle.load(open(filename, "rb"))
        for (k, val) in self.judge_recv.iteritems():
            self.judge_recv[k] = map(Ether, val)

    def save_recv_frames(self, path):
        self.set_status('save recv frames')
        net_recv = self.getOriginal(self.client_recv)
        filename = path + '/recv_frames/' + str(self.client_number) + ".p"
        self.saveFile(net_recv, filename)

    def load_judge_send(self, path):
        filename = path + '/send_frames/' + str(self.client_number) + ".p"
        self.judge_send = pickle.load(open(filename, "rb"))
        for (k, val) in self.judge_send.iteritems():
            self.judge_send[k] = map(Ether, val)

    def save_sent_frames(self, path):
        self.set_status('save send frames')
        net_sent = self.getOriginal(self.client_send)
        filename = path + '/send_frames/' + str(self.client_number) + ".p"
        self.saveFile(net_sent, filename)

    def allQueueToListAndPcap(self, path):
        self.client_recv = self.mapQueueToMapList(self.net_recv_queues)
        self.client_send = self.mapQueueToMapList(self.net_send_queues)
        self.client_output = self.queueToList(self.io_read_queue)
        self.writeLog(path)

    def writeLog(self, path):
        for (i, v) in self.client_recv.iteritems():
            wrpcap(path + "/recv_node:" + str(self.client_number) + "_iface:" + str(i) + '.pcacp', v)
        for (i, v) in self.client_send.iteritems():
            wrpcap(path + "/send_node:" + str(self.client_number) + "_iface:" + str(i) + '.pcacp', v)
        f = open(path + '/stdout_node:' + str(self.client_number) + '.log' , 'w')
        for i in self.client_output:
            f.write(i)
        f.close()


# ===================================================================================================================================================== #
# ===================================================================================================================================================== #
# ===================================================================================================================================================== #

class ClientManager:
    def __init__(self, cwd, judge):
        self.clients = {}
        self.cwd = cwd
        self.config = config['partov_server']
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

    def set_monitor(self , network_monitor):
        self.network_monitor = network_monitor

    def clear(self):
        self.network_monitor.clear()
        for client in self.clients.itervalues():
            client.net_recv_queues = {}
            client.net_send_queues = {}
            client.io_read_queues = {}

    def clean_clients(self):
        while self.clients:
            self.clients.popitem()[1].kill()

    def start_clients(self, server, client_dict={0: 'c'}):
        new_clients = {}
        for (i, val) in client_dict.iteritems():
            path = {
                'j': config['judge_path'],
                'c': config['cf_path'],
            }[val]
            new_clients[i] = ClientRun(i, cwd=path, server=server)
            new_clients[i].start_process()
        # Give time for process creation
        time.sleep(config['sleep_time']/2)

        for (i, client) in new_clients.iteritems():
            client.initialize_for_use()
            self.clients[i] = client

    def disable_capturing(self):
        self.network_monitor.disable_capturing()

    def enable_capturing(self):
        self.network_monitor.enable_capturing()
        self.network_monitor.start()

    def restart_clients(self, count=1):
        self.clean_clients()
        self.start_clients(count)

    def find_client_by_port(self, port):
        for client in self.clients.itervalues():
            if hasattr(client, 'port'):
                if client.port == port:
                    return client
            else:
                raise ClientRunError("client port not found")
        return None


    def new_map(self):
        try:
            self.free_map()
        except Exception as e:
            print 'exception freeing map'
        # command = self.get_new_command()
        command = os.path.join(self.cwd, 'new.sh')
        res = call(command, shell=True, executable="/bin/bash", stdout=PIPE, stderr=PIPE, cwd=self.cwd)
        return  res == 0

    def free_map(self):
        command = os.path.join(self.cwd, 'free.sh')
        return call(command, shell=True, executable="/bin/bash", stdout=PIPE, stderr=PIPE, cwd=self.cwd) == 0

    def check_cwd(self):
        return True

    def check_exec(self):
        directory = os.listdir(self.cwd)
        #java
        if open(os.path.join(self.cwd, 'run.sh'), 'rb').read().count('java Main'):
            exist = ('Main.class' in directory)
        #C/C++
        else:
            exist = ('machine.out' in directory)
        return exist

    def load_judge_all(self, path):
        for client in self.clients.itervalues():
            client.load_judge_output(path)
            client.load_judge_recv(path)
            client.load_judge_send(path)

    def save_judge_all(self, path):
        for client in self.clients.itervalues():
            client.save_recv_frames(path)
            client.save_sent_frames(path)
            client.save_output(path)

    def get_clients_ready_to_judge(self, logpath):
        if not os.path.exists(logpath):
            try:
                os.makedirs(logpath)
            except:
                pass
        for client in self.clients.itervalues():
            client.allQueueToListAndPcap(logpath)


# ===================================================================================================================================================== #
# ===================================================================================================================================================== #
# ===================================================================================================================================================== #

class ClientRunError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

# ===================================================================================================================================================== #
# ===================================================================================================================================================== #
# ===================================================================================================================================================== #

checkpoint_status_lines = [
    "Signing in...",
    "Selecting map...",
    "Connecting to node...",
    "Synchronizing information...",
    "Simulation started",
]
