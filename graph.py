import asyncio
import aiohttp
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import csv
import logging
from datetime import datetime
import restart
from os import path, stat, name, remove


class GRAPH:
    def __init__(self, ip='192.168.0.175', prog_path=None):
        self.ip_add = 'http://' + ip + '/values'
        if prog_path is None:
            if name == 'nt':
                self.prog_path = path.dirname(__file__) + '/'
            else:
                self.prog_path = '/home/pi/bot/'
        else:
            self.prog_path = prog_path

    async def get_info(self, session):
        try:
            async with session.get(self.ip_add) as resp:
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
            data_to_write = []
            for i in range(len(soup)-2):  # we don't need two last parameters (wifi)
                i = soup[i].get_text()
                i = i.replace(u'\xa0', u' ')  # change space to SPACE (I'm just normalizing the string)
                i = i.split()  # separate value from measurement units
                data_to_write.append(float(i.pop(0)))
            data_to_write[3] = data_to_write[3]*100/133  # hPa to mm Hg
            file_path = self.new_csv()
            with open(file_path, 'a', newline='') as csv_file:
                writer = csv.writer(csv_file, delimiter=',')
                writer.writerow(data_to_write)
            return True

    def new_csv(self):
        file_path = self.csv_name()
        if (not path.exists(file_path)) or (stat(file_path).st_size == 0):  # Firstly, check if we have a file
            with open(file_path, "w", newline='') as csv_file:
                writer = csv.writer(csv_file, delimiter=',')
                writer.writerow(['PM2.5', 'PM10', 'Temp', 'Pres', 'Humidity'])
        return file_path

    def csv_name(self):
        now = datetime.now()
        return self.prog_path+'data/'+now.strftime('%d-%m-%Y')+'.csv'

async def main():
    graph = GRAPH()
    async with aiohttp.ClientSession() as session:
        await graph.get_info(session)


if __name__ == '__main__':
    ioloop = asyncio.get_event_loop()
    ioloop.run_until_complete(main())
    ioloop.close()