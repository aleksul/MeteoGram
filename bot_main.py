#!/usr/bin/python3.6
import asyncio
import aiohttp
from inet import Proxy
import tg_api
from bot_handler import BotHandler
import logging
import restart
from concurrent import futures
from os import name
from os import path
if name == 'nt':
    path = path.dirname(__file__)+'/'
else:
    path = '/home/pi/bot/'

logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.basicConfig(filename=f'{path}bot.log',
                    format='%(asctime)s    %(levelname)s: %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S',
                    level=logging.INFO)

logging.info('Program started')

admin_id = ['196846654']
tkbot_token = '1061976169:AAFUJ1rnKXmhbMN5POAPk1DxdY0MPQZlwuk'
kb_start = tg_api.KeyboardBuilder([['Как пользоваться?']])
kb_stat = tg_api.KeyboardBuilder([['Лог бота']])


async def find_proxy():
    internet = Proxy(timeout=3,
                     site_to_test=f'https://api.telegram.org/bot{tkbot_token}/getMe', filename=f'{path}proxy.txt')
    if await internet.test1():
        if not await internet.test2():
            proxy = await internet.loader()
            if proxy is None:
                done, pending = await asyncio.wait(internet.broker_find(), internet.pub_find(),
                                                   return_when=futures.FIRST_COMPLETED)
                for future in pending:
                    future.cancel()
                if done.result() is None:
                    proxy = await internet.broker_find()
                    if proxy is None:
                        proxy = await internet.pub_find()
                        if proxy is None:
                            return restart.program(0)
                else:
                    proxy = done.result()
        else:
            return None
    else:
        return restart.program(5)
    logging.info(f'Proxy: {proxy}')
    return proxy


async def logic(proxy):
    if proxy:
        proxy = f'http://{proxy}'
    else:
        proxy = None
    async with aiohttp.ClientSession() as session:
        bot = BotHandler(tkbot_token, session, proxy)
        new_offset = None
        previous_update = None
        logging.info("Main started!")
        while True:
            update = await bot.get_updates(new_offset)
            last_update = update[-1]
            if last_update == previous_update:
                continue
            previous_update = last_update
            last_update_id = last_update['update_id']
            received_message = last_update['message']
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
                    asyncio.ensure_future(bot.send_message(user_id, 'Пока что не прикрутили станцию :)'))
            new_offset = last_update_id + 1


if __name__ == '__main__':
    ioloop = asyncio.get_event_loop()
    logging.info('Got event loop')
    proxy = ioloop.run_until_complete(find_proxy())
    ioloop.run_until_complete(logic(proxy))
    ioloop.close()
