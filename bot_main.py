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


def time_to_str(time: str):
    if time == '15':
        return 'последние 15 минут'
    elif time == '30':
        return 'последние полчаса'
    elif time == '60':
        return 'последний час'
    elif time == '180':
        return 'последние 3 часа'
    elif time == 'day':
        return 'день'
    elif time == 'month':
        return 'месяц'
    else:
        logging.error(f'Wrong time: {time}')
        return None


async def logic(bot):
    global RESTART_FLAG, LAST_USERS

    # getting update

    update = await bot.get_updates()
    if update is None:
        LAST_USERS.clear()  # if no update comes - clear all the dict
        return None

    # parsing update
    text, command, admin_command, reply_to_message, callback_query = False, False, False, False, False
    one_mssg_rp = False
    message_text, reply_text, data = '', '', ''
    reply_message_id, message_id = 0, 0
    callback_id = ''

    if 'callback_query' in update.keys():
        callback_query = True
        received_message = update['callback_query']['message']
        data = update['callback_query']['data']
        user_id = str(received_message['chat']['id'])
        message_id = received_message['message_id']
        callback_id: str = update['callback_query']['id']
    else:
        received_message = update['message']
        user_id = str(received_message['chat']['id'])
        message_type = list(received_message.keys())[4]
        if message_type == 'text':
            message_text = received_message['text']
            text = True
            if message_text[0] == '/':
                command = True
                if user_id in ADMIN_ID and message_text in ADMIN_COMMANDS:
                    admin_command = True
        elif message_type == 'reply_to_message':
            reply_to_message = True
            message_text = received_message['text']
            reply_message_id = int(received_message['reply_to_message']['message_id'])
            reply_text = received_message['reply_to_message']['text']
            message_id = int(received_message['message_id'])
            if message_id-reply_message_id == 1:
                one_mssg_rp = True

    user_name = received_message['chat']['first_name']

    # working with black_list

    if user_id in ban.ids:
        return None

    now = datetime.now()
    if user_id in LAST_USERS.keys():  # if user already in dict
        LAST_USERS[user_id][0] += 1  # +1 update
        LAST_USERS[user_id][2] = now  # change last update time

        # check if its necessary to add user to black_list

        last_updates = LAST_USERS[user_id]
        num_of_updates = last_updates[0]
        spam_bool = (last_updates[2] - last_updates[1]) / num_of_updates <= zero_seconds  # how fast new messages coming
        if num_of_updates == 30 and spam_bool:
            logging.debug(f"Pretend that user {user_name} (id: {user_id}) is spamming!")
            return asyncio.ensure_future(bot.send_message(user_id, 'Пожалуйста, не спамьте!\n'
                                                                   'У меня вообще-то черный список есть...',
                                                          reply_markup=tg_api.ReplyKeyboardRemove))
        elif num_of_updates == 40 and spam_bool:
            return asyncio.ensure_future(bot.send_message(user_id, 'Последний раз предупреждаю!',
                                                          reply_markup=tg_api.ReplyKeyboardRemove))
        elif num_of_updates == 49 and spam_bool:
            return asyncio.ensure_future(bot.send_message(user_id, 'Еще одно сообщение и в бан!',
                                                          reply_markup=tg_api.ReplyKeyboardRemove))
        elif num_of_updates >= 50 and spam_bool:
            ban.add(user_id)
            logging.info(f'User {user_name} (id: {user_id}) was added to blacklist')
            LAST_USERS.pop(user_id)  # delete user from dict
            return asyncio.ensure_future(bot.send_message(user_id, 'Вы были добавлены в черный список.'))
        elif num_of_updates > 30 and spam_bool:
            return None  # don't answer anything if we pretend that user is spamming

    elif user_id not in ADMIN_ID:  # if user isn't admin...
        # add user to the dict with 3 parameters: number of updates, time of the first update, time of the last one
        LAST_USERS.update({user_id: [1, now, now]})

    # working with commands

    if admin_command:
        if '/admin' == message_text:
            return asyncio.ensure_future(bot.send_message(user_id, f'Наконец то мой дорогой админ {user_name} '
                                                                   f'добрался до раздела админских возможностей!\n\n'
                                                                   f'• Напишите /log для получения файла логов,'
                                                                   f' /clear_log для того чтобы его отчистить\n'
                                                                   f'• Напишите /restart для '
                                                                   f'принудительной перезагрузки\n'
                                                                   f'• Напишите /black_list для '
                                                                   f'работы с черным списком\n'
                                                                   f'• Напишите /back для '
                                                                   f'возврашения стандартной клавиатуры',
                                                          reply_markup=kb_admin))
        elif '/log' == message_text:
            return asyncio.ensure_future(bot.send_file(user_id, f'{path}bot.log', 'log.txt'))
        elif '/restart' == message_text:
            shuffle(restart_str_list)
            kb_restart = []
            for i in list(restart_str_list):
                kb_restart.append([i])
            RESTART_FLAG = 1
            return asyncio.ensure_future(bot.send_message(user_id, 'Вы уверены?',
                                                          reply_markup=tg_api.KeyboardBuilder(kb_restart)))
        elif '/clear_log' == message_text:
            with open(path + 'bot.log', 'w'):  # log clearing
                pass
            logging.info('Cleared log')
            return asyncio.ensure_future(bot.send_message(user_id, 'Лог был отчищен!', reply_markup=kb_admin))
        elif '/black_list' == message_text:
            return asyncio.ensure_future(bot.send_message(user_id, 'Что сделать?', reply_markup=bl_keyboard))
        elif '/back' == message_text:
            return asyncio.ensure_future(
                bot.send_message(user_id, 'Возвращаю нормальную клавиатуру :)', reply_markup=kb_start2))

    elif command:
        if '/start' == message_text:
            return asyncio.ensure_future(bot.send_message(user_id, f'Приветствую, {user_name}! \n'
                                                                   f'Я бот, который поможет тебе '
                                                                   f'узнать метеоданные в Троицке!',
                                                          reply_markup=kb_start))
        elif '/help' == message_text:
            return asyncio.ensure_future(bot.send_message(user_id, 'Все чрезвычайно просто:\n'
                                                                   '• для просмотра текущего состояния напиши /now\n'
                                                                   '• для построения графика напиши /graph\n'
                                                                   '• для просмотра сырого файла напиши /raw\n\n'
                                                                   'Интересуют подробности отображаемых измерений?\n'
                                                                   'Напиши /info',
                                                          reply_markup=kb_start2))
        elif '/now' == message_text:
            now = graph.read_last()
            return asyncio.ensure_future(bot.send_message(user_id, f'Данные собраны в {now["Time"]}\n\n'
                                                                   f'Температура: {now["Temp"]} °C\n'
                                                                   f'Давление: {now["Pres"]} мм/рт.ст.\n'
                                                                   f'Влажность: {now["Humidity"]} %\n'
                                                                   f'Частицы PM2.5: {now["PM2.5"]} мкгр/м³\n'
                                                                   f'Частицы PM10: {now["PM10"]} мкгр/м³'))
        elif '/raw' == message_text:
            keyboard = [[]]
            strings_num = 0
            for i in graph.dates():
                if len(keyboard[strings_num]) > 2:
                    keyboard.append([])
                    strings_num += 1
                pretty_date = i.split('-')
                pretty_date = pretty_date[0] + '.' + pretty_date[1] + '.' + pretty_date[2]
                keyboard[strings_num].append(
                    tg_api.InlineButtonBuilder(pretty_date, callback_data='-raw+' + i)
                )
            if keyboard[0]:
                return asyncio.ensure_future(bot.send_message(user_id, 'Выберите дату:',
                                                              reply_markup=tg_api.InlineMarkupBuilder(keyboard)))
            else:
                return asyncio.ensure_future(bot.send_message(user_id, 'Нет данных :('))
        elif '/graph' == message_text:
            return asyncio.ensure_future(bot.send_message(user_id, 'Выберите временной промежуток:',
                                                          reply_markup=kb_choose_time))
        elif '/info' == message_text:
            return asyncio.ensure_future(bot.send_message(user_id, 'Где производится замер?\n'
                                                                   'Метеостанция располгается по адресу: '
                                                                   'г.Москва, г.Троицк, '
                                                                   'Сиреневый бульвар, д.1, снаружи "Точки Кипения"\n\n'
                                                                   'Как определяется время суток на графике дня?\n'
                                                                   '4:00-10:00 - утро\n'
                                                                   '10:00-16:00 - день\n'
                                                                   '16:00-22:00 - вечер\n'
                                                                   '22:00-4:00 - ночь\n\n'
                                                                   'Что такое частицы PM2.5 и PM10?\n'
                                                                   'Это мелкодисперсные частицы пыли, которые, '
                                                                   'буквально, "витают в воздухе". '
                                                                   'Из-за их малых размеров '
                                                                   '(2.5 мкм и 10 мкм соответсвенно) '
                                                                   'и веса они практически не осядают, '
                                                                   'таким образом загрязняя'
                                                                   ' воздух, которым мы дышим.\n'
                                                                   'Согласно ВОЗ, среднесуточный уровень этих частиц '
                                                                   'не должен быть больше 25 мкгр/м³\n'
                                                                   'Подробнее можно прочитать, например, здесь:\n'
                                                                   'https://habr.com/ru/company/tion/blog/396111/',
                                                          reply_markup=kb_start2))
        else:
            return asyncio.ensure_future(
                bot.send_message(user_id, 'Неверная команда!\nДля вывода подсказки напишите /help'))

    elif text:
        if user_id in ADMIN_ID and message_text == 'Да, перезапуск!' and RESTART_FLAG:
            RESTART_FLAG = 0
            await bot.send_message(user_id, 'Перезапускаюсь...', reply_markup=kb_admin)
            raise restart.UserRestart
        elif user_id in ADMIN_ID and RESTART_FLAG:
            RESTART_FLAG = 0
            return asyncio.ensure_future(bot.send_message(user_id, 'Перезапуск отменен', reply_markup=kb_admin))
        else:
            return asyncio.ensure_future(bot.send_message(user_id, 'Помочь с командами?\nНапиши /help'))

    elif reply_to_message:
        if one_mssg_rp and user_id in ADMIN_ID:
            if reply_text == bl_add_text:
                asyncio.ensure_future(bot.delete_message(user_id, reply_message_id))
                if message_text.isdigit() and len(message_text) == 9:
                    if message_text not in ban.ids:
                        ban.add(message_text)
                        return asyncio.ensure_future(bot.send_message(user_id, f'Пользователь (id: {message_text}) '
                                                                               f'был добавлен в черный список',
                                                                      reply_markup=kb_admin))
                    else:
                        return asyncio.ensure_future(bot.send_message(user_id, f"Пользователь (id: {message_text}) уже "
                                                                               f"в черном списке",
                                                                      reply_markup=kb_admin))
                else:
                    return asyncio.ensure_future(bot.send_message(user_id, 'Id введен неверно! Он должен содержать'
                                                                           ' 9 цифр, и ничего более!',
                                                                  reply_markup=kb_admin))
            elif reply_text == bl_del_text:
                asyncio.ensure_future(bot.delete_message(user_id, reply_message_id))
                if message_text.isdigit() and len(message_text) == 9:
                    if message_text in ban.ids:
                        ban.remove(message_text)
                        return asyncio.ensure_future(bot.send_message(user_id, f'Пользователь (id: {message_text}) '
                                                                               f'был удален из черного списка',
                                                                      reply_markup=kb_admin))
                    else:
                        return asyncio.ensure_future(bot.send_message(user_id, f"Пользователь (id: {message_text}) не "
                                                                               f"в черном списке",
                                                                      reply_markup=kb_admin))
                else:
                    return asyncio.ensure_future(bot.send_message(user_id, 'Id введен неверно! Он должен содержать'
                                                                           ' 9 цифр, и ничего более!',
                                                                  reply_markup=kb_admin))
            else:
                return asyncio.ensure_future(bot.send_message(user_id, 'Помочь с командами?\nНапиши /help'))
        else:
            return asyncio.ensure_future(bot.send_message(user_id, 'Помочь с командами?\nНапиши /help'))

    elif callback_query:
        if data[0] == '+':
            bt_pm25 = tg_api.InlineButtonBuilder('Частицы PM2.5', callback_data='=PM2.5' + data)
            bt_pm10 = tg_api.InlineButtonBuilder('Частицы PM10', callback_data='=PM10' + data)
            bt_temp = tg_api.InlineButtonBuilder('Температура', callback_data='=Temp' + data)
            bt_pres = tg_api.InlineButtonBuilder('Давление', callback_data='=Pres' + data)
            bt_humidity = tg_api.InlineButtonBuilder('Влажность', callback_data='=Humidity' + data)
            kb_choose_parameter = tg_api.InlineMarkupBuilder([[bt_pm25, bt_pm10], [bt_temp], [bt_pres, bt_humidity]])
            return asyncio.ensure_future(bot.edit_message(user_id, message_id, text='Выберите параметр:',
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
                if keyboard[0]:
                    return asyncio.ensure_future(bot.edit_message(user_id, message_id, text='Выберите дату:',
                                                                  reply_markup=tg_api.InlineMarkupBuilder(keyboard)))
                else:
                    asyncio.ensure_future(bot.delete_message(user_id, message_id))
                    asyncio.ensure_future(bot.callback_answer(callback_id, text='Нет данных :(', show_alert=True))
            elif data.split('+')[0] == '-raw':
                asyncio.ensure_future(bot.delete_message(user_id, message_id))
                return asyncio.ensure_future(bot.send_file(user_id,
                                                           path + '/' + 'data' + '/' + data.split('+')[1] + '.csv',
                                                           filename=data.split('+')[1] + '.txt',
                                                           reply_markup=kb_start2))

        elif data[0] == '=':
            data = data[1:].split('+')
            asyncio.ensure_future(bot.delete_message(user_id, message_id))

            if data[1] in ['15', '30', '60', '180']:  # minutes
                plot_data = graph.read_csv_timedelta(data[0], datetime.now(),
                                                     datetime.now() - timedelta(minutes=int(data[1])))
                if plot_data:
                    photo = graph.plot_minutes(plot_data, data[0])
                    if photo:
                        param_str = graph.parameter_to_str(data[0]).capitalize()
                        return asyncio.ensure_future(bot.send_photo(user_id, photo,
                                                                    caption=f'{param_str} за'
                                                                            f' {time_to_str(data[1])}'))
                    else:
                        return asyncio.ensure_future(
                            bot.callback_answer(callback_id, text='За этот период нет данных :(',
                                                show_alert=True))
                else:
                    return asyncio.ensure_future(bot.callback_answer(callback_id, text='За этот период нет данных :(',
                                                                     show_alert=True))

            elif data[1] == 'day':  # one day
                date = data[2].split('-')
                date = [int(i) for i in date]
                date1 = datetime(date[2], date[1], date[0], 0, 0, 0)
                date2 = datetime(date[2], date[1], date[0], 23, 59, 59)
                plot_data = graph.read_csv_timedelta(data[0], date1, date2)
                if plot_data:
                    photo = graph.plot_day(plot_data, data[0])
                    if photo:
                        param_str = graph.parameter_to_str(data[0]).capitalize()
                        return asyncio.ensure_future(bot.send_photo(user_id, photo,
                                                                    caption=f'{param_str} за: '
                                                                            f'{date[0]}.{date[1]}.{date[2]}')
                                                     )
                    else:
                        return asyncio.ensure_future(
                            bot.callback_answer(callback_id, text='За этот период нет данных :(',
                                                show_alert=True))
                else:
                    return asyncio.ensure_future(bot.callback_answer(callback_id, text='За этот период нет данных :(',
                                                                     show_alert=True))

            elif data[1] == 'month':  # month
                plot_data = graph.read_month(data[0])
                photo = graph.plot_month(plot_data, data[0])
                if photo:
                    param_str = graph.parameter_to_str(data[0]).capitalize()
                    return asyncio.ensure_future(bot.send_photo(user_id, photo, caption=f'{param_str} за последний '
                                                                                        f'месяц'))
                else:
                    return asyncio.ensure_future(bot.callback_answer(callback_id, text='За этот период нет данных :(',
                                                                     show_alert=True))

        elif data[0] == '_':
            data = data[1:].split('+')
            asyncio.ensure_future(bot.callback_answer(callback_id))
            if data[1] == 'add':
                return asyncio.ensure_future(bot.send_message(user_id, bl_add_text,
                                                              reply_markup=tg_api.Force_Reply))
            elif data[1] == 'del':
                if ban.ids:
                    return asyncio.ensure_future(bot.send_message(user_id, bl_del_text,
                                                                  reply_markup=tg_api.Force_Reply))
                else:
                    return asyncio.ensure_future(bot.send_message(user_id, 'Черный список пуст!',
                                                                  reply_markup=kb_admin))
            elif data[1] == 'ids':
                if ban.ids:
                    pretty_ids = ''
                    for i in ban.ids:
                        pretty_ids += (i + ', ')
                    pretty_ids = pretty_ids[:-2]
                    return asyncio.ensure_future(bot.send_message(user_id, f'Все id:  {pretty_ids}',
                                                                  reply_markup=kb_admin))
                else:
                    return asyncio.ensure_future(bot.send_message(user_id, 'Черный список пуст!',
                                                                  reply_markup=kb_admin))

    else:
        return asyncio.ensure_future(bot.send_message(user_id, 'Данный тип данных не поддерживается'))


async def aio_session(proxy_local):
    async with aiohttp.ClientSession() as session:
        tg_bot = BotHandler(tkbot_token, session, proxy_local)
        minute = ioloop.time()
        task_bot = asyncio.ensure_future(logic(tg_bot), loop=ioloop)
        task_get_info = asyncio.ensure_future(graph.get_info(session), loop=ioloop)
        while True:
            if task_bot.done():  # check if our task done
                task_bot.result()  # will raise error if task finished incorrectly
                task_bot = asyncio.ensure_future(logic(tg_bot), loop=ioloop)
            if task_get_info.done():
                task_get_info.result()
            if ioloop.time() - minute >= 60.0:
                minute += 60.0  # maybe we have waited a bit more than expected but this trick will compensate it
                task_get_info = asyncio.ensure_future(graph.get_info(session), loop=ioloop)
            await asyncio.sleep(0)  # give control back to event loop


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

    RESTART_FLAG = 0
    restart_str_list = ['Нет конечно!', 'Да, перезапуск!', 'Нет!', 'Неееет!']

    tkbot_token = '1012565455:AAGctwGzz0LRlucqZiiEIvchtLhJjd1Fqdw'
    # tkbot_token = '1061976169:AAFUJ1rnKXmhbMN5POAPk1DxdY0MPQZlwuk'

    kb_start = tg_api.KeyboardBuilder([['/now', '/graph', '/raw'], ['/help']], one_time_keyboard=False)
    kb_start2 = tg_api.KeyboardBuilder([['/now'], ['/graph', '/raw']], one_time_keyboard=False)

    kb_admin = tg_api.KeyboardBuilder([['/log', '/restart'], ['/clear_log', '/black_list'], ['/back']],
                                      one_time_keyboard=False)

    bt_month = tg_api.InlineButtonBuilder('Месяц', callback_data='+month')
    bt_day = tg_api.InlineButtonBuilder('День', callback_data='-day')
    bt_3h = tg_api.InlineButtonBuilder('3 часа', callback_data='+180')
    bt_1h = tg_api.InlineButtonBuilder('1 час', callback_data='+60')
    bt_30min = tg_api.InlineButtonBuilder('Полчаса', callback_data='+30')
    bt_15min = tg_api.InlineButtonBuilder('15 минут', callback_data='+15')
    kb_choose_time = tg_api.InlineMarkupBuilder([[bt_15min, bt_30min, bt_1h], [bt_3h, bt_day], [bt_month]])

    graph = GRAPH('192.168.0.175', data_path=path + 'data/', timeout=10)

    ban = BlackList(file_path=path + 'ban_list.dat')
    LAST_USERS = {}
    zero_seconds = timedelta(seconds=0.5)
    bl_add = tg_api.InlineButtonBuilder('Добавить', callback_data='_bl+add')
    bl_add_text = 'В ответ на это сообщение напишите id пользователя, которого необходимо добавить:'
    bl_del = tg_api.InlineButtonBuilder('Удалить', callback_data='_bl+del')
    bl_del_text = 'В ответ на это сообщение напишите id пользователя, которого необходимо удалить:'
    bl_ids = tg_api.InlineButtonBuilder('Просмотреть все id', callback_data='_bl+ids')
    bl_keyboard = tg_api.InlineMarkupBuilder([[bl_add, bl_del], [bl_ids]])

    inet = Proxy(timeout=3,
                 filename=f'{path}proxy.dat',
                 site_to_test=f'https://api.telegram.org/bot{tkbot_token}/getMe')

    ioloop = asyncio.get_event_loop()
    task_proxy = ioloop.create_task(find_proxy())
    try:
        proxy = ioloop.run_until_complete(task_proxy)
    except Exception as err:
        logging.critical(f'Restart caused: {type(err)}:{err}')
        task_proxy.cancel()
        ioloop.stop()
        ioloop.close()
        restart.program(path + 'bot_main.py', 10)
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
            restart.program(path + 'bot_main.py', 10)
else:
    logging.critical(f'__Name__ is NOT equal main! It is {__name__}')
