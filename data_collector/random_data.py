import random
from datetime import datetime, timedelta, date
import peewee

def write_all_day_data(db: peewee.SqliteDatabase, _date=datetime.now().date()):
        time = datetime.now()
        time = time.replace(hour=0, minute=0, second=0, microsecond=0)
        time = time.replace(year=_date.year, month=_date.month, day=_date.day)
        delta = timedelta(minutes=1)
        db.connect()
        for _ in range(1439):
            time += delta
            OneMinuteData.create(
                pm25=random.randint(0, 15) / 10,
                pm10=random.randint(0, 15) / 10, 
                temperature=random.randint(-200, 300) / 10,
                pressure=random.randint(7350, 7750) / 10, 
                humidity=random.randint(0, 100) / 10, 
                time=time
            )
        db.close()
        print('Done!')


if __name__ == '__main__':
    db = peewee.SqliteDatabase('test_data.db', autoconnect=False)
    
    class OneMinuteData(peewee.Model):
        pm25 = peewee.FloatField()
        pm10 = peewee.FloatField()
        temperature = peewee.FloatField()
        pressure = peewee.FloatField()
        humidity = peewee.FloatField()
        time = peewee.DateTimeField()

        class Meta:
            database = db
            table_name = 'weather'
    
    db.connect()
    db.create_tables([OneMinuteData])
    db.close()

    #write_all_day_data(db, _date=date(2020, 11, 16))
    write_all_day_data(db)

    db.connect()
    query = (OneMinuteData
            .select(OneMinuteData.temperature, OneMinuteData.time)
            .where(
                OneMinuteData.time > datetime.now().replace(hour=1, minute=29, second=59),
                OneMinuteData.time <= datetime.now().replace(hour=2, minute=0)
                )
            )
    print([i.temperature for i in query])
    #print([i.time for i in query])
