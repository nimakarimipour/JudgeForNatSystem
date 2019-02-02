from ..base.test import Test, grade
import copy
import socket, struct
import time

class OptionalNatTest(Test):
    description = "Optional Nat"
    order = 3
    enabled = True
    test_order = ['test_optional_nat_simple', 'test_optional_nat_complicated']
    save_judge_mode=False

    def before(self):
        client_count = 13
        self.kill_clients()
        self.new_map()
        client_dict = {3: 'j', 7: 'c', 9: 'j', 10: 'c', 11: 'j'}
        # client_dict = {3: 'j', 7: 'j', 9: 'j', 10: 'j', 11:'j'}
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
    def test_optional_nat_simple(self):
        self.clients[9].write_io('make a connection to server on port 2000')
        time.sleep(self.sleep_time)
        self.clients[10].write_io('bad command')
        time.sleep(self.sleep_time)

        self.client_manager.get_clients_ready_to_judge('log/test_optional_nat_simple')
        if not self.save_judge_mode:
            self.assert_true(self.check_output(9), message='Output for node 9 did not match', end=False, grade=5)
            self.assert_true(self.check_output(10), message='Output for node 10 did not match', end=False, grade=5)
            self.assert_true(self.check_send_frames(9), message='send frames node 9 did not match', end=False, grade=10)
            self.assert_true(self.check_recv_frames(9), message='recv frames node 9 did not match', end=False, grade=5)

    @grade(75)
    def test_optional_nat_complicated(self):
        self.clients[7].write_io('block port range 3000 3500')
        time.sleep(self.sleep_time)
        self.clients[9].write_io('make a connection to server on port 3310')
        time.sleep(self.sleep_time * 3)
        self.clients[11].write_io('make a connection to server on port 4000')
        time.sleep(self.sleep_time * 3)
        self.clients[9].write_io('get info of 2')
        time.sleep(self.sleep_time)
        self.clients[9].write_io('make a public session to 2')
        time.sleep(self.sleep_time)

        self.client_manager.get_clients_ready_to_judge('log/test_optional_nat_complicated')
        if not self.save_judge_mode:
            self.assert_true(self.check_output(10), message='Output for node 10 did not match', end=False, grade=5)
            self.assert_true(self.check_send_frames(10), message='send frames node 10 did not match', end=False, grade=10)
            self.assert_true(self.check_recv_frames(10), message='recv frames node 10 did not match', end=False, grade=10)

            self.assert_true(self.check_output(7), message='Output for node 7 did not match', end=False, grade=5)
            self.assert_true(self.check_send_frames(7), message='send frames node 7 did not match', end=False, grade=10)
            self.assert_true(self.check_recv_frames(7), message='recv frames node 7 did not match', end=False, grade=10)

            self.assert_true(self.check_output(11), message='Output for node 11 did not match', end=False, grade=10)
            self.assert_true(self.check_output(9), message='Output for node 9 did not match', end=False, grade=10)
            self.assert_true(self.check_output(3), message='Output for node 3 did not match', end=False, grade=5)
