#!/usr/bin/python3.6
import asyncio
import aiohttp
from inet import Proxy
import tg_api
from bot_handler import BotHandler
import logging
import restart
from os import name, path
from graph import GRAPH

if name == 'nt':
    path = path.dirname(__file__) + '/'
else:
    path = '/home/pi/bot/'

logging.basicConfig(filename=f'{path}bot.log',
                    format='%(asctime)s    %(levelname)s: %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S',
                    level=logging.INFO)

logging.info('Program started')

graph = GRAPH()
admin_id = ['196846654', '463145322']
# tkbot_token = '1061976169:AAFUJ1rnKXmhbMN5POAPk1DxdY0MPQZlwuk'
tkbot_token = '1050529824:AAHxUjGm7oCAPLD0jnbTC4CEM4_b_aYiB40'
kb_start = tg_api.KeyboardBuilder([['/now', '/graph'], ['/help']], one_time_keyboard=False)
kb_start2 = tg_api.KeyboardBuilder([['/now'], ['/graph']], one_time_keyboard=False)
kb_stat = tg_api.KeyboardBuilder([['/log']])
bt_1h = tg_api.InlineButtonBuilder('1 час', callback_data='+60')
bt_30min = tg_api.InlineButtonBuilder('Полчаса', callback_data='+30')
bt_15min = tg_api.InlineButtonBuilder('15 минут', callback_data='+15')
kb_choose_time = tg_api.InlineMarkupBuilder([[bt_15min, bt_30min, bt_1h]])


async def repeat(interval, func, *args, **kwargs):
    """Run func every interval seconds.

    If func has not finished before *interval*, will run again
    immediately when the previous iteration finished.

    *args and **kwargs are passed as the arguments to func.
    """
    while True:
        await asyncio.gather(
            func(*args, **kwargs),
            asyncio.sleep(interval),
        )


async def find_proxy():
    inet = Proxy(timeout=3,
                 site_to_test=f'https://api.telegram.org/bot{tkbot_token}/getMe',
                 filename=f'{path}proxy.txt')
    results, _ = await asyncio.wait([inet.test1(), inet.test2()])
    results = [i.result() for i in results]
    if not results[-1]:  # internet connection test
        return restart.program(5)
    elif results[-2]:  # telegram without proxy connection test
        return None
    else:
        results, _ = await asyncio.wait([inet.loader(), inet.broker_find(), inet.pub_find()])
        results = [i.result() for i in results]
        if results[-1]:
            return results[-1]
        elif results[-2]:
            return results[-2]
        elif results[-3]:
            return results[-3]
        else:
            return restart.program(1)


async def logic(bot):
    update = await bot.get_updates()
    if update is None:
        return None
    if 'callback_query' in update.keys():
        received_message = update['callback_query']['message']
        message_type = 'callback_query'
        data = update['callback_query']['data']
    else:
        received_message = update['message']
        message_type = list(received_message.keys())[4]
        if message_type == 'text':
            message_text = received_message['text']
            if message_text[0] == '/':
                message_type = 'command'
    user_id = str(received_message['chat']['id'])
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
                                                            '• для построения графика напиши /graph',
                                                   reply_markup=kb_start2))
        elif message_text == '/now':
            temperature = graph.read_csv('Temp', 1)['data'][0]
            pm25 = graph.read_csv('PM2.5', 1)['data'][0]
            pm10 = graph.read_csv('PM10', 1)['data'][0]
            pressure = graph.read_csv('Pres', 1)['data'][0]
            humidity = graph.read_csv('Humidity', 1)['data'][0]
            asyncio.ensure_future(bot.send_message(user_id, f'Температура: {temperature} °C\n'
                                                            f'Давление: {pressure} мм/рт.ст.\n'
                                                            f'Влажность: {humidity} %\n'
                                                            f'Частицы PM2.5: {pm25} мгр/м³\n'
                                                            f'Частицы PM10: {pm10} мгр/м³', ))
        elif message_text == '/graph':
            asyncio.ensure_future(bot.send_message(user_id, 'Выберите время:',
                                                   reply_markup=kb_choose_time))
        elif message_text == '/stat' and user_id in admin_id:
            asyncio.ensure_future(bot.send_message(user_id, f'Наконец то мой дорогой админ {user_name} '
                                                            f'добрался до статистики! Что интересует?',
                                                   reply_markup=kb_stat))
        elif message_text == '/log' and user_id in admin_id:
            asyncio.ensure_future(bot.send_file(user_id, f'{path}bot.log', reply_markup=kb_start2))
    elif message_type == 'text':
        print('pass')
        pass
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
        elif data[0] == '=':
            data = data[1:].split('+')
            if data[1] in ['15', '30', '60']:  # minutes
                asyncio.ensure_future(bot.send_photo(user_id,
                                                     graph.plot_minutes(
                                                         graph.read_csv(data[0], int(data[1])), data[0])
                                                     ))
    else:
        asyncio.ensure_future(bot.send_message(user_id, f'{message_type.capitalize()} messages are NOT '
                                                        f'supported!'))


async def main(best_proxy):
    logging.info('Main started!')
    session = aiohttp.ClientSession()
    tg_bot = BotHandler(tkbot_token, session, best_proxy)
    t1 = asyncio.ensure_future(repeat(0, logic, tg_bot))
    t2 = asyncio.ensure_future(repeat(60, graph.get_info, session))
    await t1
    await t2


if __name__ == '__main__':
    ioloop = asyncio.get_event_loop()
    proxy = ioloop.run_until_complete(find_proxy())
    if proxy:
        proxy = f'http://{proxy}'
    ioloop.create_task(main(proxy))
    ioloop.run_forever()
    ioloop.close()
