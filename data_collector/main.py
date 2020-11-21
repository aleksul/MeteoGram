import requests
import schedule
from time import sleep
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from os import environ
import peewee

DB_PATH = '/meteo_data/data.db'
if 'DEBUG' in environ:
    DB_PATH = 'test_data.db'

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
    soup = BeautifulSoup(text, 'html.parser')
    soup = soup.find_all('td', class_='r')
    data = []
    for i in range(len(soup) - 2):  # we don't need two last parameters (wifi)
        i = soup[i].get_text()
        i = i.replace(u'\xa0', u' ')  # change space to SPACE (I'm just normalizing the string)
        i = i.split()  # separate value from measurement units  # TODO use it as dict key
        temp = i.pop(0)
        if temp == '-':
            logging.warning("Received empty values")
            return {}
        data.append(float(temp))
    data[3] = round(data[3] * 100 / 133, 2)  # hPa to mm Hg
    return {'PM2.5': data.pop(0), 'PM10': data.pop(0), 'Temperature': data.pop(0),
            'Pressure': data.pop(0), 'Humidity': data.pop(0), 'Time': datetime.now()} 


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
                OneMinuteData.create(
                    pm25=data['PM2.5'],
                    pm10=data['PM10'],
                    temperature=data['Temperature'],
                    pressure=data['Pressure'],
                    humidity=data['Humidity'],
                    time=data['Time']
                )
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
        schedule.every(60).seconds.do(get_info, ip)
        while True:
            schedule.run_pending()
            sleep(1)
