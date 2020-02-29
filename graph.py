import asyncio
from aiohttp import ClientTimeout
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from bs4 import BeautifulSoup
import csv
import logging
from datetime import datetime, timedelta, time
from os import path, stat, name, remove, listdir
from io import BytesIO
from restart import MeteoError


class GRAPH:
    def __init__(self, ip='192.168.0.175', prog_path=None, timeout=15):
        self.ip_add = 'http://' + ip + '/values'
        if prog_path is None:
            if name == 'nt':
                self.prog_path = path.dirname(__file__) + '\\'
            else:
                self.prog_path = '/home/pi/bot/'
        else:
            self.prog_path = prog_path
        self.timeout = ClientTimeout(total=timeout)

    async def get_info(self, session, bad_requests=0):
        try:
            async with session.get(self.ip_add, timeout=self.timeout) as resp:
                assert resp.status == 200
                text = await resp.text()
                data = self.html_parser(text)
        except Exception as err:
            logging.error(f"Getting info from meteo error: {type(err)}:{err}")
            await asyncio.sleep(5)
            if bad_requests >= 5:
                logging.critical('Too many bad requests with meteo')
                raise MeteoError
            else:
                bad_requests += 1
                return await self.get_info(session, bad_requests=bad_requests)
        else:
            return self.csv_write(data)

    @staticmethod
    def html_parser(text):
        soup = BeautifulSoup(text, 'html.parser')
        soup = soup.find_all('td', class_='r')
        data_to_write = []
        for i in range(len(soup) - 2):  # we don't need two last parameters (wifi)
            i = soup[i].get_text()
            i = i.replace(u'\xa0', u' ')  # change space to SPACE (I'm just normalizing the string)
            i = i.split()  # separate value from measurement units
            data_to_write.append(float(i.pop(0)))
        data_to_write[3] = round(data_to_write[3] * 100 / 133, 2)  # hPa to mm Hg
        data_to_write.append(datetime.now().strftime('%H:%M:%S'))  # adds time value
        return data_to_write

    def csv_write(self, data_to_write):
        file_path = self.csv_path()
        with open(file_path, 'a', newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(data_to_write)
        logging.debug('Wrote info to the file')
        return None

    def csv_path(self, date=None, new_file=True, bad_tries=0):  # creates new file or show previous
        if date is None:
            date = datetime.now().strftime('%d-%m-%Y')
        file_path = self.prog_path + 'data/' + date + '.csv'
        if (not path.exists(file_path)) or (stat(file_path).st_size == 0):  # check if we have a file
            if new_file:
                logging.debug(f'Create new file: {file_path}')
                with open(file_path, "w", newline='') as csv_file:
                    writer = csv.writer(csv_file, delimiter=',')
                    writer.writerow(['PM2.5', 'PM10', 'Temp', 'Pres', 'Humidity', 'Time'])
                self.delete_old()  # call deleter every time we write new file
            else:
                if bad_tries >= 5:
                    logging.warning('Can NOT find the file, so will create a new one')
                    return self.csv_path()
                else:
                    bad_tries += 1
                    logging.debug("Didn't find anything, try previous date")
                    return self.csv_path(self.previous_date(date), new_file=False, bad_tries=bad_tries)
        return file_path

    def read_last(self):  # reads last data
        date = datetime.now().strftime('%d-%m-%Y')
        file_path = self.csv_path(date=date, new_file=False)  # the name of file we will read
        logging.debug(f'Reading file: {file_path}')
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)  # read the file as csv table
            read_list = list(reader)
        return read_list[-1]

    def read_csv(self, parameter: str, minutes: int, date=None, previous_data=None, previous_time=None):
        # returns last _minutes_ values
        data_to_graph = []
        time_to_graph = []
        if date is None:
            date = datetime.now().strftime('%d-%m-%Y')
        file_path = self.csv_path(date=date, new_file=False)  # the name of file we will read
        logging.debug(f'Reading file: {file_path}')
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

    def read_all_csv(self, parameter: str, date: str):  # returns all data for one day
        data_to_graph = []
        time_to_graph = []
        file_path = self.csv_path(date=date, new_file=False)
        logging.debug(f'Reading all file: {file_path}')
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)  # read the file as csv table
            read_list = list(reader)
        for i in range(len(read_list)):  # read all the data
            data_to_graph.append(
                float(read_list[i][parameter])
            )
            time_to_graph.append(
                read_list[i]['Time']
            )
        return {'data': data_to_graph, 'time': time_to_graph}

    def read_month(self, parameter: str):  # returns min and max for every saved day (file)
        files = self.dates()
        max_list = []
        min_list = []
        for i in files:
            read_day = self.read_all_csv(parameter, i)
            max_list.append(max(read_day['data']))
            min_list.append(min(read_day['data']))
        return {'min': min_list, 'max': max_list, 'dates': files}

    @staticmethod
    def plot_minutes(data, parameter):  # plots a graph for x last minutes (x should be <100)
        if data is None:
            logging.error("Can't plot the graph, no data!")
            return None
        minutes = data['time']
        time_local = []
        for i in minutes:
            time_local.append(
                datetime.strptime(i, '%H:%M:%S')
            )
        data = data['data']
        data_formatter = DateFormatter('%H:%M')
        plt.plot(time_local, data, marker='.')
        plt.gcf().autofmt_xdate()
        ax = plt.gca()  # gca stands for 'get current axis'
        ax.xaxis.set_major_formatter(data_formatter)
        all_labels = ax.xaxis.get_ticklabels()
        labels_count = len(all_labels)
        if labels_count > 15:
            for i in range(1, labels_count, 2):
                all_labels[i].set_visible(False)
        if labels_count > 30:
            for i in range(2, labels_count, 4):
                all_labels[i].set_visible(False)
        plt.xlabel('Время')
        if parameter == 'PM2.5':
            plt.ylabel('Частицы PM2.5, мкгр/м³')
        elif parameter == 'PM10':
            plt.ylabel('Частицы PM10, мкгр/м³')
        elif parameter == 'Temp':
            plt.ylabel('Температура, °C')
        elif parameter == 'Pres':
            plt.ylabel('Давление, мм/рт.ст.')
            plt.ylim(bottom=700)
        elif parameter == 'Humidity':
            plt.ylabel('Влажность, %')
        else:
            logging.error('Parameter is wrong!')
            return None
        plt.title('Данные метеостанции в Точке Кипения г.Троицк')
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        buffer = buf.getvalue()
        buf.close()
        plt.close()
        return buffer

    def plot_three_hours(self, data, parameter):  # counts average of three nearest points and uses plot_minutes then
        if data is None:
            logging.error("Can't plot the graph, no data!")
            return None
        minutes_temp = data['time']
        data_temp = data['data']
        data_to_graph = []
        minutes_to_graph = []
        for i in range(2, len(data_temp), 3):
            avg = round((data_temp[i-2]+data_temp[i-1]+data_temp[i])/3, 2)
            data_to_graph.append(avg)
            minutes_to_graph.append(minutes_temp[i-1])
        data_return = dict(data=data_to_graph, time=minutes_to_graph)
        return self.plot_minutes(data_return, parameter)

    @staticmethod
    def plot_day(data: dict, parameter: str):  # plots graph of a day with min and max for four time periods
        if data is None:
            logging.error("Can't plot the graph, no data!")
            return None
        minutes = data['time']
        data = data['data']
        four_am = time(4, 0, 0)
        ten_am = time(10, 0, 0)
        four_pm = time(16, 0, 0)
        ten_pm = time(22, 0, 0)
        twelve_pm = time(0, 0, 0)
        q1, q2, q3, q4 = [], [], [], []
        for i in range(len(minutes)):
            time_temp = minutes[i].split(':')
            time_temp = time(int(time_temp[0]), int(time_temp[1]), int(time_temp[2]))
            if four_am <= time_temp < ten_am:
                q1.append(float(data[i]))  # morning
            elif ten_am <= time_temp < four_pm:
                q2.append(float(data[i]))  # day
            elif four_pm <= time_temp < ten_pm:
                q3.append(float(data[i]))  # evening
            elif ten_pm <= time_temp or twelve_pm <= time_temp < four_am:
                q4.append(float(data[i]))  # night
        if not q1 or not q2 or not q3 or not q4:  # if we have no data for time period in this file
            return None
        y1 = [min(q1), min(q2), min(q3), min(q4)]
        y2 = [max(q1), max(q2), max(q3), max(q4)]
        x = ['Утро', 'День', 'Вечер', 'Ночь']
        min_bar = plt.bar(x=x, height=y1, color='blue', width=-0.3, align='edge', label='Минимум')
        max_bar = plt.bar(x=x, height=y2, color='orange', width=0.3, align='edge', label='Максимум')
        if parameter == 'PM2.5':
            plt.ylabel('Частицы PM2.5, мкгр/м³')
        elif parameter == 'PM10':
            plt.ylabel('Частицы PM10, мкгр/м³')
        elif parameter == 'Temp':
            plt.ylabel('Температура, °C')
        elif parameter == 'Pres':
            plt.ylabel('Давление, мм/рт.ст.')
            plt.ylim(bottom=700)
        elif parameter == 'Humidity':
            plt.ylabel('Влажность, %')
        else:
            logging.error('Parameter is wrong!')
            return None
        plt.legend([min_bar, max_bar], ['Минимум', 'Максимум'],
                   bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
                   ncol=2, mode="expand", borderaxespad=0.)
        plt.xlabel('Время суток')
        plt.title('Данные метеостанции в Точке Кипения г.Троицк', pad=27)
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        buffer = buf.getvalue()
        buf.close()
        plt.close()
        return buffer

    @staticmethod
    def plot_month(data: dict, parameter: str):  # plots month graph with min and max values of a day
        if data is None:
            logging.error("Can't plot the graph, no data!")
            return None
        min_list = data['min']
        max_list = data['max']
        dates = data['dates']
        min_line, = plt.plot(dates, min_list, marker='.', color='blue', label='Минимум')
        max_line, = plt.plot(dates, max_list, marker='.', color='orange', label='Максимум')
        plt.gcf().autofmt_xdate()
        ax = plt.gca()  # gca stands for 'get current axis'
        all_labels = ax.xaxis.get_ticklabels()
        labels_count = len(all_labels)
        if labels_count > 15:
            for i in range(1, labels_count, 2):
                all_labels[i].set_visible(False)
        plt.xlabel('Дни')
        if parameter == 'PM2.5':
            plt.ylabel('Частицы PM2.5, мкгр/м³')
        elif parameter == 'PM10':
            plt.ylabel('Частицы PM10, мкгр/м³')
        elif parameter == 'Temp':
            plt.ylabel('Температура, °C')
        elif parameter == 'Pres':
            plt.ylabel('Давление, мм/рт.ст.')
            plt.ylim(bottom=700)
        elif parameter == 'Humidity':
            plt.ylabel('Влажность, %')
        else:
            logging.error('Parameter is wrong!')
            return None
        plt.legend([min_line, max_line], ['Минимум', 'Максимум'],
                   bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
                   ncol=2, mode="expand", borderaxespad=0.)
        plt.title('Данные метеостанции в Точке Кипения г.Троицк', pad=27)
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        buffer = buf.getvalue()
        buf.close()
        plt.close()
        return buffer

    def dates(self):  # returns all the files in dates order
        if name == 'nt':
            files = listdir(self.prog_path+'\\data')
        else:
            files = listdir(self.prog_path+'/data')

        # delete .csv from file name + delete today file
        files = [i[0:-4] for i in files if i != datetime.now().strftime('%d-%m-%Y')+'.csv']
        temp_list = []
        for i in files:
            temp = i.split('-')
            temp = datetime(int(temp[2]), int(temp[1]), int(temp[0]))  # make all dates datetime objects to sort them
            temp_list.append(temp)
        files = temp_list
        files.sort()
        files = [i.strftime('%d-%m-%Y') for i in files]  # and make them strings again
        return files

    @staticmethod
    def previous_date(date: str):  # receives date as 01-01-2020 and returns previous date as 31-12-2019
        date = date.split('-')
        date = datetime(int(date[2]), int(date[1]), int(date[0]))
        date -= timedelta(days=1)
        return date.strftime('%d-%m-%Y')

    def delete_old(self, days_to_save=30, files_num=1):  # deletes old files (calls every time new file creates)
        old_file_date = datetime.now() - timedelta(days=days_to_save)
        one_day_delta = timedelta(days=1)
        for i in range(files_num):
            file_path = self.prog_path + 'data/' + old_file_date.strftime('%d-%m-%Y') + '.csv'
            logging.debug(f'File that should be removed:{file_path}')
            if path.exists(file_path):
                remove(file_path)
                logging.info(f'Removed old file: {file_path}')
            old_file_date -= one_day_delta
