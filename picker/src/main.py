import requests
import schedule
from time import sleep
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from os import environ
import peewee

DB_PATH = '/meteo_data/data.db'

db = peewee.SqliteDatabase(DB_PATH, autoconnect=False)


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


def html_parser(text) -> dict:
    data = {'PM2.5': -1, 'PM10': -1, 'Temperature': -1, 'Pressure': -1, 'Humidity': -1}
    for row in BeautifulSoup(text, 'html.parser').find('table').find_all("tr"):
        row = BeautifulSoup(row, 'html.parser').find_all('td')
        for tag in range(0, len(row)):
            row[tag] = row[tag].string  # prettify
        if len(row) == 3:
            # translate
            row[1] = row[1].replace('Температура', 'Temperature')
            row[1] = row[1].replace('Давление воздуха', 'Pressure')
            row[1] = row[1].replace('Относительная влажность', 'Humidity')
            if row[1] in data.keys():
                data[row[1]] = float(row[2].split()[0])  # convert values
                if row[1] == 'Pressure':  # hPa to mmHg
                    data[row[1]] = round(data[row[1]] * 100 / 133, 2)
    assert not (all(item == -1 for item in data.values())), "All values \
        haven't changed yet"

    data.update(Time=datetime.now())  # adding timestamp
    return data


def get_info(ip: str, errors_left=2):
    try:
        response = requests.get(ip, timeout=15)
        assert response.status_code == 200
    except Exception as err:
        logging.error(f"Getting info from meteostation error: {type(err)}:{err}")
        logging.error(f'Retries left: {errors_left}')
        errors_left -= 1
        if errors_left > 0:
            get_info(ip, errors_left=errors_left)
    else:
        data = html_parser(response.text)
        if data:
            db.connect()
            OneMinuteData.create(pm25=data['PM2.5'],
                                 pm10=data['PM10'],
                                 temperature=data['Temperature'],
                                 pressure=data['Pressure'],
                                 humidity=data['Humidity'],
                                 time=data['Time'])
            db.close()


if __name__ == "__main__":
    logging.basicConfig(filename='data_collector.log',
                        format='%(asctime)s    %(levelname)s: %(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        level=logging.WARNING)
    logging.info('Program started')

    db.connect()
    db.create_tables([OneMinuteData])
    db.close()

    if 'DEBUG' in environ:  # if DEBUG key in enviroment variables
        logging.level = logging.DEBUG
        import random_data
        random_data.write_all_day_data(db)  # TODO does it work?
        while True:
            pass
    else:
        ip = environ.get("MeteostationIP", "192.168.0.2")
        ip = 'http://' + ip + '/values'
        get_info(ip)
        schedule.every(60).seconds.do(get_info, ip)
        while True:
            schedule.run_pending()
            sleep(1)
