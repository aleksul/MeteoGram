import random
import csv

file_path = 'P:/EOS bot/data' + '/' + '05-02-2020' + '.csv'


def new_file():
    with open(file_path, "w", newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(['PM2.5', 'PM10', 'Temp', 'Pres', 'Humidity'])
    print('New file done!')


def data_writer(i):
    for i in range(i):
        data_to_write = [random.uniform(0, 1), random.uniform(0, 1), random.uniform(20, 30),
                         random.uniform(740, 750), random.uniform(0, 100)]
        with open(file_path, 'a', newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(data_to_write)
        print(i)
    print('Done!')


if __name__ == '__main__':
    new_file()
    data_writer(1440)