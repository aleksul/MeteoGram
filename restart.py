"""
Restarts the current program.
Note: this function does not return.
Any cleanup action (like saving data) must be done before calling this function.
"""
import logging
from os import execl
import sys
def program():
    logging.info("Restart!")
    #exec(open('/home/pi/bot/bot_main.py').read())
    python = sys.executable
    execl(python, python, *sys.argv)
