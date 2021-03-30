import logging

from asyncio import run as async_run

from tortoise import Tortoise
from tortoise.functions import Min, Max
from tortoise.query_utils import Q

from models import OneMinuteData

from datetime import datetime, timedelta, time, date

from typing import IO
from tempfile import NamedTemporaryFile


class DatabaseHandler:

    def __init__(self, db_path: str):
        self.DB_PATH = db_path
        async_run(Tortoise.init(db_url=self.DB_PATH, modules={"models": ["models"]}))

    @staticmethod
    def isValueCorrect(value: str) -> bool:
        """Checks if passed value is correct

        Args:
            value (str): value to check

        Raises:
            Exception: value is incorrect

        Returns:
            bool: True, if value is correct
        """
        if value not in OneMinuteData.__vars__():
            logging.error(f"Got wrong value ({value})")
            raise Exception("Wrong value")
        return True

    async def getDataByTimedelta(self, start_point: datetime, delta: timedelta, value: str) -> list:
        """Collects data from database in set period

        Args:
            start_point (datetime): When start data collecting
            delta (timedelta): How much to collect
            value (str): Which data are you interested in

        Returns:
            list: data you asked for
        """
        self.isValueCorrect(value)
        result: list
        if delta >= timedelta():  # if delta >= 0
            result = (await OneMinuteData.filter(time__gte=start_point,
                                                 time__lte=start_point +
                                                 delta).order_by("time").values(value, "time"))
        else:
            result = (await OneMinuteData.filter(time__gte=start_point + delta,
                                                 time__lte=start_point).order_by("time").values(
                                                     value, "time"))
        assert result, "Recieved nothing"
        return result

    async def getDataByDay(self, day: date, value: str) -> dict:
        """Collects data from database on a certain day

        Args:
            day (date): The day to collect data
            value (str): Which data are you interested in

        Returns:
            dict: dict of dicts for every day part, each one contains max & min
        """
        self.isValueCorrect(value)
        four_am = datetime.combine(day, time(4, 0, 0))
        ten_am = datetime.combine(day, time(10, 0, 0))
        four_pm = datetime.combine(day, time(16, 0, 0))
        ten_pm = datetime.combine(day, time(22, 0, 0))
        twelve_pm = datetime.combine(day, time(0, 0, 0))
        twelve_pm_next_day = twelve_pm + timedelta(days=1)
        dayByParts = {
            "morning":
                await OneMinuteData.annotate(max=Max(value)).annotate(min=Min(value)).filter(
                    time__gte=four_am, time__lt=ten_am).values("max", "min"),
            "day":
                await OneMinuteData.annotate(max=Max(value)).annotate(min=Min(value)).filter(
                    time__gte=ten_am, time__lt=four_pm).values("max", "min"),
            "evening":
                await OneMinuteData.annotate(max=Max(value)).annotate(min=Min(value)).filter(
                    time__gte=four_pm, time__lt=ten_pm).values("max", "min"),
            "night":
                await OneMinuteData.annotate(max=Max(value)).annotate(min=Min(value)).filter(
                    Q(time__gte=twelve_pm, time__lt=four_am) |
                    Q(time__gte=ten_pm, time__lte=twelve_pm_next_day)).values("max", "min"),
        }
        for key in dayByParts.keys():
            assert dayByParts[key] is not None, "Received nothing"
            dayByParts[key] = dayByParts[key].pop(0)
        return dayByParts

    async def getRawDataByDay(self, day: date) -> IO:
        """Creates .csv file with all day data

        Args:
            day (date): The day to collect data

        Returns:
            IO: .csv file as a bytes object
        """
        start = datetime.combine(day, time(0, 0, 0))
        end = start + timedelta(days=1)
        values = await OneMinuteData.filter(time__gte=start, time__lte=end).values_list(
            "pm25", "pm10", "temperature", "pressure", "humidity", "time")
        assert values, "Recieved nothing"
        with NamedTemporaryFile(delete=False) as f:
            f.write(b"PM2.5,PM10,Temperature,Pressure,Humidity,Time\n")
            for line in values:
                stroka = ""
                for value in line:
                    if type(value) is datetime:
                        value = value.time()
                    stroka += str(value) + ","
                stroka = stroka[0:-1] + "\n"
                f.write(bytes(stroka, "utf-8"))
        return f

    async def getLastData(self) -> dict:
        """Collects last data written to database

        Returns:
            dict: all values
        """
        result = await OneMinuteData.annotate(last=Max("id")).values()
        result = result[0]
        result.pop("id", None)
        result.pop("last", None)
        assert result is not None, "Recieved nothing"
        return result

    async def getAllDates(self, includeToday=False) -> list:
        """Collects which days are written to database

        Args:
            includeToday (bool, optional): If True, starts with today, else starts with yesterday.
            Defaults to False.

        Returns:
            list: list of date objects
        """
        start_day = date.today()
        result = []
        if includeToday:
            now = datetime.now()
            if now.hour == 0 and now.minute <= 1:  # no info for today
                start_day -= timedelta(days=1)
        else:
            start_day -= timedelta(days=1)
        before = datetime.combine(start_day, time(0, 0, 0))
        after = datetime.combine(start_day, time(23, 59, 59))
        while await OneMinuteData.exists(time__gte=before, time__lte=after):
            result.append(after.date())
            before -= timedelta(days=1)
            after -= timedelta(days=1)
        return result

    async def getMonthData(self, value: str) -> dict:
        """Collects min, max and Datetime.date for last 30 saved days

        Args:
            value (str): Value, that needs to be collected from database

        Returns:
            dict: Dict of lists with values
        """
        self.isValueCorrect(value)
        result = {"max": [], "min": [], "date": []}
        dates = await self.getAllDates()
        assert len(dates) >= 2, "Got not enough info"
        if len(dates) > 30:
            dates = dates[0:30]  # limit to 30 dates
        for day in dates:
            day_start = datetime.combine(day, time(0, 0, 0))
            day_end = day_start + timedelta(days=1)
            temp = (await OneMinuteData.annotate(min=Min(value)).annotate(max=Max(value)).filter(
                time__gte=day_start, time__lt=day_end).values("max", "min"))
            result["date"].append(day)
            temp = temp.pop(0)
            result["max"].append(temp["max"])
            result["min"].append(temp["min"])
        assert all(result.values()) is True, "Recieved nothing"
        return result


if __name__ == "__main__":
    db = DatabaseHandler(db_path="sqlite://test_data.db")
