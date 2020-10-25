import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MinuteLocator, DayLocator
from matplotlib.ticker import NullFormatter
import csv
import logging
from datetime import datetime, timedelta, time, date
from os import path, stat, listdir
from io import BytesIO


class Plotter:
    def __init__(self, data_path='/'):
        self.data_path = data_path

    def csv_path(self, date_local=None, tries=5):  # creates new file or show previous
        if date_local is None:
            date_local = datetime.now().strftime('%d-%m-%Y')
        file_path = self.data_path + date_local + '.csv'
        if (not path.exists(file_path)) or (stat(file_path).st_size == 0):  # check if we have a file
            if tries <= 0:
                logging.error('Can NOT find the file')
                raise FileNotFoundError("Can't find .csv file")
            else:
                tries -= 1
                logging.debug("Didn't find anything, try previous date")
                return self.csv_path(date_local=self.previous_date(date_local), tries=tries)
        return file_path

    def read_last(self):  # reads last data
        file_path = self.csv_path()  # the name of file we will read
        logging.debug(f'Reading file: {file_path}')
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)  # read the file as csv table
            read_list = list(reader)
        return read_list[-1]

    def read_csv_timedelta(self, parameter: str, start: datetime, end: datetime):
        if parameter not in ['PM2.5', 'PM10', 'Temp', 'Pres', 'Humidity']:
            logging.error(f'Parameter is wrong: {parameter}')
            return None
        if end > start:
            start, end = end, start
        date1 = start.date()
        date2 = end.date()
        files_to_read = [date1.strftime('%d-%m-%Y') + '.csv']
        one_day = timedelta(days=1)
        while date1 - date2 >= one_day:
            date1 -= one_day
            files_to_read.append(date1.strftime('%d-%m-%Y') + '.csv')
        all_files = listdir(self.data_path)
        for file in files_to_read:
            if file not in all_files:
                logging.error(f'Can not build the graph because we do not have file: {file}')
                return None
        data_to_graph = []
        time_to_graph = []
        for file in files_to_read:
            reading_file = self.data_path + file
            with open(reading_file, 'r') as f:
                read = list(csv.DictReader(f))  # read the file as csv table
            read.reverse()
            for temp in read:
                temp_datetime = datetime.strptime(file[0:-4] + '-' + temp['Time'], '%d-%m-%Y-%H:%M:%S')
                if start >= temp_datetime >= end:
                    data_to_graph.append(float(temp[parameter]))
                    time_to_graph.append(temp_datetime)
        return {'data': data_to_graph, 'time': time_to_graph}

    def read_month(self, parameter: str):  # returns min and max for every saved day (file)
        files = self.dates()
        max_list = []
        min_list = []
        dates = []
        for file in files:
            file = file.split('-')
            file = [int(i) for i in file]
            date1 = datetime(file[2], file[1], file[0], 0, 0, 0)
            date2 = datetime(file[2], file[1], file[0], 23, 59, 59)
            dates.append(date(file[2], file[1], file[0]))
            read_day = self.read_csv_timedelta(parameter, date1, date2)
            max_list.append(max(read_day['data']))
            min_list.append(min(read_day['data']))
        return {'min': min_list, 'max': max_list, 'dates': dates}

    @staticmethod
    def plot_minutes(data, parameter):  # plots a graph for x last minutes
        time_local = data['time']
        data = data['data']
        labels_count = len(data)  # counts how much points we have to know time-step
        if labels_count > 100:
            data_temp = data
            minutes_temp = time_local
            data = []
            time_local = []
            for i in range(2, len(data_temp), 3):  # counts averange of three nearest points
                data.append(round((data_temp[i - 2] + data_temp[i - 1] + data_temp[i]) / 3, 2))
                time_local.append(minutes_temp[i - 1])
        plt.plot(time_local, data, marker='.')
        plt.xlim(left=time_local[0] + timedelta(minutes=1),
                 right=time_local[-1] - timedelta(minutes=1))  # invert x axis + add extra space on y-axis
        plt.gcf().autofmt_xdate()  # rotate the date
        ax = plt.gca()  # gca stands for 'get current axis'
        ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))  # sets major formatter to '23:59'
        if labels_count <= 15:
            ax.xaxis.set_major_locator(MinuteLocator(byminute=range(60)))
        elif labels_count <= 30:
            ax.xaxis.set_major_locator(MinuteLocator(byminute=range(0, 60, 2)))
            ax.xaxis.set_minor_formatter(NullFormatter())
            ax.xaxis.set_minor_locator(MinuteLocator(byminute=range(1, 60, 2)))
        elif labels_count <= 60:
            ticks_minute = list(range(0, 60, 5))
            ax.xaxis.set_major_locator(MinuteLocator(byminute=ticks_minute))
            ax.xaxis.set_minor_formatter(NullFormatter())
            every_minute = list(range(0, 60))
            ax.xaxis.set_minor_locator(MinuteLocator(
                byminute=[i for i in every_minute if i not in ticks_minute]))
        elif labels_count <= 180:
            ticks_minute = list(range(0, 60, 10))
            ax.xaxis.set_major_locator(MinuteLocator(byminute=ticks_minute))
            ax.xaxis.set_minor_formatter(NullFormatter())
            every_minute = list(range(0, 60))
            ax.xaxis.set_minor_locator(MinuteLocator(
                byminute=[i for i in every_minute if i not in ticks_minute]))
        else:
            logging.error('Wrong label counter!')
            return None
        plt.xlabel('Время')
        if parameter == 'PM2.5':
            plt.ylabel('Частицы PM2.5, мкгр/м³')
        elif parameter == 'PM10':
            plt.ylabel('Частицы PM10, мкгр/м³')
        elif parameter == 'Temp':
            plt.ylabel('Температура, °C')
        elif parameter == 'Pres':
            plt.ylabel('Давление, мм/рт.ст.')
        elif parameter == 'Humidity':
            plt.ylabel('Влажность, %')
        else:
            logging.error('Parameter is wrong!')
            return None
        ax.set_autoscale_on(True)
        plt.title('Данные метеостанции в Точке Кипения г.Троицк')
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        buffer = buf.getvalue()
        buf.close()
        plt.close()
        return buffer

    @staticmethod
    def plot_day(data: dict, parameter: str):  # plots graph of a day with min and max for four time periods
        minutes = data['time']
        data = data['data']
        four_am = time(4, 0, 0)
        ten_am = time(10, 0, 0)
        four_pm = time(16, 0, 0)
        ten_pm = time(22, 0, 0)
        twelve_pm = time(0, 0, 0)
        q1, q2, q3, q4 = [], [], [], []
        for i in range(len(minutes)):
            time_temp = minutes[i].time()
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
            plt.ylim(bottom=0, top=max(y2) + 1)
        elif parameter == 'PM10':
            plt.ylabel('Частицы PM10, мкгр/м³')
            plt.ylim(bottom=0, top=max(y2) + 1)
        elif parameter == 'Temp':
            plt.ylabel('Температура, °C')
            plt.ylim(bottom=min(y1) - 1, top=max(y2) + 1)
        elif parameter == 'Pres':
            plt.ylabel('Давление, мм/рт.ст.')
            plt.ylim(bottom=min(y1) - 3, top=max(y2) + 3)
        elif parameter == 'Humidity':
            plt.ylabel('Влажность, %')
            plt.ylim(bottom=min(y1) - 3, top=max(y2) + 3)
        else:
            logging.error('Parameter is wrong!')
            return None
        plt.gca().set_autoscale_on(True)
        plt.legend([min_bar, max_bar], ['Минимум', 'Максимум'],
                   bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
                   ncol=2, mode="expand", borderaxespad=0.)
        plt.xlabel("Время суток")
        plt.title('Данные метеостанции в Точке Кипения г.Троицк', pad=27)
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        buffer = buf.getvalue()
        buf.close()
        plt.close()
        return buffer

    @staticmethod
    def parameter_to_str(parameter: str):
        if parameter == 'PM2.5':
            return 'Частицы PM2.5'
        elif parameter == 'PM10':
            return 'Частицы PM10'
        elif parameter == 'Temp':
            return 'Температура'
        elif parameter == 'Pres':
            return 'Давление'
        elif parameter == 'Humidity':
            return 'Влажность'
        else:
            logging.error('Parameter is wrong!')
            return None

    @staticmethod
    def plot_month(data: dict, parameter: str):  # plots month graph with min and max values of a day
        min_list = data['min']
        max_list = data['max']
        dates = data['dates']
        if not min_list or not max_list or not dates:
            logging.error("Can't plot month graph, no data!")
            return None
        min_line, = plt.plot(dates, min_list, marker='.',
                             color='blue', label='Минимум')
        max_line, = plt.plot(dates, max_list, marker='.',
                             color='orange', label='Максимум')
        plt.xlim(left=dates[-1] + timedelta(days=1), right=dates[0] - timedelta(days=1))  # invert x axis
        plt.gcf().autofmt_xdate()
        ax = plt.gca()  # gca stands for 'get current axis'
        ax.xaxis.set_major_formatter(DateFormatter('%d.%m.%y'))
        ax.xaxis.set_major_locator(DayLocator(interval=2))
        ax.xaxis.set_minor_locator(DayLocator())
        plt.xlabel('Дни')
        if parameter == 'PM2.5':
            plt.ylabel('Частицы PM2.5, мкгр/м³')
        elif parameter == 'PM10':
            plt.ylabel('Частицы PM10, мкгр/м³')
        elif parameter == 'Temp':
            plt.ylabel('Температура, °C')
        elif parameter == 'Pres':
            plt.ylabel('Давление, мм/рт.ст.')
        elif parameter == 'Humidity':
            plt.ylabel('Влажность, %')
        else:
            logging.error('Parameter is wrong!')
            return None
        ax.set_autoscale_on(True)
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
        files = listdir(self.data_path)
        # delete .csv from file name + delete today file
        files = [i[0:-4] for i in files if i != datetime.now().strftime('%d-%m-%Y') + '.csv']
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
    def previous_date(date_local: str):  # receives date as 01-01-2020 and returns previous date as 31-12-2019
        date_local = date_local.split('-')
        date_local = datetime(int(date_local[2]), int(date_local[1]), int(date_local[0]))
        date_local -= timedelta(days=1)
        return date_local.strftime('%d-%m-%Y')

    @staticmethod
    def time_to_str(time: str):
        if time == '15':
            return 'последние 15 минут'
        elif time == '30':
            return 'последние полчаса'
        elif time == '60':
            return 'последний час'
        elif time == '180':
            return 'последние 3 часа'
        elif time == 'day':
            return 'день'
        elif time == 'month':
            return 'месяц'
        else:
            logging.error(f'Wrong time: {time}')
            return None