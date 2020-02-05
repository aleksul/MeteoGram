"""
Restarts the current program.
Note: this function does not return.
Any cleanup action (like saving data) must be done before calling this function.
"""
import logging
from os import execl
from os import name
import sys
from time import sleep


def program(secs_of_sleep):
    logging.info(f"Restart in {secs_of_sleep} seconds!")
    sleep(secs_of_sleep)
    if name == 'nt':
        logging.info('Restart on Windows')
        exec(open('/home/pi/bot/bot_main.py').read())
    else:
        logging.info(f'Restart on {name}')
        python = sys.executable
        execl(python, python, *sys.argv)
    return None
