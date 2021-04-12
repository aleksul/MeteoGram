import logging  # TODO use loguru instead

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MinuteLocator, DayLocator
from matplotlib.ticker import NullFormatter
from matplotlib.figure import Figure

from io import BytesIO

from models import PlotData, PlotDayData, PlotMonthData

trans_values = {
    "pm25": "Частицы PM2.5",
    "pm10": "Частицы PM10",
    "temperature": "Температура",
    "pressure": "Давление",
    "humidity": "Влажность",
}
trans_values_and_units = {
    "pm25": "Частицы PM2.5, мкгр/м³",
    "pm10": "Частицы PM10, мкгр/м³",
    "temperature": "Температура, °C",
    "pressure": "Давление, мм/рт.ст.",
    "humidity": "Влажность, %",
}


class MinutesPlotter:

    def __init__(self):
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        # set labels
        self.ax.set_title("Данные метеостанции в Точке Кипения г.Троицк", pad=27)
        self.ax.set_xlabel("Время")
        self.fig.autofmt_xdate()  # rotates xaxis dates tickables for 30*
        # set major formatter to '23:59'
        self.ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))
        self.ax.xaxis.set_major_locator(MinuteLocator(byminute=list(range(0, 60, 5))))
        self.ax.xaxis.set_minor_formatter(NullFormatter())
        self.ax.xaxis.set_minor_locator(MinuteLocator(byminute=list(range(0, 60))))
        # plot
        self.line, = self.ax.plot([], [], marker=".")

    def plot_minutes(self, data: PlotData) -> bytes:
        """Plots a graph for N (3 < N < 330) minutes

        Args:
            data (PlotData): pydantic model - contains values, time for them and valueName

        Returns:
            bytes: Graph photo
        """
        # set new label
        self.ax.set_ylabel(self.valueToStr(data.valueName, with_units=True))
        # compress values
        if len(data.values) > 100:
            i = data.values
            t = data.time
            if len(data.values) < 180:  # compress level 1
                data.values = [(i[n - 2] + i[n - 1] + i[n]) / 3 for n in range(3, len(i), 3)]
                data.time = [t[n] for n in range(2, len(t), 3)]
                self._change_locator_mode(2)
            elif len(data.values) < 330:  # compress level 2
                data.values = [(i[n - 4] + i[n - 3] + i[n - 2] + i[n - 1] + i[n]) / 5
                               for n in range(5, len(i), 5)]
                data.time = [t[n] for n in range(3, len(t), 5)]
                self._change_locator_mode(3)
            else:
                raise ValueError("Too much values")
        else:
            self._change_locator_mode(1)
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

    def _change_locator_mode(self, mode: int) -> None:
        """Changes figure's locator

        Args:
            mode (int): from 1 to 3. Locator selecter
        """
        assert mode in [1, 2, 3], 'Select mode from 1-3'
        if mode == 1:
            self.ax.xaxis.set_major_locator(MinuteLocator(byminute=list(range(0, 60, 5))))
            self.ax.xaxis.set_minor_locator(MinuteLocator(byminute=list(range(0, 60))))
        elif mode == 2:
            self.ax.xaxis.set_major_locator(MinuteLocator(byminute=list(range(0, 60, 10))))
            self.ax.xaxis.set_minor_locator(MinuteLocator(byminute=list(range(0, 60, 2))))
        elif mode == 3:
            self.ax.xaxis.set_major_locator(MinuteLocator(byminute=list(range(0, 60, 15))))
            self.ax.xaxis.set_minor_locator(MinuteLocator(byminute=list(range(0, 60, 3))))


class DayPlotter:

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

    def plot_day(self, data: PlotDayData) -> bytes:
        """Plots graph of a day with min and max for four time periods

        Args:
            data (PlotDayData): pydantic model - contains all day parts, value name and date

        Returns:
            bytes: graph photo
        """
        # set new label
        self.ax.set_ylabel(self.valueToStr(data.valueName, with_units=True))
        # find max and min per day
        maximum = max(
            (data.morning.maximum, data.noon.maximum, data.evening.maximum, data.night.maximum))
        minimum = min(
            (data.morning.minimum, data.noon.minimum, data.evening.minimum, data.night.minimum))
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
        if data.valueName == "pm25" or data.valueName == "pm10":
            self.ax.set_ylim(bottom=0, top=maximum + 1)
        elif data.valueName == "temperature":
            self.ax.set_ylim(bottom=minimum - 1, top=maximum + 1)
        elif data.valueName == "pressure" or data.valueName == "humidity":
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


class MonthPlotter:

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

    def plot_month(self, data: PlotMonthData) -> bytes:
        """Plots month graph with min and max values of the day

        Args:
            data (PlotMonthData): pydantic model - contains all dates and max/min for them,
            as well as value name

        Returns:
            bytes: graph photo
        """
        # set new label
        self.ax.set_ylabel(self.valueToStr(data.valueName, with_units=True))
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


class Plotter(MinutesPlotter, DayPlotter, MonthPlotter):

    @staticmethod
    def valueToStr(value: str, with_units=False) -> str:
        """Translates value

        Args:
            value (str): value to convert
            with_units (bool, optional): to use measurment units or not. Defaults to False.

        Raises:
            ValueError: value is wrong

        Returns:
            str: translated value
        """
        global trans_values, trans_values_and_units
        if not with_units:
            result = trans_values.get(value)
        else:
            result = trans_values_and_units.get(value)
        if result is None:
            logging.error(f"Can not convert value ({value}) to string!")
            raise ValueError(f"Wrong value ({value})")
        return result
