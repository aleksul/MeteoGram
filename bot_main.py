#!/usr/bin/python3.6
import asyncio
import aiohttp
import tg_api
from inet import Proxy
from bot_handler import BotHandler
import logging
import restart
from os import name, path
from graph import GRAPH
from datetime import datetime


async def repeat(interval, func, *args, **kwargs):
    """Run func every interval seconds.

    If func has not finished before *interval*, will run again
    immediately when the previous iteration finished.

    *args and **kwargs are passed as the arguments to func.
    """
    if interval == 0:
        while True:
            try:
                await func(*args, **kwargs)
            except Exception as err1:
                raise err1
    else:
        while True:
            try:
                await asyncio.gather(
                    func(*args, **kwargs),
                    asyncio.sleep(interval),
                )
            except Exception as err2:
                raise err2


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
    update = await bot.get_updates()
    if update is None:
        return None
    global RESTART_FLAG
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
                                                            '• для построения графика напиши /graph\n\n'
                                                            'Интересуют подробности отображаемых измерений?\n'
                                                            'Напиши /info',
                                                   reply_markup=kb_start2))
        elif message_text == '/now':
            date = datetime.now().strftime('%d-%m-%Y')
            temperature = graph.read_csv('Temp', 1, date=date)['data'][0]
            pm25 = graph.read_csv('PM2.5', 1, date=date)['data'][0]
            pm10 = graph.read_csv('PM10', 1, date=date)['data'][0]
            pressure = graph.read_csv('Pres', 1, date=date)['data'][0]
            humidity = graph.read_csv('Humidity', 1, date=date)['data'][0]
            asyncio.ensure_future(bot.send_message(user_id, f'Температура: {temperature} °C\n'
                                                            f'Давление: {pressure} мм/рт.ст.\n'
                                                            f'Влажность: {humidity} %\n'
                                                            f'Частицы PM2.5: {pm25} мкгр/м³\n'
                                                            f'Частицы PM10: {pm10} мкгр/м³',
                                                   reply_markup=kb_start2))
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
            asyncio.ensure_future(bot.send_file(user_id, f'{path}bot.log', reply_markup=kb_start2))
        elif message_text == '/restart':
            asyncio.ensure_future(bot.send_message(user_id, 'Вы уверены?',
                                                   reply_markup=tg_api.KeyboardBuilder(
                                                       [['Нет конечно!'], ['Да, перезапуск!'], ['Нет!']])))
            RESTART_FLAG = 1
        elif message_text == '/raw':
            keyboard = [[]]
            strings_num = 0
            for i in graph.dates():
                if len(keyboard[strings_num]) > 2:
                    keyboard.append([])
                    strings_num += 1
                keyboard[strings_num].append(
                    tg_api.InlineButtonBuilder(i, callback_data='-raw+' + i)
                )
            asyncio.ensure_future(bot.send_message(user_id, 'Выберите дату:',
                                                   reply_markup=tg_api.InlineMarkupBuilder(keyboard)))
        elif message_text == '/back':
            asyncio.ensure_future(bot.send_message(user_id, 'Возвращаю нормальную клавиатуру :)', reply_markup=kb_start2))
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
                    keyboard[strings_num].append(
                        tg_api.InlineButtonBuilder(i, callback_data='+day+' + i)
                    )
                asyncio.ensure_future(bot.send_message(user_id, 'Выберите дату:',
                                                       reply_markup=tg_api.InlineMarkupBuilder(keyboard)))
            elif data.split('+')[0] == '-raw':
                asyncio.ensure_future(bot.send_file(user_id,
                                                    path+'/'+'data'+'/'+data.split('+')[1]+'.csv',
                                                    reply_markup=kb_start2))

        elif data[0] == '=':
            data = data[1:].split('+')
            if data[1] in ['15', '30', '60']:  # minutes
                asyncio.ensure_future(bot.send_photo(user_id,
                                                     graph.plot_minutes(
                                                         graph.read_csv(data[0], int(data[1])),
                                                         data[0])
                                                     ))
            elif data[1] == '180':  # 3 hours
                asyncio.ensure_future(bot.send_photo(user_id,
                                                     graph.plot_three_hours(
                                                         graph.read_csv(data[0], int(data[1])),
                                                         data[0])
                                                     ))
            elif data[1] == 'day':  # one day
                asyncio.ensure_future(bot.send_photo(user_id,
                                                     graph.plot_day(
                                                         graph.read_all_csv(data[0], data[2]),
                                                         data[0])
                                                     ))
            elif data[1] == 'month':  # month
                asyncio.ensure_future(bot.send_photo(user_id,
                                                     graph.plot_month(
                                                         graph.read_month(data[0]),
                                                         data[0]
                                                     )))

    else:
        asyncio.ensure_future(bot.send_message(user_id, 'Данный тип данных не поддерживается'))


async def main(best_proxy: str):
    session = aiohttp.ClientSession()
    try:
        tg_bot = BotHandler(tkbot_token, session, best_proxy)
        t1 = asyncio.ensure_future(repeat(0, logic, tg_bot))
        t2 = asyncio.ensure_future(repeat(60, graph.get_info, session))
        await t1
        await t2
    finally:
        await session.close()


if __name__ == '__main__':
    if name == 'nt':
        path = path.dirname(__file__) + '/'
    else:
        path = '/home/pi/bot/'

    logging.basicConfig(filename=f'{path}bot.log',
                        format='%(asctime)s    %(levelname)s: %(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        level=logging.INFO)
    logging.info('Program started')

    ADMIN_ID = ['196846654', '463145322']
    ADMIN_COMMANDS = ['/admin', '/log', '/restart', '/raw', '/back']
    RESTART_FLAG = 0

    tkbot_token = '1012565455:AAGctwGzz0LRlucqZiiEIvchtLhJjd1Fqdw'
    # tkbot_token = '1061976169:AAFUJ1rnKXmhbMN5POAPk1DxdY0MPQZlwuk'

    kb_start = tg_api.KeyboardBuilder([['/now', '/graph'], ['/help']], one_time_keyboard=False)
    kb_start2 = tg_api.KeyboardBuilder([['/now'], ['/graph']], one_time_keyboard=False)
    kb_admin = tg_api.KeyboardBuilder([['/log', '/raw'], ['/restart', '/back']])
    bt_month = tg_api.InlineButtonBuilder('Месяц', callback_data='+month')
    bt_day = tg_api.InlineButtonBuilder('День', callback_data='-day')
    bt_3h = tg_api.InlineButtonBuilder('3 часа', callback_data='+180')
    bt_1h = tg_api.InlineButtonBuilder('1 час', callback_data='+60')
    bt_30min = tg_api.InlineButtonBuilder('Полчаса', callback_data='+30')
    bt_15min = tg_api.InlineButtonBuilder('15 минут', callback_data='+15')
    kb_choose_time = tg_api.InlineMarkupBuilder([[bt_15min, bt_30min, bt_1h], [bt_3h, bt_day], [bt_month]])
    graph = GRAPH()
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
        restart.program(3)
    else:
        if proxy:
            proxy_str = f'http://{proxy}'
        else:
            proxy_str = None
        task_main = ioloop.create_task(main(proxy_str))
        try:
            ioloop.run_until_complete(task_main)
        except Exception as err:
            logging.critical(f'Restart caused: {type(err)}:{err}')
        finally:
            task_main.cancel()
            ioloop.stop()
            ioloop.close()
            restart.program(1)
else:
    logging.critical(f'__Name__ is NOT equal main! It is {__name__}')