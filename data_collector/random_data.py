import random
import csv
from datetime import datetime, timedelta

DOCKER_VOLUME_PATH = '/meteo_data/'
# DOCKER_VOLUME_PATH = 'C:\\Projects\\tg-bot\\bot\\data\\'
file_path = ''


def new_file(date=None):
    global file_path
    if date is None:
        date = datetime.now().strftime('%d-%m-%Y')
    file_path = DOCKER_VOLUME_PATH + date + '.csv'
    with open(file_path, "w", newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(['PM2.5', 'PM10', 'Temp', 'Pres', 'Humidity', 'Time'])
    print('New file done!')


def data_writer(i):
    global file_path
    time = datetime(2020, 1, 1, 0, 0, 0)
    delta = timedelta(minutes=1)
    for i in range(i):
        time += delta
        data_to_write = [random.randint(0, 15) / 10, random.randint(0, 15) / 10, random.randint(-200, 300) / 10,
                         random.randint(7350, 7750) / 10, random.randint(0, 100) / 10, time.strftime('%H:%M:%S')]
        with open(file_path, 'a', newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(data_to_write)
        print(i)
    print('Done!')


if __name__ == '__main__':
    new_file()
    data_writer(1439)
