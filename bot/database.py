import logging

from asyncio import run as async_run

from tortoise import Tortoise
from tortoise.functions import Min, Max
from tortoise.query_utils import Q

from models import OneMinuteData  # tortoise model
from models import MinuteData, PlotData, PlotDayData, MinMaxData  # pydantic models

from datetime import datetime, timedelta, time, date

from typing import IO
from tempfile import NamedTemporaryFile

__models__ = [OneMinuteData]


class DatabaseHandler:

    def __init__(self, db_path: str):
        self.DB_PATH = db_path
        async_run(Tortoise.init(db_url=self.DB_PATH, modules={"models": ["models"]}))

        self.day_parts = {
            "four_am": datetime.combine(date=date.today(), time=time(4, 0, 0)),
            "ten_am": datetime.combine(date.today(), time(10, 0, 0)),
            "four_pm": datetime.combine(date.today(), time(16, 0, 0)),
            "ten_pm": datetime.combine(date.today(), time(22, 0, 0)),
            "twelve_pm": datetime.combine(date.today(), time(0, 0, 0)),
            "twelve_pm_next_day": datetime.combine(date.today() + timedelta(days=1), time(0, 0, 0))
        }

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

    async def getDataByTimedelta(self, start_point: datetime, delta: timedelta,
                                 value: str) -> PlotData:
        """Collects data from database in set period

        Args:
            start_point (datetime): When start data collecting
            delta (timedelta): How much to collect
            value (str): Which data are you interested in

        Returns:
            PlotData: pydantic model with data you asked for
        """
        self.isValueCorrect(value)
        result: PlotData
        end_point: datetime
        if delta >= timedelta():  # if delta >= 0
            end_point = start_point + delta
        else:
            end_point = start_point
            start_point += delta
        query = OneMinuteData.filter(time__gte=start_point, time__lte=end_point).order_by("time")
        result = PlotData(values=await query.values_list(value, flat=True),
                          time=await query.values_list('time', flat=True))
        return result

    async def getDataByDay(self, day: date, value: str) -> PlotDayData:
        """Collects data from database on a certain day

        Args:
            day (datetime.date): The day to collect data
            value (str): Which data are you interested in

        Returns:
            PlotDayData: pydantic model with fields for
            every day part, each one contains max & min
        """
        self.isValueCorrect(value)
        # preparing day dividers
        parts = {}
        for k, v in self.day_parts.items():
            parts.update({k: v.replace(year=day.year, month=day.month, day=day.day)})
        parts["twelve_pm_next_day"] += timedelta(days=1)
        # preparing queries
        mainQuery = OneMinuteData.annotate(max=Max(value)).annotate(min=Min(value))
        queries = {
            'morning':
                mainQuery.filter(time__gte=parts['four_am'], time__lt=parts['ten_am']),
            'noon':
                mainQuery.filter(time__gte=parts['ten_am'], time__lt=parts['four_pm']),
            'evening':
                mainQuery.filter(time__gte=parts['four_pm'], time__lt=parts['ten_pm']),
            'night':
                mainQuery.filter(
                    Q(time__gte=parts['twelve_pm'], time__lt=parts['four_am']) |
                    Q(time__gte=parts['ten_pm'], time__lte=parts['twelve_pm_next_day']))
        }
        # execute queries
        dataByParts = {}
        for partName, query in queries.items():
            t = (await query.values("max", "min"))[0]
            dataByParts.update({partName: MinMaxData(minimum=t['min'], maximum=t['max'])})
        # return retrieved values
        return PlotDayData(day=day,
                           morning=dataByParts['morning'],
                           noon=dataByParts['noon'],
                           evening=dataByParts['evening'],
                           night=dataByParts['night'])

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

    async def getLastData(self) -> MinuteData:
        """Collects last data written to database

        Returns:
            MinuteData: pydantic model with all values
        """
        vals = (await OneMinuteData.annotate(last=Max("id")).values())[0]
        return MinuteData(pm25=vals.pop('pm25'),
                          pm10=vals.pop('pm10'),
                          temperature=vals.pop('temperature'),
                          pressure=vals.pop('pressure'),
                          humidity=vals.pop('humidity'),
                          time=vals.pop('time'))

    async def getAllDates(self, includeToday=False) -> list:  # TODO rewrite for pydantic
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

    async def getMonthData(self, value: str) -> dict:  # TODO rewrite for pydantic
        """Collects min, max and Datetime.date for last 30 (or less) saved days

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
            temp = await OneMinuteData.annotate(min=Min(value)).annotate(max=Max(value)).filter(
                time__gte=day_start, time__lt=day_end).values("max", "min")
            result["date"].append(day)
            temp = temp.pop(0)
            result["max"].append(temp["max"])
            result["min"].append(temp["min"])
        assert all(result.values()) is True, "Recieved nothing"
        return result


# testing
if __name__ == "__main__":
    db = DatabaseHandler(db_path="sqlite://test_data.db")
    print(async_run(db.getDataByDay(date.today(), 'pm25')))
