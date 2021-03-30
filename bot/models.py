from pydantic.class_validators import validator
from tortoise import fields
from tortoise.models import Model

from pydantic import BaseModel, root_validator
from typing import List, Optional
from datetime import date, datetime


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
        return ["id", "pm25", "pm10", "temperature", "pressure", "humidity", "time"]

    class Meta:
        table = "weather"


'''
class _Data(BaseModel):
    pm25: Optional[float]
    pm10: Optional[float]
    temperature: Optional[float]
    pressure: Optional[float]
    humidity: Optional[float]
    time: datetime

    @root_validator
    def one_is_required(cls, values):
        assert not all(i is None for i in values), "At least one value is required"
        return values


class MinutesData(BaseModel):
    data = List[_Data]

'''


class PlotData(BaseModel):
    values: List[float]
    time: List[datetime]

    @root_validator
    def same_length(cls, values):
        assert len(values['time']) == len(values['values']), \
            "The value must be the same length as the time list"
        return values

    @validator('values')
    def min_max_values_count(cls, v):
        assert len(v) < 5, "We need MORE values"
        assert len(v) > 330, "That's TOO MUCH (values), man"
        return v


class _MinMaxData(BaseModel):
    minimum: float
    maximum: float


class PlotDayData(BaseModel):
    day: date
    morning: _MinMaxData
    noon: _MinMaxData
    evening: _MinMaxData
    night: _MinMaxData


class PlotMonthData(BaseModel):
    minimum: List[float]
    maximum: List[float]
    dates: List[date]

    @root_validator
    def same_length(cls, values):
        t = values.copy()
        dates_len = len(t.pop('dates'))
        assert all(len(x) == dates_len for x in t.values()), \
            "Min and max must be the same length as the dates list"
        return values
