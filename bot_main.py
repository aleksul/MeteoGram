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
#tkbot_token = '1061976169:AAFUJ1rnKXmhbMN5POAPk1DxdY0MPQZlwuk'
tkbot_token = '1050529824:AAHxUjGm7oCAPLD0jnbTC4CEM4_b_aYiB40'
kb_start = tg_api.KeyboardBuilder([['Как пользоваться?']])
kb_stat = tg_api.KeyboardBuilder([['Лог бота']])
kb_choose_parameter = tg_api.KeyboardBuilder([['PM2.5', 'PM10'], ['Температура'], ['Давление', 'Влажность']])
kb_choose_time = tg_api.KeyboardBuilder([['Час']])


async def get_session():
    return aiohttp.ClientSession()


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
    while True:
        update = await bot.get_updates()
        if update is None:
            return None
        if not update:
            return None
        received_message = update['message']
        user_id = str(received_message['chat']['id'])
        user_name = received_message['chat']['first_name']
        message_type = list(received_message.keys())[4]
        if message_type != 'text':
            asyncio.ensure_future(bot.send_message(user_id, f'{message_type.capitalize()} messages are NOT '
                                                            f'supported!'))
        else:
            message_text = received_message['text']
            if message_text == '/start':
                asyncio.ensure_future(bot.send_message(user_id, f'Приветствую, {user_name}! \n'
                                                                f'Я бот, который поможет тебе '
                                                                f'узнать метеоданные в Троицке!',
                                                       reply_markup=kb_start))
            elif message_text == '/stat' and user_id in admin_id:
                asyncio.ensure_future(bot.send_message(user_id, f'Наконец то мой дорогой админ {user_name} '
                                                                f'добрался до статистики! Что интересует?',
                                                       reply_markup=kb_stat))
            elif message_text == 'Лог бота' and user_id in admin_id:
                asyncio.ensure_future(bot.send_file(user_id, f'{path}bot.log'))
            elif message_text == 'Как пользоваться?':
                asyncio.ensure_future(bot.send_message(user_id, 'Все чрезвычайно просто:\n'
                                                                '• для просмотра текущего состояния напиши /now\n'
                                                                '• для просмотра графика напиши /graph',
                                                       reply_markup=tg_api.ReplyKeyboardRemove))
            elif message_text == '/now':
                temperature = graph.read_csv('Temp', 1)[0]
                pm25 = graph.read_csv('PM2.5', 1)[0]
                pm10 = graph.read_csv('PM10', 1)[0]
                pressure = graph.read_csv('Pres', 1)[0]
                humidity = graph.read_csv('Humidity', 1)[0]
                asyncio.ensure_future(bot.send_message(user_id, f'Температура: {temperature} °C\n'
                                                                f'Давление: {pressure} мм/рт.ст.\n'
                                                                f'Влажность: {humidity} %\n'
                                                                f'Частицы PM2.5: {pm25} мгр/м³\n'
                                                                f'Частицы PM10: {pm10} мгр/м³'))
            elif message_text == '/graph':
                asyncio.ensure_future(bot.send_message(user_id, 'Выберите время:',
                                                       reply_markup=kb_choose_time))
            elif message_text == 'Час':
                asyncio.ensure_future(bot.send_message(user_id, 'Выберите параметр:',
                                                       reply_markup=kb_choose_parameter))
            elif message_text == 'PM2.5':
                asyncio.ensure_future(bot.send_photo(user_id,
                                                     graph.plot_minutes(
                                                         graph.read_csv('PM2.5', 60), 'PM2.5')
                                                     )
                                      )
            elif message_text == 'PM10':
                asyncio.ensure_future(bot.send_photo(user_id,
                                                     graph.plot_minutes(
                                                         graph.read_csv('PM10', 60), 'PM10')
                                                     )
                                      )
            elif message_text == 'Температура':
                asyncio.ensure_future(bot.send_photo(user_id,
                                                     graph.plot_minutes(
                                                         graph.read_csv('Temp', 60), 'Temp')
                                                     )
                                      )
            elif message_text == 'Давление':
                asyncio.ensure_future(bot.send_photo(user_id,
                                                     graph.plot_minutes(
                                                         graph.read_csv('Pres', 60), 'Pres')
                                                     )
                                      )
            elif message_text == 'Влажность':
                asyncio.ensure_future(bot.send_photo(user_id,
                                                     graph.plot_minutes(
                                                         graph.read_csv('Humidity', 60), 'Humidity')
                                                     )
                                      )

if __name__ == '__main__':
    ioloop = asyncio.get_event_loop()
    logging.info('Got event loop')
    proxy = ioloop.run_until_complete(find_proxy())
    if proxy:
        proxy = f'http://{proxy}'
    else:
        proxy = None
    session = ioloop.run_until_complete(get_session())
    tg_bot = BotHandler(tkbot_token, session, proxy)
    ioloop.create_task(logic(tg_bot))
    ioloop.create_task(graph.get_info(session))
    ioloop.run_forever()
    ioloop.close()
