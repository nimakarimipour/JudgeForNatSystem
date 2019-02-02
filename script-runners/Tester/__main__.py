#!/usr/bin/env python2
from base.server import PartovServer
from base.client import ClientManager
from base.test import TestExecuter
from base.logger import logger
from base.config import config

import atexit, sys, argparse, os, signal, time, importlib
import tests
import json

settings = {}
parser = argparse.ArgumentParser(description="PA1 Tester")


def main():
    # with open('Tester/config.json') as data_file:
    #     data = json.load(data_file)

    cwd = config['cf_path']

    client_manager = ClientManager(cwd, judge=False)

    partov_server = PartovServer(client_manager, cwd, judge=False)

    test_executor = TestExecuter(client_manager=client_manager,
                                 partov_server=partov_server,
                                 sleep_time=config['sleep_time'])
    test_executor.load_tests(tests)

    @atexit.register
    def on_exit():
        client_manager.clean_clients()
        partov_server.stop()

        logger.flush()
        logger.stop()

    def sigint(signal, frame):
        on_exit()
        exit(0)

    signal.signal(signal.SIGINT, sigint)

    if not client_manager.check_exec():
        logger.log("client executeable not found, aborting")
        return

    if config['partov_server'].get('renew_server', False):
        print('renew map for judge')
        client_manager.free_map()
        if not client_manager.new_map():
            logger.log("client server - Failed to create new map", break_after=True, color="error")
            time.sleep(1)
            sys.exit(1)

    partov_server.start()

    print 'beginning to execute tests'
    test_executor.execute_tests()
    on_exit()


def create_loggers():
    logdefs = config.get('loggers', [])
    for logdef in logdefs:
        name = logdef['type']
        module_name, class_name = name[:name.rfind('.')], name[name.rfind('.') + 1:]
        module = __import__(module_name, fromlist=[class_name], globals=globals())
        handlerclass = getattr(module, class_name)

        outfile_name = logdef['output']
        if len(outfile_name.strip()) == 0:
            continue
        outfile = {
            'stdout': sys.stdout,
            'stdin': sys.stdin,
            'stderr': sys.stderr
        }.get(outfile_name, None)

        if not outfile:
            outfile = open(outfile_name, 'w')

        handler = handlerclass(outfile)
        logger.add_handler(handler)
    logger.start()


def option_type(s):
    try:
        k, v = s.split("=")
        return (k, v)
    except:
        raise argparse.ArgumentTypeError("Invalid option, has to be in the format: 'key=value'")


def parse_args():
    parser.add_argument('-f', nargs='?', default=None, type=str, help='Client Framework location')
    parser.add_argument('-p', nargs='?', default=None, type=int, help='Partov port')
    parser.add_argument('-c', nargs='?', default=None, type=str, help='Config File')
    parser.add_argument('--options', nargs='+', dest="options", type=option_type, help='Extra options')
    args, unknown = parser.parse_known_args()

    config['options'] = args.options if args.options else []

    if args.c:
        config_file = args.c
    else:
        config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')
    config.read_from_file(config_file, options=config['options'])

    if args.f:
        config['cf_path'] = args.f
    if args.p:
        config['partov_server']['port'] = args.p


if __name__ == "__main__":
    parse_args()
    create_loggers()
    main()




