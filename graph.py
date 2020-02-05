import asyncio
import aiohttp
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import csv
import logging
from time import time
from os import path, name
import restart

IP_ADD = 'http://' + '192.168.1.175' + '/values'

if name == 'nt':
    path = path.dirname(__file__) + '/'
else:
    path = '/home/pi/bot/'

CSV_FILE = path+'meteo.csv'


async def get_info(ip, session):
    try:
        async with session.get(ip) as resp:
            assert resp.status == 200
            text = await resp.text()
    except AssertionError:
        logging.warning('Assertion error in getting info!')
        return None
    except Exception as err:
        logging.error(f"Getting info from meteo error: {type(err)}:{err}")
        return restart.program(1)
    else:
        soup = BeautifulSoup(text, 'html.parser')
        soup = soup.find_all('td', class_='r')
        soup[]


