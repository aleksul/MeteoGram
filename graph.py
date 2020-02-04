import asyncio
import aiohttp
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from os import path, name

if name == 'nt':
    path = path.dirname(__file__)+'/'
else:
    path = '/home/pi/bot/'

IP_ADD = 'http://'+'192.168.1.52'+'/values'

async def get_info(IP_ADD, session):

