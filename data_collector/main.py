import requests
import schedule
from time import sleep
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from os import path, stat, remove
import csv
import logging
from os import environ


class MeteostationDataSaver:
    def __init__(self, ip: str, data_path: str, timeout=10):
        self.ip_add = 'http://' + ip + '/values'
        self.data_path = data_path
        self.timeout = timeout

    def get_info(self):
        try:
            response = requests.get(self.ip_add, timeout=self.timeout)
            assert response.status_code == 200
            text = response.text()
            data = self.html_parser(text)
        except Exception as err:
            logging.error(f"Getting info from meteostation error: {type(err)}:{err}")
        else:
            if data:
                self.csv_write(data)

    @staticmethod
    def html_parser(text):
        soup = BeautifulSoup(text, 'html.parser')
        soup = soup.find_all('td', class_='r')
        data_to_write = []
        for i in range(len(soup) - 2):  # we don't need two last parameters (wifi)
            i = soup[i].get_text()
            i = i.replace(u'\xa0', u' ')  # change space to SPACE (I'm just normalizing the string)
            i = i.split()  # separate value from measurement units
            temp = i.pop(0)
            if temp == '-':
                logging.warning("Received empty values")
                return None
            data_to_write.append(float(temp))
        data_to_write[3] = round(data_to_write[3] * 100 / 133, 2)  # hPa to mm Hg
        data_to_write.append(datetime.now().strftime('%H:%M:%S'))  # adds time value
        return data_to_write

    def csv_write(self, data_to_write):
        file_path = self.csv_path()
        with open(file_path, 'a', newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(data_to_write)
        logging.debug('Wrote info to the file')
        return None

    def csv_path(self, date_local=None, new_file=True, tries=5):  # creates new file or show previous
        if date_local is None:
            date_local = datetime.now().strftime('%d-%m-%Y')
        file_path = self.data_path + date_local + '.csv'
        if (not path.exists(file_path)) or (stat(file_path).st_size == 0):  # check if we have a file
            if new_file:
                logging.debug(f'Create new file: {file_path}')
                with open(file_path, "w", newline='') as csv_file:
                    writer = csv.writer(csv_file, delimiter=',')
                    writer.writerow(['PM2.5', 'PM10', 'Temp', 'Pres', 'Humidity', 'Time'])
                self.delete_old()  # call deleter every time we write new file
            else:
                if tries <= 0:
                    logging.warning('Can NOT find the file, so will create a new one')
                    return self.csv_path()
                else:
                    tries -= 1
                    logging.debug("Didn't find anything, try previous date")
                    return self.csv_path(date_local=self.previous_date(date_local), new_file=False, tries=tries)
        return file_path

    @staticmethod
    def previous_date(date_local: str):  # receives date as 01-01-2020 and returns previous date as 31-12-2019
        date_local = date_local.split('-')
        date_local = datetime(int(date_local[2]), int(date_local[1]), int(date_local[0]))
        date_local -= timedelta(days=1)
        return date_local.strftime('%d-%m-%Y')

    def delete_old(self, days_to_save=31, files_num=1):  # deletes old files (calls every time new file creates)
        old_file_date = datetime.now() - timedelta(days=days_to_save)
        one_day_delta = timedelta(days=1)
        for _ in range(files_num):
            file_path = self.data_path + old_file_date.strftime('%d-%m-%Y') + '.csv'
            logging.debug(f'File that should be removed:{file_path}')
            if path.exists(file_path):
                remove(file_path)
                logging.info(f'Removed old file: {file_path}')
            old_file_date -= one_day_delta


if __name__ == "__main__":
    logging.basicConfig(filename='data_collector.log',
                        format='%(asctime)s    %(levelname)s: %(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        level=logging.WARNING)
    logging.info('Program started')
    if 'DEBUG' in environ:  # if DEBUG key in enviroment variables
        logging.level = logging.DEBUG
        import random_data
        random_data.new_file()
        random_data.data_writer(1439)
        while True:
            pass
    else:
        dataSaver = MeteostationDataSaver(environ.get("MeteostationIP", "192.168.0.2"), "/meteo_data")
        schedule.every(60).seconds.do(dataSaver.get_info)
        while True:
            schedule.run_pending()
            sleep(1)
