from ..base.test import Test, grade
import copy
import socket, struct
import time

class ComplicatedTest(Test):
    description = "Complicated Test"
    order = 4
    enabled = True
    test_order = ['test_exceptions_1', 'test_exceptions_2', 'test_complicated']
    save_judge_mode=False

    def before(self):
        client_count = 13
        self.kill_clients()
        self.new_map()
        client_dict = {3: 'c', 7: 'j', 2: 'c', 8: 'c', 9:'c', 13:'j', 14:'c'}
        # client_dict = {3: 'j', 7: 'j', 2: 'j', 8: 'j', 9:'j', 13:'j', 14:'j'}
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
    def test_exceptions_1(self):
        self.clients[14].write_io('bad command')
        time.sleep(self.sleep_time)
        self.clients[2].write_io('get info of 2')
        time.sleep(self.sleep_time)

        self.client_manager.get_clients_ready_to_judge('log/test_exceptions_1')
        if not self.save_judge_mode:
            self.assert_true(self.check_output(14), message='Output for node 14 did not match', end=False, grade=5)
            self.assert_true(self.check_send_frames(2), message='send frames node 2 did not match', end=False, grade=5)
            self.assert_true(self.check_recv_frames(2), message='recv frames node 2 did not match', end=False, grade=5)
            self.assert_true(self.check_output(2), message='Output node 2 did not match', end=False, grade=5)
            self.assert_true(self.check_output(3), message='Output node 3 did not match', end=False, grade=5)

    @grade(25)
    def test_exceptions_2(self):
        self.clients[14].write_io('make a connection to server on port 3000')
        time.sleep(self.sleep_time*3)
        self.clients[2].write_io('make a connection to server on port 2000')
        time.sleep(self.sleep_time)
        self.clients[2].write_io('make a connection to server on port 2000')
        time.sleep(self.sleep_time)
        self.clients[14].write_io('get info of 2')
        time.sleep(self.sleep_time*3)
        self.clients[14].write_io('send msg to 2:salam')
        time.sleep(self.sleep_time*3)

        self.client_manager.get_clients_ready_to_judge('log/test_exceptions_2')
        if not self.save_judge_mode:
            self.assert_true(self.check_output(14), message='Output for node 14 did not match', end=False, grade=5)
            self.assert_true(self.check_output(3), message='Output for node 3 did not match', end=False, grade=5)
            self.assert_true(self.check_output(2), message='Output for node 2 did not match', end=False, grade=5)
            self.assert_true(self.check_send_frames(14), message='send frames node 14 did not match', end=False, grade=5)
            self.assert_true(self.check_send_frames(2), message='send frames node 2 did not match', end=False, grade=5)


    @grade(50)
    def test_complicated(self):
        self.clients[13].write_io('block port range 3000 3500')
        time.sleep(self.sleep_time)
        self.clients[14].write_io('make a connection to server on port 3310')
        time.sleep(self.sleep_time*4)
        self.clients[8].write_io('make a connection to server on port 3000')
        time.sleep(self.sleep_time)
        self.clients[9].write_io('make a connection to server on port 3000')
        time.sleep(self.sleep_time)
        self.clients[8].write_io('get info of 3')
        time.sleep(self.sleep_time)
        self.clients[8].write_io('make a public session to 3')
        time.sleep(self.sleep_time)
        self.clients[9].write_io('get info of 2')
        time.sleep(self.sleep_time)
        self.clients[9].write_io('make a public session to 2')
        time.sleep(self.sleep_time)
        self.clients[8].write_io('send msg to 3:salam')
        time.sleep(self.sleep_time)
        self.clients[9].write_io('send msg to 2:chetori')
        time.sleep(self.sleep_time)

        self.client_manager.get_clients_ready_to_judge('log/test_complicated')
        if not self.save_judge_mode:
            self.assert_true(self.check_output(3), message='Output for node 3 did not match', end=False, grade=5)
            self.assert_true(self.check_output(8), message='Output for node 8 did not match', end=False, grade=5)
            self.assert_true(self.check_output(9), message='Output for node 9 did not match', end=False, grade=5)
            self.assert_true(self.check_output(14), message='Output for node 14 did not match', end=False, grade=5)
            self.assert_true(self.check_send_frames(3), message='send frames node 3 did not match', end=False, grade=5)
            self.assert_true(self.check_send_frames(8), message='send frames node 8 did not match', end=False, grade=5)
            self.assert_true(self.check_send_frames(9), message='send frames node 9 did not match', end=False, grade=5)
            self.assert_true(self.check_send_frames(14), message='send frames node 14 did not match', end=False, grade=5)
            self.assert_true(self.check_recv_frames(3), message='recv frames node 3 did not match', end=False, grade=10)
