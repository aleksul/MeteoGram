import logging

from asyncio import run as async_run

from tortoise import Tortoise, fields
from tortoise.models import Model
from tortoise.functions import Min, Max
from tortoise.query_utils import Q

from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MinuteLocator, DayLocator
from matplotlib.ticker import NullFormatter

from datetime import datetime, timedelta, time, date

from io import BytesIO
from typing import IO
from tempfile import NamedTemporaryFile


class OneMinuteData(Model):
    id = fields.IntField(pk=True)
    pm25 = fields.FloatField()
    pm10 = fields.FloatField()
    temperature = fields.FloatField()
    pressure = fields.FloatField()
    humidity = fields.FloatField()
    time = fields.DatetimeField()
    
    def __str__(self):
        return self.time.strftime("%H:%M:%S %d %b %Y")
    
    @staticmethod
    def __vars__():
        return ['id', 'pm25', 'pm10', 'temperature', 'pressure', 'humidity', 'time']
    
    class Meta:
        table = 'weather'


class Plotter:
    def plot_minutes(self, data: list, value: str) -> bytes:  # plots a graph for x last minutes
        assert data, 'Can NOT plot graph (minutes): data list is empty'
        self.isValueCorrect(value)
        converted = defaultdict(list)
        {converted[key].append(sub[key]) for sub in data for key in sub}  # turns list of dicts to dict of lists
        convertedData = converted[value]
        _time = converted['time']
        labels_count = len(convertedData)  # counts how much points we have to know time-step
        if labels_count > 100:
            data_temp = convertedData
            minutes_temp = _time
            convertedData = []
            _time = []
            for i in range(2, len(data_temp), 3):  # counts averange of three nearest points
                convertedData.append(round((data_temp[i - 2] + data_temp[i - 1] + data_temp[i]) / 3, 2))
                _time.append(minutes_temp[i - 1])
        plt.plot(_time, convertedData, marker='.')
        plt.xlim(left=_time[0] + timedelta(minutes=1),
                 right=_time[-1] - timedelta(minutes=1))  # invert x axis + add extra space on y-axis
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
        plt.ylabel(self.valueToStrWithUnits(value))
        ax.set_autoscale_on(True)
        plt.title('Данные метеостанции в Точке Кипения г.Троицк')
        notFile = BytesIO()
        plt.savefig(notFile, format='png')
        notFile.seek(0)
        buffer = notFile.getvalue()
        notFile.close()
        plt.close()
        return buffer

    def plot_day(self, data: dict, value: str) -> bytes:  # plots graph of a day with min and max for four time periods
        assert data, 'Can NOT plot graph (day): data dict is empty'
        self.isValueCorrect(value)
        y1 = [data['morning']['min'], data['day']['min'], data['evening']['min'], data['night']['min']]
        y2 = [data['morning']['max'], data['day']['max'], data['evening']['max'], data['night']['max']]
        x = ['Утро', 'День', 'Вечер', 'Ночь']
        min_bar = plt.bar(x=x, height=y1, color='blue', width=-0.3, align='edge', label='Минимум')
        max_bar = plt.bar(x=x, height=y2, color='orange', width=0.3, align='edge', label='Максимум')
        plt.ylabel(self.valueToStrWithUnits(value))
        if value == 'pm25':
            plt.ylim(bottom=0, top=max(y2) + 1)
        elif value == 'pm10':
            plt.ylim(bottom=0, top=max(y2) + 1)
        elif value == 'temperature':
            plt.ylim(bottom=min(y1) - 1, top=max(y2) + 1)
        elif value == 'pressure':
            plt.ylim(bottom=min(y1) - 3, top=max(y2) + 3)
        elif value == 'humidity':
            plt.ylim(bottom=min(y1) - 3, top=max(y2) + 3)
        plt.gca().set_autoscale_on(True)
        plt.legend([min_bar, max_bar], ['Минимум', 'Максимум'],
                   bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
                   ncol=2, mode="expand", borderaxespad=0.)
        plt.xlabel("Время суток")
        plt.title('Данные метеостанции в Точке Кипения г.Троицк', pad=27)
        notFile = BytesIO()
        plt.savefig(notFile, format='png')
        notFile.seek(0)
        buffer = notFile.getvalue()
        notFile.close()
        plt.close()
        return buffer

    def plot_month(self, data: list, value: str) -> bytes:  # plots month graph with min and max values of a day
        assert data, 'Can NOT plot graph (month): data list is empty'
        self.isValueCorrect(value)
        converted = defaultdict(list) 
        {converted[key].append(sub[key]) for sub in data for key in sub}  # turns list of dicts to dict of lists
        # converted == {'date': [date1, date2, etc], 'min': [min1, min2, etc], 'max': [max1, max2, etc]}
        min_line, = plt.plot(converted['date'], converted['min'], marker='.',
                             color='blue', label='Минимум')
        max_line, = plt.plot(converted['date'], converted['max'], marker='.',
                             color='orange', label='Максимум')
        plt.gcf().autofmt_xdate()
        ax = plt.gca()  # gca stands for 'get current axis'
        ax.xaxis.set_major_formatter(DateFormatter('%d.%m.%y'))
        ax.xaxis.set_major_locator(DayLocator(interval=2))
        if len(converted['date']) <= 5:
            ax.xaxis.set_major_locator(DayLocator(interval=1))
        ax.xaxis.set_minor_locator(DayLocator())
        plt.xlabel('Дни')
        plt.ylabel(self.valueToStrWithUnits(value))
        ax.set_autoscale_on(True)
        plt.legend([min_line, max_line], ['Минимум', 'Максимум'],
                   bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
                   ncol=2, mode="expand", borderaxespad=0.)
        plt.title('Данные метеостанции в Точке Кипения г.Троицк', pad=27)
        notFile = BytesIO()
        plt.savefig(notFile, format='png')
        notFile.seek(0)
        buffer = notFile.getvalue()
        notFile.close()
        plt.close()
        return buffer

    @staticmethod
    def valueToStr(value: str):
        value_dict = {'pm25': 'Частицы PM2.5', 
                          'pm10': 'Частицы PM10', 
                          'temperature': 'Температура', 
                          'pressure': 'Давление', 
                          'humidity': 'Влажность'
                          }
        result = value_dict.get(value)
        if result is None:
            logging.error(f'Can not convert value ({value}) to string!')
        return result

    @staticmethod
    def timeToStr(time: str):
        time_dict = {'015': '15 минут', 
                     '030': 'полчаса', 
                     '060': '1 час', 
                     '180': '3 часа', 
                     'day': 'день', 
                     'mon': 'месяц'
                     }
        result = time_dict.get(time)
        if result is None:
            logging.error(f'Wrong time: {time}')
        return result
    
    @staticmethod
    def valueToStrWithUnits(value: str):
        value_dict = {'pm25': 'Частицы PM2.5, мкгр/м³', 
                      'pm10': 'Частицы PM10, мкгр/м³', 
                      'temperature': 'Температура, °C', 
                      'pressure': 'Давление, мм/рт.ст.', 
                      'humidity': 'Влажность, %'
                      }
        result = value_dict.get(value)
        if result is None:
            logging.error(f'Can not convert value ({value}) to string with units!')
            raise Exception(f'Wrong value ({value})')
        return result

    @staticmethod
    def isValueCorrect(value: str) -> bool:  # checks if passed value is correct
        if value not in OneMinuteData.__vars__():
            logging.error(f'Got wrong value ({value})')
            raise Exception("Wrong value")
        return True
        

class DatabaseHandler:
    def __init__(self, db_path: str):
        self.DB_PATH = db_path
        async_run(Tortoise.init(db_url=self.DB_PATH,
                                modules={'models': ['plotter']}
                                ))

    @staticmethod
    def isValueCorrect(value: str) -> bool:  # checks if passed value is correct
        if value not in OneMinuteData.__vars__():
            logging.error(f'Got wrong value ({value})')
            raise Exception("Wrong value")
        return True

    async def getDataByTimedelta(self, start_point: datetime, delta: timedelta, value: str) -> list:  # returns data by timedelta
        self.isValueCorrect(value)
        result: list
        if delta >= timedelta():
            result = await OneMinuteData.filter(time__gte=start_point, time__lte=start_point+delta).values(value, 'time')
        else:
            result = await OneMinuteData.filter(time__gte=start_point+delta, time__lte=start_point).values(value, 'time')
        assert result, 'Recieved nothing from database (getDataByTimedelta)'
        return result
    
    async def getDataByDay(self, day: date, value: str) -> dict:  # devides day in parts, than collect min and max for all of them
        self.isValueCorrect(value)
        four_am = datetime.combine(day, time(4, 0, 0))
        ten_am = datetime.combine(day, time(10, 0, 0))
        four_pm = datetime.combine(day, time(16, 0, 0))
        ten_pm = datetime.combine(day, time(22, 0, 0))
        twelve_pm = datetime.combine(day, time(0, 0, 0))
        twelve_pm_next_day = twelve_pm + timedelta(days=1)
        dayByParts = {
            'morning': await OneMinuteData.filter(time__gte=four_am, time__lt=ten_am).first(),
            'day':     await OneMinuteData.filter(time__gte=ten_am, time__lt=four_pm).first(),
            'evening': await OneMinuteData.filter(time__gte=four_pm, time__lt=ten_pm).first(),
            'night':   await OneMinuteData.filter(Q(time__gte=twelve_pm, time__lt=four_am) | 
                                                  Q(time__gte=ten_pm, time__lte=twelve_pm_next_day)).first()
        }
        for key in dayByParts.keys():
            assert dayByParts[key] is not None, 'Received nothing from database (getDataByDay)'
            t1 = await dayByParts[key].annotate(max=Max(value)).values('max')
            t2 = await dayByParts[key].annotate(min=Min(value)).values('min')
            dayByParts[key] = t1[0]
            dayByParts[key].update(t2[0])
        return dayByParts
    
    async def getRawDataByDay(self, day: date) -> IO:  # creates .csv file with all day data
        start = datetime.combine(day, time(0, 0, 0))
        end = start + timedelta(days=1)
        values = await OneMinuteData.filter(time__gte=start, time__lte=end).values_list()
        assert values, 'Recieved nothing from database (getRawDataByDay)'
        with NamedTemporaryFile(delete=False) as f:
            f.write(b'ID,PM2.5,PM10,Temperature,Pressure,Humidity,Time\n')
            for line in values:
                stroka = ''
                for value in line:
                    if type(value) is datetime:
                        value = value.time()
                    stroka += str(value)+','
                stroka = stroka[0:-1]+'\n'
                f.write(bytes(stroka, 'utf-8'))
        return f
    
    async def getLastData(self) -> dict:  # returns last written data
        result = await OneMinuteData.annotate(last=Max('id')).values()
        result = result[0]
        result.pop('id', None); result.pop('last', None)
        assert result is not None, 'Recieved nothing from database (getLastData)'
        return result
    
    async def getAllDates(self, includeToday = False) -> list:  # returns list of all saved day's
        start_day = date.today()
        result = []
        if includeToday:
            now = datetime.now()
            if now.hour == 0 and now.minute <= 1:  # time less than 0:01, simply no info for today
                start_day -= timedelta(days=1)
        else:
            start_day -= timedelta(days=1)
        before, after = datetime.combine(start_day, time(0, 0, 0)), datetime.combine(start_day, time(23, 59, 59))
        flag = await OneMinuteData.exists(time__gte=before, time__lte=after)
        while flag:
            result.append(after.date())
            before -= timedelta(days=1)
            after -= timedelta(days=1)
            flag = await OneMinuteData.exists(time__gte=before, time__lte=after)
        return result
    
    async def getMonthData(self, value: str) -> list:  # returns min and max for every saved day
        self.isValueCorrect(value)
        result = []
        dates = await self.getAllDates()
        if len(dates) > 30:
            dates = dates[0:30]
        for _date in dates:
            day_start = datetime.combine(_date, time(0, 0, 0))
            day_end = datetime.combine(_date, time(23, 59, 59))
            day_data = await OneMinuteData.filter(time__gte=day_start, time__lte=day_end).first()
            t1 = await day_data.annotate(max=Max(value)).values('max')
            t2 = await day_data.annotate(min=Min(value)).values('min')
            day = {'date': _date}
            day.update(t1[0])
            day.update(t2[0])
            result.append(day)
        assert result is not None, 'Recieved nothing from database (getMonthData)'
        return result
