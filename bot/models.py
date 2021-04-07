from tortoise import fields
from tortoise.models import Model

from typing import Tuple
from pydantic import BaseModel, root_validator
from pydantic.class_validators import validator
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


class PlotData(BaseModel):
    values: Tuple[float, ...]
    time: Tuple[datetime, ...]

    @root_validator
    def same_length(cls, values):
        assert len(values.get('time')) == len(values.get('values')), \
            "The value must be the same length as the time list"
        return values

    @validator('values')
    def min_max_values_count(cls, v):
        assert len(v) > 3, "We need MORE values"
        assert len(v) < 330, "That's TOO MUCH (values), man"
        return v


class MinMaxData(BaseModel):
    minimum: float
    maximum: float


class PlotDayData(BaseModel):
    day: date
    morning: MinMaxData
    noon: MinMaxData
    evening: MinMaxData
    night: MinMaxData


class PlotMonthData(BaseModel):
    minimum: Tuple[float, ...]
    maximum: Tuple[float, ...]
    dates: Tuple[date, ...]

    @root_validator
    def same_length(cls, values):
        t = values.copy()
        dates_len = len(t.pop('dates'))
        assert all(len(x) == dates_len for x in t.values()), \
            "Min and max must be the same length as the dates list"
        return values
