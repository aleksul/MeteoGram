#!/usr/bin/python3.6
import asyncio
import aiohttp
import tg_api
from inet import Proxy
from bot_handler import BotHandler, BlackList
import logging
import restart
from os import name, path
from graph import GRAPH
from random import shuffle
from datetime import datetime, timedelta


async def find_proxy():
    inet = Proxy(timeout=3,
                 filename=f'{path}proxy.txt',
                 site_to_test=f'https://api.telegram.org/bot{tkbot_token}/getMe')
    results_temp = await asyncio.gather(inet.internet_check('http://example.org/'),
                                        inet.internet_check(f'https://api.telegram.org/bot{tkbot_token}/getMe'))
    if results_temp[0]['site'] == 'http://example.org/':
        results = [results_temp[0]['result'], results_temp[1]['result']]
    else:
        results = [results_temp[1]['result'], results_temp[0]['result']]
    logging.info(f'Internet test results: {results[0]}, {results[1]}')
    if not results[0]:  # internet connection test
        raise restart.InternetConnectionError
    elif results[1]:  # telegram without proxy connection test
        return None
    else:
        result = await inet.loader()
        if result:
            return result
        else:
            results, _ = await asyncio.wait([inet.broker_find(), inet.pub_find()])
        results = [i.result() for i in results if i.result() is not None]
        if results:
            return results[-1]
        else:
            raise restart.InternetConnectionError


async def logic(bot):
    global RESTART_FLAG, LAST_FIVE_RESPONSES, FINISH_START_FLAG
    update = await bot.get_updates()
    if update is None:
        FINISH_START_FLAG = True
        return None
    logging.debug("New message!")
    if 'callback_query' in update.keys():
        received_message = update['callback_query']['message']
        message_type = 'callback_query'
        data = update['callback_query']['data']
        user_id = str(received_message['chat']['id'])
    else:
        received_message = update['message']
        user_id = str(received_message['chat']['id'])
        message_type = list(received_message.keys())[4]
        if message_type == 'text':
            message_text = received_message['text']
            if message_text[0] == '/':
                message_type = 'command'
                if user_id in ADMIN_ID and message_text in ADMIN_COMMANDS:
                    message_type = 'admin_command'
    if user_id in ban.ids:
        return None
    if FINISH_START_FLAG:
        LAST_FIVE_RESPONSES[4], LAST_FIVE_RESPONSES[3], LAST_FIVE_RESPONSES[2], LAST_FIVE_RESPONSES[1] = \
            LAST_FIVE_RESPONSES[3], LAST_FIVE_RESPONSES[2], LAST_FIVE_RESPONSES[1], LAST_FIVE_RESPONSES[0]
        LAST_FIVE_RESPONSES[0] = {'user_id': user_id, 'time': datetime.now()}
        ids = {i['user_id'] for i in LAST_FIVE_RESPONSES}
        if len(ids) == 1 and \
                LAST_FIVE_RESPONSES[0]['time']-LAST_FIVE_RESPONSES[4]['time'] <= timedelta(seconds=1):
            ban.add(user_id)
            logging.info(f'User {received_message["chat"]["first_name"]} with id:{user_id} was added to blacklist')
            asyncio.ensure_future(bot.send_message(user_id, 'Вы были добавлены в черный список'))
            return None

    logging.debug(f'Message type: {message_type}')
    user_name = received_message['chat']['first_name']
    if message_type == 'command':
        if message_text == '/start':
            asyncio.ensure_future(bot.send_message(user_id, f'Приветствую, {user_name}! \n'
                                                            f'Я бот, который поможет тебе '
                                                            f'узнать метеоданные в Троицке!',
                                                   reply_markup=kb_start))
        elif message_text == '/help':
            asyncio.ensure_future(bot.send_message(user_id, 'Все чрезвычайно просто:\n'
                                                            '• для просмотра текущего состояния напиши /now\n'
                                                            '• для построения графика напиши /graph\n'
                                                            '• для просмотра сырого файла напиши /raw\n\n'
                                                            'Интересуют подробности отображаемых измерений?\n'
                                                            'Напиши /info',
                                                   reply_markup=kb_start2))
        elif message_text == '/now':
            now = graph.read_last()
            asyncio.ensure_future(bot.send_message(user_id, f'Данные собраны в {now["Time"]}\n\n'
                                                            f'Температура: {now["Temp"]} °C\n'
                                                            f'Давление: {now["Pres"]} мм/рт.ст.\n'
                                                            f'Влажность: {now["Humidity"]} %\n'
                                                            f'Частицы PM2.5: {now["PM2.5"]} мкгр/м³\n'
                                                            f'Частицы PM10: {now["PM10"]} мкгр/м³',
                                                   reply_markup=kb_start2))
        elif message_text == '/raw':
            keyboard = [[]]
            strings_num = 0
            for i in graph.dates():
                if len(keyboard[strings_num]) > 2:
                    keyboard.append([])
                    strings_num += 1
                pretty_date = i.split('-')
                pretty_date = pretty_date[0]+'.'+pretty_date[1]+'.'+pretty_date[2]
                keyboard[strings_num].append(
                    tg_api.InlineButtonBuilder(pretty_date, callback_data='-raw+' + i)
                )
            asyncio.ensure_future(bot.send_message(user_id, 'Выберите дату:',
                                                   reply_markup=tg_api.InlineMarkupBuilder(keyboard)))
        elif message_text == '/graph':
            asyncio.ensure_future(bot.send_message(user_id, 'Выберите временной промежуток:',
                                                   reply_markup=kb_choose_time))
        elif message_text == '/info':
            asyncio.ensure_future(bot.send_message(user_id, 'Где производится замер?\n'
                                                            'Метеостанция располгается по адресу: г.Москва, г.Троицк, '
                                                            'Сиреневый бульвар, д.1, снаружи "Точки Кипения"\n\n'
                                                            'Как определяется время суток на графике дня?\n'
                                                            '4:00-10:00 - утро\n'
                                                            '10:00-16:00 - день\n'
                                                            '16:00-22:00 - вечер\n'
                                                            '22:00-4:00 - ночь\n\n'
                                                            'Что такое частицы PM2.5 и PM10?\n'
                                                            'Это мелкодисперсные частицы пыли, которые, '
                                                            'буквально, "витают в воздухе". '
                                                            'Из-за их малых размеров (2.5 мкм и 10 мкм соответсвенно) '
                                                            'и веса они практически не осядают, таким образом загрязняя'
                                                            ' воздух, которым мы дышим.\n'
                                                            'Согласно ВОЗ, среднесуточный уровень этих частиц '
                                                            'не должен быть больше 25 мкгр/м³\n'
                                                            'Подробнее можно прочитать, например, здесь:\n'
                                                            'https://habr.com/ru/company/tion/blog/396111/',
                                                   reply_markup=kb_start2))
        else:
            asyncio.ensure_future(bot.send_message(user_id, 'Неверная команда!\nДля вывода подсказки напишите /help'))

    elif message_type == 'admin_command':
        if message_text == '/admin':
            asyncio.ensure_future(bot.send_message(user_id, f'Наконец то мой дорогой админ {user_name} '
                                                            f'добрался до раздела админских возможностей! '
                                                            f'Что интересует?',
                                                   reply_markup=kb_admin))
        elif message_text == '/log':
            asyncio.ensure_future(bot.send_file(user_id, f'{path}bot.log', 'log.txt', reply_markup=kb_start2))
        elif message_text == '/restart':
            shuffle(restart_str_list)
            kb_restart = []
            for i in list(restart_str_list):
                kb_restart.append([i])
            asyncio.ensure_future(bot.send_message(user_id, 'Вы уверены?',
                                                   reply_markup=tg_api.KeyboardBuilder(kb_restart)))
            RESTART_FLAG = 1
        elif message_text == '/clear_log':
            with open(path+'bot.log', 'w'):
                pass
            logging.info('Cleared log')
            asyncio.ensure_future(bot.send_message(user_id, 'Готово!', reply_markup=kb_admin))
        elif message_text == '/back':
            asyncio.ensure_future(
                bot.send_message(user_id, 'Возвращаю нормальную клавиатуру :)', reply_markup=kb_start2))
    elif message_type == 'text':
        if user_id in ADMIN_ID and message_text == 'Да, перезапуск!' and RESTART_FLAG:
            RESTART_FLAG = 0
            await bot.send_message(user_id, 'Перезапускаюсь...', reply_markup=kb_start2)
            raise restart.UserRestart
        elif user_id in ADMIN_ID and RESTART_FLAG:
            asyncio.ensure_future(bot.send_message(user_id, 'Перезапуск отменен', reply_markup=kb_start2))
            RESTART_FLAG = 0
        else:
            asyncio.ensure_future(bot.send_message(user_id, 'Помочь с командами?\nНапиши /help'))
    elif message_type == 'callback_query':
        if data[0] == '+':
            bt_pm25 = tg_api.InlineButtonBuilder('Частицы PM2.5', callback_data='=PM2.5' + data)
            bt_pm10 = tg_api.InlineButtonBuilder('Частицы PM10', callback_data='=PM10' + data)
            bt_temp = tg_api.InlineButtonBuilder('Температура', callback_data='=Temp' + data)
            bt_pres = tg_api.InlineButtonBuilder('Давление', callback_data='=Pres' + data)
            bt_humidity = tg_api.InlineButtonBuilder('Влажность', callback_data='=Humidity' + data)
            kb_choose_parameter = tg_api.InlineMarkupBuilder([[bt_pm25, bt_pm10], [bt_temp], [bt_pres, bt_humidity]])
            asyncio.ensure_future(bot.send_message(user_id, 'Выберите параметр:',
                                                   reply_markup=kb_choose_parameter))
        elif data[0] == '-':
            if data == '-day':
                keyboard = [[]]
                strings_num = 0
                for i in graph.dates():
                    if len(keyboard[strings_num]) > 2:
                        keyboard.append([])
                        strings_num += 1
                    pretty_date = i.split('-')
                    pretty_date = pretty_date[0] + '.' + pretty_date[1] + '.' + pretty_date[2]
                    keyboard[strings_num].append(
                        tg_api.InlineButtonBuilder(pretty_date, callback_data='+day+' + i)
                    )
                asyncio.ensure_future(bot.send_message(user_id, 'Выберите дату:',
                                                       reply_markup=tg_api.InlineMarkupBuilder(keyboard)))
            elif data.split('+')[0] == '-raw':
                asyncio.ensure_future(bot.send_file(user_id,
                                                    path + '/' + 'data' + '/' + data.split('+')[1] + '.csv',
                                                    filename=data.split('+')[1]+'.txt',
                                                    reply_markup=kb_start2))

        elif data[0] == '=':
            data = data[1:].split('+')
            if data[1] in ['15', '30', '60', '180']:  # minutes
                plot_data = graph.read_csv_timedelta(data[0], datetime.now(),
                                                     datetime.now()-timedelta(minutes=int(data[1])))
                if plot_data:
                    photo = graph.plot_minutes(plot_data, data[0])
                    if photo:
                        asyncio.ensure_future(bot.send_photo(user_id, photo))
                    else:
                        asyncio.ensure_future(bot.send_message(user_id, 'За этот период нет данных :('))
                else:
                    asyncio.ensure_future(bot.send_message(user_id, 'За этот период нет данных :('))
            elif data[1] == 'day':  # one day
                date = data[2].split('-')
                date = [int(i) for i in date]
                date1 = datetime(date[2], date[1], date[0], 0, 0, 0)
                date2 = datetime(date[2], date[1], date[0], 23, 59, 59)
                plot_data = graph.read_csv_timedelta(data[0], date1, date2)
                if plot_data:
                    photo = graph.plot_day(plot_data, data[0])
                    if photo:
                        asyncio.ensure_future(bot.send_photo(user_id, photo,
                                                             caption=f'Данные за: {date[0]}.{date[1]}.{date[2]}'))
                    else:
                        asyncio.ensure_future(bot.send_message(user_id, 'За этот период нет данных :('))
                else:
                    asyncio.ensure_future(bot.send_message(user_id, 'За этот период нет данных :('))
            elif data[1] == 'month':  # month
                plot_data = graph.read_month(data[0])
                photo = graph.plot_month(plot_data, data[0])
                if photo:
                    asyncio.ensure_future(bot.send_photo(user_id, photo))
                else:
                    asyncio.ensure_future(bot.send_message(user_id, 'За этот период нет данных :('))

    else:
        asyncio.ensure_future(bot.send_message(user_id, 'Данный тип данных не поддерживается'))


async def aio_session(proxy_local):
    async with aiohttp.ClientSession() as session:
        tg_bot = BotHandler(tkbot_token, session, proxy_local)
        minute = ioloop.time()
        task_bot = asyncio.ensure_future(logic(tg_bot), loop=ioloop)
        task_get_info = asyncio.ensure_future(graph.get_info(session), loop=ioloop)
        while 1:
            if task_bot.done():  # check if our task done
                task_bot.result()  # will raise error if task finished incorrectly
                task_bot = asyncio.ensure_future(logic(tg_bot), loop=ioloop)
            if task_get_info.done():
                task_get_info.result()
            if ioloop.time() - minute >= 60.0:
                minute += 60.0  # maybe we have waited a bit more than expected but this trick will compensate it
                task_get_info = asyncio.ensure_future(graph.get_info(session), loop=ioloop)
            await asyncio.sleep(0.1)  # we need to give control back to event loop

if __name__ == '__main__':
    if name == 'nt':
        path = path.dirname(__file__) + '/'
    else:
        path = '/home/pi/bot/'

    logging.basicConfig(filename=f'{path}bot.log',
                        format='%(asctime)s    %(levelname)s: %(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        level=logging.DEBUG)
    logging.info('Program started')

    ADMIN_ID = ['196846654', '463145322']
    ADMIN_COMMANDS = ['/admin', '/log', '/restart', '/clear_log', '/black_list', '/back']

    empty_user = dict(user_id='0', time=datetime.now())
    LAST_FIVE_RESPONSES = [empty_user, empty_user, empty_user, empty_user, empty_user]

    RESTART_FLAG = 0
    restart_str_list = ['Нет конечно!', 'Да, перезапуск!', 'Нет!', 'Неееет!']

    tkbot_token = '1012565455:AAGctwGzz0LRlucqZiiEIvchtLhJjd1Fqdw'
    # tkbot_token = '1061976169:AAFUJ1rnKXmhbMN5POAPk1DxdY0MPQZlwuk'

    kb_start = tg_api.KeyboardBuilder([['/now', '/graph', '/raw'], ['/help']], one_time_keyboard=False)
    kb_start2 = tg_api.KeyboardBuilder([['/now'], ['/graph', '/raw']], one_time_keyboard=False)

    kb_admin = tg_api.KeyboardBuilder([['/log', '/restart'], ['/clear_log', '/back']])

    bt_month = tg_api.InlineButtonBuilder('Месяц', callback_data='+month')
    bt_day = tg_api.InlineButtonBuilder('День', callback_data='-day')
    bt_3h = tg_api.InlineButtonBuilder('3 часа', callback_data='+180')
    bt_1h = tg_api.InlineButtonBuilder('1 час', callback_data='+60')
    bt_30min = tg_api.InlineButtonBuilder('Полчаса', callback_data='+30')
    bt_15min = tg_api.InlineButtonBuilder('15 минут', callback_data='+15')
    kb_choose_time = tg_api.InlineMarkupBuilder([[bt_15min, bt_30min, bt_1h], [bt_3h, bt_day], [bt_month]])

    graph = GRAPH('192.168.0.175', data_path=path+'data/', timeout=5)

    ban = BlackList(file_path=path+'ban_list.txt')
    FINISH_START_FLAG = False

    asyncio.set_event_loop(asyncio.new_event_loop())
    ioloop = asyncio.get_event_loop()
    task_proxy = ioloop.create_task(find_proxy())
    try:
        proxy = ioloop.run_until_complete(task_proxy)
    except Exception as err:
        logging.critical(f'Restart caused: {type(err)}:{err}')
        task_proxy.cancel()
        ioloop.stop()
        ioloop.close()
        restart.program(path+'bot_main.py', 10)
    else:
        if proxy:
            proxy_str = f'http://{proxy}'
        else:
            proxy_str = None
        try:
            ioloop.run_until_complete(aio_session(proxy_str))
        except Exception as err:
            logging.critical(f'Restart caused: {type(err)}:{err}')
        finally:
            ioloop.stop()
            ioloop.close()
            restart.program(path+'bot_main.py', 10)
else:
    logging.critical(f'__Name__ is NOT equal main! It is {__name__}')
