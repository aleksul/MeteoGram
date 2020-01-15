"""
Restarts the current program.
Note: this function does not return.
Any cleanup action (like saving data) must be done before calling this function.
"""
import logging
from time import sleep

def program():    
    logging.info("Restart in 5 sec!")
    sleep(5)
    logging.info("Restart!")
    exec(open('main.py').read())
