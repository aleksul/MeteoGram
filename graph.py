import asyncio
import aiohttp
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import csv
import logging
from datetime import datetime, timedelta
import restart
from os import path, stat, name, remove
from io import BytesIO


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
            for i in range(len(soup) - 2):  # we don't need two last parameters (wifi)
                i = soup[i].get_text()
                i = i.replace(u'\xa0', u' ')  # change space to SPACE (I'm just normalizing the string)
                i = i.split()  # separate value from measurement units
                data_to_write.append(float(i.pop(0)))
            data_to_write[3] = round(data_to_write[3] * 100 / 133, 2)  # hPa to mm Hg
            file_path = self.new_csv()

            data_to_write.append(datetime.now().strftime('%H:%M:%S'))  # adds time value
            with open(file_path, 'a', newline='') as csv_file:
                writer = csv.writer(csv_file, delimiter=',')
                writer.writerow(data_to_write)
            return True

    def new_csv(self):
        now = datetime.now()
        file_path = self.prog_path + 'data/' + now.strftime('%d-%m-%Y') + '.csv'
        if (not path.exists(file_path)) or (stat(file_path).st_size == 0):  # Firstly, check if we have a file
            with open(file_path, "w", newline='') as csv_file:
                writer = csv.writer(csv_file, delimiter=',')
                writer.writerow(['PM2.5', 'PM10', 'Temp', 'Pres', 'Humidity', 'Time'])
            self.delete_old()
        return file_path

    def read_csv(self, parameter: str, minutes: int, date=None, previous_data=None, previous_time=None):
        data_to_graph = []
        time_to_graph = []
        if date is None:
            date = datetime.now().strftime('%d-%m-%Y')
        file_path = self.prog_path + 'data/' + date + '.csv'  # the name of file we will read
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)  # read the file as csv table
            read_list = list(reader)
        counter = 0
        for i in range(len(read_list) - 1, -1, -1):  # read all the data backwards
            if counter < minutes:  # read until needed limit
                counter += 1
                data_to_graph.append(
                    float(read_list[i][parameter])
                )
                time_to_graph.append(
                    read_list[i]['Time']
                )
            else:
                break
        if previous_data and previous_time:  # if we called the function recursively
            for i in data_to_graph:
                previous_data.append(i)
            for i in time_to_graph:
                previous_time.append(i)
            data_to_graph = previous_data
            time_to_graph = previous_time
        if counter < minutes:  # if that's the end of file
            return self.read_csv(parameter=parameter, minutes=minutes - counter,
                                 date=self.previous_date(date),
                                 previous_data=data_to_graph, previous_time=time_to_graph)
        else:
            return {'data': data_to_graph, 'time': time_to_graph}

    def previous_date(self, date: str):
        date = date.split('-')
        date = datetime(int(date[2]), int(date[1]), int(date[0]))
        delta = timedelta(days=1)
        new_date = date - delta
        new_date = new_date.strftime('%d-%m-%Y')
        return new_date

    def delete_old(self, days_to_save=30, files_num=1):
        now = datetime.now()
        delta = timedelta(days=days_to_save)
        old = now - delta
        day = timedelta(1)
        for i in range(files_num):
            file_path = self.prog_path + 'data/' + old.strftime('%d-%m-%Y') + '.csv'
            if path.exists(file_path):
                remove(file_path)
            old -= day

    def plot_minutes(self, data, parameter):  # do NOT pass over 100 points
        minutes = data['time']
        data = data['data']
        plotted = plt.plot(minutes, data, marker='.')
        plt.gcf().autofmt_xdate()
        ax = plt.gca()
        labels_count = len(ax.xaxis.get_ticklabels())
        if labels_count > 15:
            for label in ax.xaxis.get_ticklabels()[::2]:
                label.set_visible(False)
        if labels_count > 30:
            for label in ax.xaxis.get_ticklabels()[1::2]:
                label.set_visible(False)
        plt.xlabel('Время, минут')
        if parameter == 'PM2.5':
            plt.ylabel('Частицы PM2.5, мгр/м³')
        elif parameter == 'PM10':
            plt.ylabel('Частицы PM10, мгр/м³')
        elif parameter == 'Temp':
            plt.ylabel('Температура, °C')
        elif parameter == 'Pres':
            plt.ylabel('Давление, мм/рт.ст.')
        elif parameter == 'Humidity':
            plt.ylabel('Влажность, %')
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        buffer = buf.getvalue()
        buf.close()
        plt.close()
        return buffer
