#!/usr/bin/python3.6
import asyncio
from typing import Optional, Any

from inet import Proxy
from bot_handler import *
from tg_api import *
import logging
import restart
from concurrent import futures

# import telegram

logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.basicConfig(filename='/home/pi/bot/bot.log',
                    format='%(asctime)s    %(levelname)s: %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S',
                    level=logging.INFO)

logging.info('Program started')

admin_id = '196846654'
eos_token = "1012565455:AAGctwGzz0LRlucqZiiEIvchtLhJjd1Fqdw"
test_token = "1050529824:AAHxUjGm7oCAPLD0jnbTC4CEM4_b_aYiB40"


async def startup():
    internet = Proxy(timeout=3,
                     site_to_test=f'https://api.telegram.org/bot{test_token}/getMe')
    if await internet.is_internet_connected():
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
                        restart.program(0)
            else:
                proxy = done.result()
    else:
        restart.program(5)
    return proxy


def build_keyboards():
    key1 = KeyBuilder([['HI', 'Wassup?'], ['BYE']])
    key1 = key1.build()
    markup1 = KeyboardBuilder(key1)
    markup1 = markup1.build()

    but1 = InlineButtonBuilder('кнопка 1', callback_data='/1')
    but1 = but1.build()
    but2 = InlineButtonBuilder('trashbox', url='http://trashbox.ru')
    but2 = but2.build()
    but3 = InlineButtonBuilder('pay 2000р', callback_data='pay', pay=True)
    but3 = but3.build()
    markup2 = InlineMarkupBuilder([[but1], [but2, but3]])
    markup2 = markup2.build()


async def logic():
    new_offset = None
    logging.info("Main started!")
    while True:
        eos_bot.get_updates(new_offset)

        last_update = eos_bot.get_last_update()
        if last_update is None:
            continue
        last_update_id = last_update['update_id']
        if 'message' in last_update.keys():
            last_chat_text = last_update['message']['text']
            last_chat_id = last_update['message']['chat']['id']
            last_chat_name = last_update['message']['chat']['first_name']
        elif 'callback_query' in last_update.keys():
            last_chat_text = last_update['callback_query']['data']
            last_chat_id = last_update['callback_query']['message']['chat']['id']
            last_chat_name = last_update['callback_query']['message']['chat']['first_name']

        if last_chat_text.lower() == '/start':
            eos_bot.send_message(last_chat_id, 'Приветствую, {}.'.format(last_chat_name), markup=ReplyKeyboardRemove)
        elif last_chat_text.lower() == '/new':
            eos_bot.send_message(last_chat_id, 'New, {}.'.format(last_chat_name), markup=markup2)
        elif last_chat_text.lower() == '/kb':
            eos_bot.send_message(last_chat_id, 'New, {}.'.format(last_chat_name), markup=markup1)
        new_offset = last_update_id + 1


if __name__ == '__main__':
    ioloop = asyncio.get_event_loop()
    proxy = ioloop.run_until_complete(startup())

    ioloop.close()
