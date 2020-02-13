"""
Restarts the current program.
Note: this function does not return.
Any cleanup action (like saving data) must be done before calling this function.
"""
import logging
from os import execl, name, path
import sys
from time import sleep


class restart:

    def __init__(self, loop):
        if name == 'nt':
            self.prog_path = path.dirname(__file__) + '\\'
        else:
            self.prog_path = '/home/pi/bot/'
        self.loop = loop

    def program(self, secs_of_sleep):
        logging.info(f"Restart in {secs_of_sleep} seconds!")
        self.loop.stop()
        sleep(secs_of_sleep)
        if name == 'nt':
            logging.info('Restart on Windows')
            exec(open(self.prog_path+'bot_main.py').read())
        else:
            logging.info(f'Restart on {name}')
            python = sys.executable
            execl(python, python, *sys.argv)
