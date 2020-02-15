"""
Restarts the current program.
Note: this function does not return.
Any cleanup action (like saving data) must be done before calling this function.
"""
import logging
from os import name, path, spawnv, P_NOWAIT
from sys import executable, argv
from time import sleep


class RestartError(Exception):
    pass


class MeteoError(RestartError):
    pass


class SendError(RestartError):
    pass


class GetUpdatesError(RestartError):
    pass


class UserRestart(RestartError):
    pass


class InternetConnectionError(RestartError):
    pass


def program(secs_of_sleep):
    if name == 'nt':
        prog_path = path.dirname(__file__) + '\\'
    else:
        prog_path = '/home/pi/bot/'
    logging.info(f"Restart in {secs_of_sleep} seconds!")
    sleep(secs_of_sleep)
    logging.info(f'Restart on {name}')
    python = executable
    spawnv(P_NOWAIT, python, [python, prog_path+'bot_main.py', *argv])
    exit()
