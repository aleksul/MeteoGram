import logging  # TODO use loguru instead

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MinuteLocator, DayLocator
from matplotlib.ticker import NullFormatter
from matplotlib.figure import Figure

from datetime import date, datetime, timedelta

from io import BytesIO

from models import OneMinuteData, PlotData, PlotDayData, PlotMonthData


class Plotter:
    # TODO rewrite plot minutes

    @staticmethod
    def valueToStr(value: str):
        value_dict = {
            "pm25": "Частицы PM2.5",
            "pm10": "Частицы PM10",
            "temperature": "Температура",
            "pressure": "Давление",
            "humidity": "Влажность",
        }
        result = value_dict.get(value)
        if result is None:
            logging.error(f"Can not convert value ({value}) to string!")
        return result

    @staticmethod
    def timeToStr(time: str):
        time_dict = {
            "015": "15 минут",
            "030": "полчаса",
            "060": "1 час",
            "180": "3 часа",
            "day": "день",
            "mon": "месяц",
        }
        result = time_dict.get(time)
        if result is None:
            logging.error(f"Wrong time: {time}")
        return result

    @staticmethod
    def valueToStrWithUnits(value: str) -> str:
        """Translates value

        Args:
            value (str): value to translate

        Raises:
            Exception: value is wrong

        Returns:
            str: translated value
        """
        value_dict = {
            "pm25": "Частицы PM2.5, мкгр/м³",
            "pm10": "Частицы PM10, мкгр/м³",
            "temperature": "Температура, °C",
            "pressure": "Давление, мм/рт.ст.",
            "humidity": "Влажность, %",
        }
        result = value_dict.get(value)
        if result is None:
            logging.error(f"Can not convert value ({value}) to string with units!")
            raise Exception(f"Wrong value ({value})")
        return result

    @staticmethod
    def isValueCorrect(value: str) -> bool:
        """Checks if value is correct.

        Args:
            value (str): value to check

        Raises:
            Exception: value is wrong

        Returns:
            bool: True, if value is correct
        """
        if value not in OneMinuteData.__vars__():
            logging.error(f"Got wrong value ({value})")
            raise Exception("Wrong value")
        return True


class MinutesPlotter(Plotter):

    def __init__(self):
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        # set labels
        self.ax.set_title("Данные метеостанции в Точке Кипения г.Троицк", pad=27)
        self.ax.set_xlabel("Время")
        self.fig.autofmt_xdate()  # rotates xaxis dates tickables for 30*
        # set major formatter to '23:59'
        self.ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))
        ticks_minute = list(range(0, 60, 5))
        self.ax.xaxis.set_major_locator(MinuteLocator(byminute=ticks_minute))
        self.ax.xaxis.set_minor_formatter(NullFormatter())
        every_minute = list(range(0, 60))
        self.ax.xaxis.set_minor_locator(  # TODO test with 'every minute'
            MinuteLocator(byminute=[i for i in every_minute if i not in ticks_minute]))
        # plot
        self.line, = self.ax.plot([], [], marker=".")

    def plot_minutes(self, data: PlotData, value: str) -> bytes:  # TODO add data description
        """Plots a graph for N minutes

        Args:
            data (PlotData): [description]
            value (str): Name of the plotting info

        Returns:
            bytes: Graph photo
        """
        # set new label
        self.ax.set_ylabel(self.valueToStrWithUnits(value))
        if len(data.values) > 100:
            return self._plot_lots_of_minutes(data, value)
        # set new data
        self.line.set_data(data.time, data.values)

        # redraw
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()
        # save
        notFile = BytesIO()
        self.fig.savefig(notFile, format="png")
        notFile.seek(0)
        buffer = notFile.getvalue()
        notFile.close()
        plt.close()
        return buffer

    def _plots_lots_of_minutes(self, data: PlotData, value: str) -> bytes:
        '''
        data_temp = convertedData
            minutes_temp = _time
            convertedData = []
            _time = []
            for i in range(2, len(data_temp), 3):
                # counts averange of three nearest points
                convertedData.append(
                    round((data_temp[i - 2] + data_temp[i - 1] + data_temp[i]) / 3, 2))
                _time.append(minutes_temp[i - 1])
        '''
        '''
        elif labels_count <= 180:
            ticks_minute = list(range(0, 60, 10))
            ax.xaxis.set_major_locator(MinuteLocator(byminute=ticks_minute))
            ax.xaxis.set_minor_formatter(NullFormatter())
            every_minute = list(range(0, 60, 2))
            ax.xaxis.set_minor_locator(
                MinuteLocator(byminute=[i for i in every_minute if i not in ticks_minute]))
        '''
        pass


class DayPlotter(Plotter):

    def __init__(self):
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Данные метеостанции в Точке Кипения г.Троицк", pad=27)
        self.ax.set_xlabel("Время суток")
        x = ["Утро", "День", "Вечер", "Ночь"]
        self.min_bar = self.ax.bar(x=x,
                                   height=[1, 1, 1, 1],
                                   color="blue",
                                   width=-0.3,
                                   align="edge",
                                   label="Минимум")
        self.max_bar = self.ax.bar(x=x,
                                   height=[1, 1, 1, 1],
                                   color="orange",
                                   width=0.3,
                                   align="edge",
                                   label="Максимум")
        self.ax.legend(
            [self.min_bar, self.max_bar],
            ["Минимум", "Максимум"],
            bbox_to_anchor=(0.0, 1.02, 1.0, 0.102),
            loc="lower left",
            ncol=2,
            mode="expand",
            borderaxespad=0.0,
        )

    def plot_day(self, data: PlotDayData, value: str) -> bytes:  # TODO add data description
        """Plots graph of a day with min and max for four time periods

        Args:
            data (PlotDayData): [description]
            value (str): Name of the plotting info

        Returns:
            bytes: graph photo
        """
        # set new label
        self.ax.set_ylabel(self.valueToStrWithUnits(value))
        # find max and min per day
        maximum = max(
            [data.morning.maximum, data.noon.maximum, data.evening.maximum, data.night.maximum])
        minimum = min(
            [data.morning.minimum, data.noon.minimum, data.evening.minimum, data.night.minimum])
        # set new data
        self.min_bar.patches[0].set_height(data.morning.minimum)
        self.min_bar.patches[1].set_height(data.noon.minimum)
        self.min_bar.patches[2].set_height(data.evening.minimum)
        self.min_bar.patches[3].set_height(data.night.minimum)
        self.max_bar.patches[0].set_height(data.morning.maximum)
        self.max_bar.patches[1].set_height(data.noon.maximum)
        self.max_bar.patches[2].set_height(data.evening.maximum)
        self.max_bar.patches[3].set_height(data.night.maximum)
        # set limits
        if value == "pm25" or value == "pm10":
            self.ax.set_ylim(bottom=0, top=maximum + 1)
        elif value == "temperature":
            self.ax.set_ylim(bottom=minimum - 1, top=maximum + 1)
        elif value == "pressure" or value == "humidity":
            self.ax.set_ylim(bottom=minimum - 3, top=maximum + 3)
        # redraw
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()
        # save
        notFile = BytesIO()
        self.fig.savefig(notFile, format='png')
        notFile.seek(0)
        buffer = notFile.getvalue()
        notFile.close()
        plt.close()
        return buffer


class MonthPlotter(Plotter):

    def __init__(self):
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.grid()
        self.ax.set_title("Данные метеостанции в Точке Кипения г.Троицк", pad=27)
        self.ax.set_xlabel("Дни")
        self.fig.autofmt_xdate()  # rotates xaxis dates tickables for 30*
        self.ax.xaxis.set_major_formatter(DateFormatter("%d.%m.%y"))
        self.ax.xaxis.set_major_locator(DayLocator(interval=2))
        self.ax.xaxis.set_minor_locator(DayLocator())
        self.min_line, = self.ax.plot([], [], marker=".", color="blue", label="Минимум")
        self.max_line, = self.ax.plot([], [], marker=".", color="orange", label="Максимум")
        self.ax.legend(
            [self.min_line, self.max_line],
            ["Минимум", "Максимум"],
            bbox_to_anchor=(0.0, 1.02, 1.0, 0.102),
            loc="lower left",
            ncol=2,
            mode="expand",
            borderaxespad=0.0,
        )

    def plot_month(self, data: PlotMonthData, value: str) -> bytes:  # TODO add data description
        """Plots month graph with min and max values of the day

        Args:
            data (PlotMonthData): [description]
            value (str): Name of the plotting info

        Returns:
            bytes: graph photo
        """
        # set new label
        self.ax.set_ylabel(self.valueToStrWithUnits(value))
        # set new data
        self.min_line.set_data(data.dates, data.minimum)
        self.max_line.set_data(data.dates, data.maximum)
        # redraw
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()
        # save
        notFile = BytesIO()
        self.fig.savefig(notFile, format="png")
        notFile.seek(0)
        buffer = notFile.getvalue()
        notFile.close()
        return buffer
