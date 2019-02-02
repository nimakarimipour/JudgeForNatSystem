from ..base.test import Test, grade
import copy
import socket, struct
import time

class SingleClientTest(Test):
    description = "Single Client"
    order = 1
    enabled = True
    test_order = ['test_connect_to_server', 'test_get_info', 'test_local_session',
                  'test_public_session', 'test_send_message']
    save_judge_mode=False

    def before(self):
        client_count = 13
        self.kill_clients()
        self.new_map()
        client_dict = {0:'c', 1:'j', 2:'j', 3:'j'}
        # client_dict = {0: 'j', 1: 'j', 2: 'j', 3: 'j'}
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

    @grade(20)
    def test_connect_to_server(self):
        self.clients[0].write_io('make a connection to server on port 2000')
        time.sleep(self.sleep_time)

        self.client_manager.get_clients_ready_to_judge('log/test_connect_to_server')
        if not self.save_judge_mode:
            self.assert_true(self.check_output(0), message='Output for node 0 did not match', end=False, grade=10)
            self.assert_true(self.check_send_frames(0), message='send frames node 0 did not match', end=False, grade=10)

    @grade(20)
    def test_get_info(self):
        self.clients[0].write_io('make a connection to server on port 2000')
        time.sleep(self.sleep_time)
        self.clients[1].write_io('make a connection to server on port 3000')
        time.sleep(self.sleep_time)
        self.clients[0].write_io('get info of 2')
        time.sleep(self.sleep_time)

        self.client_manager.get_clients_ready_to_judge('log/test_get_info')
        if not self.save_judge_mode:
            self.assert_true(self.check_output(0), message='Output for node 0 did not match', end=False, grade=10)
            self.assert_true(self.check_send_frames(0), message='send frames node 0 did not match', end=False, grade=10)

    @grade(20)
    def test_local_session(self):
        self.clients[0].write_io('make a connection to server on port 2000')
        time.sleep(self.sleep_time)
        self.clients[1].write_io('make a connection to server on port 3000')
        time.sleep(self.sleep_time)
        self.clients[0].write_io('get info of 2')
        time.sleep(self.sleep_time)
        self.clients[0].write_io('make a local session to 2')
        time.sleep(self.sleep_time)

        self.client_manager.get_clients_ready_to_judge('log/test_local_session')
        if not self.save_judge_mode:
            self.assert_true(self.check_output(0), message='Output for node 0 did not match', end=False, grade=10)
            self.assert_true(self.check_send_frames(0), message='send frames node 0 did not match', end=False, grade=10)

    @grade(20)
    def test_public_session(self):
        self.clients[0].write_io('make a connection to server on port 2000')
        time.sleep(self.sleep_time)
        self.clients[1].write_io('make a connection to server on port 3000')
        time.sleep(self.sleep_time)
        self.clients[0].write_io('get info of 2')
        time.sleep(self.sleep_time)
        self.clients[0].write_io('make a public session to 2')
        time.sleep(self.sleep_time)

        self.client_manager.get_clients_ready_to_judge('log/test_public_session')
        if not self.save_judge_mode:
            self.assert_true(self.check_output(0), message='Output for node 0 did not match', end=False, grade=10)
            self.assert_true(self.check_send_frames(0), message='send frames node 0 did not match', end=False, grade=10)

    @grade(20)
    def test_send_message(self):
        self.clients[0].write_io('make a connection to server on port 2000')
        time.sleep(self.sleep_time)
        self.clients[1].write_io('make a connection to server on port 3000')
        time.sleep(self.sleep_time)
        self.clients[0].write_io('get info of 2')
        time.sleep(self.sleep_time)
        self.clients[0].write_io('make a local session to 2')
        time.sleep(self.sleep_time)
        self.clients[0].write_io('send msg to 2:salam')
        time.sleep(self.sleep_time)

        self.client_manager.get_clients_ready_to_judge('log/test_send_message')
        if not self.save_judge_mode:
            self.assert_true(self.check_output(0), message='Output for node 0 did not match', end=False, grade=10)
            self.assert_true(self.check_send_frames(0), message='send frames node 0 did not match', end=False, grade=10)


# ===================================================================================================================================================== #
