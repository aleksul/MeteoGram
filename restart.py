"""
Restarts the current program.
Note: this function does not return.
Any cleanup action (like saving data) must be done before calling this function.
"""
import logging
from os import execl, name, path
import sys
from time import sleep


def program(secs_of_sleep):
    if name == 'nt':
        prog_path = path.dirname(__file__) + '/'
    else:
        prog_path = '/home/pi/bot/'
    logging.info(f"Restart in {secs_of_sleep} seconds!")
    sleep(secs_of_sleep)
    if name == 'nt':
        logging.info('Restart on Windows')
        exec(open(f'{prog_path}bot_main.py').read())
    else:
        logging.info(f'Restart on {name}')
        python = sys.executable
        execl(python, python, *sys.argv)
    return None
