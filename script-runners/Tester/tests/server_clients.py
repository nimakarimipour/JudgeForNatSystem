from ..base.test import Test, grade
import copy
import socket, struct
import time

class ServerClientsTest(Test):
    description = "Server Clients"
    order = 2
    enabled = True
    test_order = ['test_simple_routing', 'test_simple_msg', 'test_simple_nat', 'test_local_nat']
    save_judge_mode=False

    def before(self):
        client_count = 13
        self.kill_clients()
        self.new_map()
        client_dict = {0:'c', 1:'c', 2:'c', 3:'c', 4:'j', 5:'c', 6:'c'}
        # client_dict = {0: 'j', 1: 'j', 2: 'j', 3: 'j', 4:'j', 5:'j', 6:'j'}
        self.start_clients(client_dict=client_dict)

        for client in self.clients.itervalues():
            client.wait_for_start()
        time.sleep(self.sleep_time)

    def after(self):
        self.kill_clients()
        self.free_map()

    def save_judge(self, path):
        self.client_manager.save_judge_all(path)

    def load_judge(self, path):
        self.client_manager.load_judge_all(path)
    # ===================================================================================================================================================== #

    @grade(25)
    def test_simple_routing(self):
        self.clients[0].write_io('make a connection to server on port 2000')
        time.sleep(self.sleep_time)

        self.client_manager.get_clients_ready_to_judge('log/test_simple_routing')
        if not self.save_judge_mode:
            self.assert_true(self.check_output(0), message='Output for node 0 did not match', end=False, grade=3)
            self.assert_true(self.check_send_frames(0), message='send frames node 0 did not match', end=False, grade=3)
            self.assert_true(self.check_send_frames(2), message='send frames node 2 did not match', end=False, grade=7)
            self.assert_true(self.check_recv_frames(2), message='recv frames node 2 did not match', end=False, grade=7)
            self.assert_true(self.check_output(3), message='Output node 3 did not match', end=False, grade=5)

    @grade(25)
    def test_simple_msg(self):
        self.clients[0].write_io('make a connection to server on port 2000')
        time.sleep(self.sleep_time)
        self.clients[2].write_io('make a connection to server on port 3000')
        time.sleep(self.sleep_time)
        self.clients[2].write_io('get info of 1')
        time.sleep(self.sleep_time)
        self.clients[2].write_io('make a local session to 1')
        time.sleep(self.sleep_time)
        self.clients[2].write_io('send msg to 1:salam')
        time.sleep(self.sleep_time)
        self.clients[0].write_io('send msg to 2:aleyk')
        time.sleep(self.sleep_time)

        self.client_manager.get_clients_ready_to_judge('log/test_simple_msg')
        if not self.save_judge_mode:
            self.assert_true(self.check_output(0), message='Output for node 0 did not match', end=False, grade=4)
            self.assert_true(self.check_send_frames(0), message='send frames node 0 did not match', end=False, grade=5)
            self.assert_true(self.check_send_frames(2), message='send frames node 2 did not match', end=False, grade=5)
            self.assert_true(self.check_recv_frames(2), message='recv frames node 2 did not match', end=False, grade=5)
            self.assert_true(self.check_output(2), message='Output node 2 did not match', end=False, grade=3)
            self.assert_true(self.check_output(3), message='Output node 3 did not match', end=False, grade=3)


    @grade(25)
    def test_simple_nat(self):
        self.clients[4].write_io('block port range 3000 3400')
        time.sleep(self.sleep_time)
        self.clients[5].write_io('make a connection to server on port 3310')
        time.sleep(self.sleep_time*3)

        self.client_manager.get_clients_ready_to_judge('log/test_simple_nat')
        if not self.save_judge_mode:
            self.assert_true(self.check_output(5), message='Output for node 5 did not match', end=False, grade=7)
            self.assert_true(self.check_send_frames(5), message='send frames node 5 did not match', end=False, grade=7)
            self.assert_true(self.check_recv_frames(5), message='recv frames node 5 did not match', end=False, grade=7)
            self.assert_true(self.check_output(3), message='Output node 3 did not match', end=False, grade=4)

    @grade(25)
    def test_local_nat(self):
        self.clients[5].write_io('make a connection to server on port 3300')
        time.sleep(self.sleep_time)
        self.clients[4].write_io('block port range 3000 3500')
        time.sleep(self.sleep_time)
        self.clients[6].write_io('make a connection to server on port 3410')
        time.sleep(self.sleep_time * 3)
        self.clients[6].write_io('get info of 1')
        time.sleep(self.sleep_time)
        self.clients[6].write_io('make a local session to 1')
        time.sleep(self.sleep_time)

        self.client_manager.get_clients_ready_to_judge('log/test_local_nat')
        if not self.save_judge_mode:
            self.assert_true(self.check_output(5), message='Output for node 5 did not match', end=False, grade=4)
            self.assert_true(self.check_send_frames(5), message='send frames node 5 did not match', end=False, grade=4)
            self.assert_true(self.check_recv_frames(5), message='recv frames node 5 did not match', end=False, grade=4)
            self.assert_true(self.check_output(6), message='Output for node 6 did not match', end=False, grade=4)
            self.assert_true(self.check_send_frames(6), message='send frames node 6 did not match', end=False, grade=4)
            self.assert_true(self.check_recv_frames(6), message='recv frames node 6 did not match', end=False, grade=5)
