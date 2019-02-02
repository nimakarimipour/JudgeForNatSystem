from functools import partial
from Queue import Queue, Empty
from logger import logger
import time, imp, inspect, sys
import signal
import time
import copy
import shutil

class TestExecuter:
    def __init__(self, client_manager, partov_server, sleep_time):
        self.client_manager = client_manager
        self.partov_server = partov_server
        self.sleep_time = sleep_time

    def load_tests(self, test_module):
        is_test_class = lambda x: inspect.isclass(x) and issubclass(x, Test) and x != Test
        test_classes = inspect.getmembers(test_module, is_test_class)
        test_instances = map(
            lambda x: x[1](self.client_manager, self.partov_server, self.sleep_time),
            test_classes)
        self.tests = test_instances
        self.tests.sort(key=lambda test: test.order)


    def execute_tests(self):
        logger.log('executing test')
        try:
            shutil.rmtree('log')
        except:
            pass
        is_test_method = lambda x: inspect.ismethod(x) and x.__name__.startswith("test_")
        for test in self.tests:
            test_methods = map(lambda x: x[1], inspect.getmembers(test, is_test_method))

            def key(meth):
                try:
                    if getattr(test, 'test_order', None):
                        return test.test_order.index(meth.__name__)
                    return 0
                except ValueError:
                    return len(test_methods)

            test_methods.sort(key=key)

            logger.start_test(test.description)
            if getattr(test, "init", None):
                test.init()

            for test_method in test_methods:
                try:
                    test.start_test_method()

                    if getattr(test, "before", None):
                        test.before()

                    signal.alarm(300)
                    if not test.save_judge_mode and getattr(test, 'load_judge'):
                        test.load_judge('Tester/judge_outs/' + test_method.__name__)
                    try:
                        test_method()
                    except Exception as e:
                        print 'Exception caught'
                        print e
                        print "Timed out!"

                    if test.save_judge_mode and getattr(test, 'save_judge'):
                        test.save_judge('Tester/judge_outs/' + test_method.__name__)

                    if getattr(test, "after", None):
                        test.after()

                except EndTestMethodException:
                    continue
                except EndTestException:
                    break
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    test.add_exception(e)
                finally:
                    test.end_test_method()

                f = open("log/%s/error.log" % test_method.__name__, 'w')
                for exception in test.method_exceptions:
                    if isinstance(exception, AssertionError):
                        f.write("#Assertion Error: " + exception.message + "\n")
                f.close()
                self.partov_server.packets = []
                test.method_exceptions = []

            # for exception in test.exceptions:
            #     if isinstance(exception, AssertionError):
            #         logger.log(" " + exception.message, "red")
            #         # break
            #     else:
            #         logger.log(" [EXCEPTION] " + str(exception), "red")
            #         # break
            logger.end_test('Finished Test')

            if getattr(test, "end", None):
                test.end()
                # ===================================================================================================================================================== #
        logger.line_break()


# ===================================================================================================================================================== #
# ===================================================================================================================================================== #
# ===================================================================================================================================================== #

class Test(object):
    def __init__(self, client_manager, partov_server, sleep_time):

        self.client_manager = client_manager

        self.partov_server = partov_server

        self.clients = self.client_manager.clients

        self.log = self.log_status
        self.grade_sum = 0
        self.grade_current = 0

        self.exceptions = []
        self.method_exceptions = []

        self.sleep_time = sleep_time

    def free_map(self):
        self.client_manager.free_map()

    def new_map(self):
        self.log('creating new client map')
        counter = 10
        while not self.client_manager.new_map():
            self.log('creating new client map attempt' + str(10 - counter))
            time.sleep(1)
            self.client_manager.free_map()
            time.sleep(1)
            counter -= 1
            if counter == 0:
                logger.set_test_grade(0)
                logger.end_test()
                self.log('map creation failed, exiting test')
                sys.exit(1)
        time.sleep(1)

    def disable_capturing(self):
        self.client_manager.disable_capturing()

    def enable_capturing(self):
        self.client_manager.enable_capturing()

    def clear_clients(self):
        self.client_manager.clear()

    def start_clients(self, client_dict):
        self.client_manager.start_clients(client_dict=client_dict, server=self.partov_server)

    def kill_clients(self):
        self.log('killing old clients')
        self.client_manager.clean_clients()

    def log_status(self, status, color="dim"):
        logger.set_test_status(status, color)

    def wait(self, seconds):
        time.sleep(seconds)

    def current_time(self):
        return int(round(time.time() * 1000))

    def check_output(self, index):
        self.clients[index].set_status('checking output')
        j = self.clients[index].judge_output
        c = self.clients[index].client_output
        if not len(c) == len(j):
            return False

        for i in range(0, len(c)):
            if c[i] != None and c[i] == j[i]:
                pass
            else:
                return False
        return True

    def check_recv_frames(self, index):
        self.clients[index].set_status('checking receive frame')

        c = self.clients[index].client_recv
        j = self.clients[index].judge_recv

        if len(c) != len(j):
            return False

        for (k, l) in c.iteritems():
            if not self.check_frame_lists(l, j[k]):
                return False
        return True

    def check_send_frames(self, index):
        self.clients[index].set_status('checking send frame')

        c = self.clients[index].client_send
        j = self.clients[index].judge_send

        if len(c) != len(j):
            return False

        for (k, l) in c.iteritems():
            if not self.check_frame_lists(l, j[k]):
                return False
        return True

    def check_frame_lists(self, a, b):
        if len(a) != len(b):
            return False

        for i in range(0, len(a)):
            if a[i].original != b[i].original:
                return False
        return True

    def check_unordered_frame_lists(self, client_frames, judge_frames):
        if len(client_frames) != len(judge_frames):
            return False

        found_frames = []

        for i in range(0, len(judge_frames)):
            found_frames.append(False)

        for i in range(0, len(client_frames)):
            found = False
            for j in range(0, len(judge_frames)):
                if not found_frames[j] and client_frames[i] != None and self.compare_packets(client_frames[i],
                                                                                             judge_frames[j]):
                    found_frames[j] = True
                    found = True
                    break
            if not found:
                return False
        return True

    def compare_packets(self, packet_1, packet_2):
        bytes_1 = str(packet_1)
        bytes_2 = str(packet_2)

        if len(bytes_1) != len(bytes_2):
            return False

        n = 0
        for byte in bytes_1:
            if bytes_2[n] != byte:
                return False
            n = n + 1

        return True

    def add_exception(self, exception):
        self.test_method_success = False
        self.exceptions.append(exception)
        self.method_exceptions.append(exception)

    def start_test_method(self):
        self.grade_current = 0
        self.test_method_success = True

    def end_test_method(self):
        self.grade_sum += self.grade_current
        self.grade_current = 0

    def end_if_failed(self):
        if len(self.exceptions) > 0:
            raise EndTestException()

    def assert_false(self, condition, message="", end=True, grade=0):
        return self.assert_true(not condition, message=message, end=end, grade=grade)

    def assert_true(self, condition, message="", end=True, grade=0):
        if not condition:
            self.add_exception(AssertionError(message))
            if end:
                raise EndTestMethodException()
            return False
        elif grade > 0:
            self.grade(grade)
        return True

    def grade(self, amount):
        self.set_current_test_grade(self.grade_current + amount)

    def set_current_test_grade(self, amount):
        self.grade_current = amount
        logger.set_test_grade(self.grade_current + self.grade_sum)


class EndTestException(Exception):
    pass


class EndTestMethodException(Exception):
    pass


# entirely useless :|
def grade(amount):
    def wrapper(func):
        def inner(self, *args, **kwargs):
            func(self, *args, **kwargs)
            if self.test_method_success:
                self.set_current_test_grade(amount)

        inner.__name__ = func.__name__
        return inner

    return wrapper


def signal_handler(signum, frame):
    raise Exception("Timed out!!")


signal.signal(signal.SIGALRM, signal_handler)


