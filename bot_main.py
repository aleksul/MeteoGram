#!/usr/bin/python3.6
import asyncio
import aiohttp
from inet import Proxy
import tg_api
from bot_handler import BotHandler
import logging
import restart
from concurrent import futures

logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.basicConfig(filename='/home/pi/bot/bot.log',
                    format='%(asctime)s    %(levelname)s: %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S',
                    level=logging.INFO)

logging.info('Program started')

admin_id = '196846654'
eos_token = "1012565455:AAGctwGzz0LRlucqZiiEIvchtLhJjd1Fqdw"
test_token = "1050529824:AAHxUjGm7oCAPLD0jnbTC4CEM4_b_aYiB40"

kb = tg_api.KeyboardBuilder([['Hi!', 'How r u?'], ['ILY']])
inbt1 = tg_api.InlineButtonBuilder('Hi', callback_data='1', pay=True)
inbt2 = tg_api.InlineButtonBuilder('Bye', callback_data='2')
inkb = tg_api.InlineMarkupBuilder([[inbt1, inbt2]])


async def find_proxy():
    internet = Proxy(timeout=3,
                     site_to_test=f'https://api.telegram.org/bot{test_token}/getMe')
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
    proxy = f'http://{proxy}'
    async with aiohttp.ClientSession() as session:
        bot = BotHandler(test_token, session, proxy)
        new_offset = None
        logging.info("Main started!")
        while True:
            await bot.get_updates(new_offset)
            last_update = await bot.get_last_update()
            if last_update is None:
                continue
            last_update_id = last_update['update_id']
            received_message = last_update['message']
            user_id = str(received_message['chat']['id'])
            user_name = received_message['chat']['first_name']
            message_type = list(received_message.keys())[4]
            if message_type != 'text':
                mssg = tg_api.Message(user_id, f'{message_type.capitalize()} messages are NOT supported!')
                await bot.send_message(mssg)
            else:
                message_text = received_message['text']
                if message_text == '/start':
                    mssg = tg_api.Message(user_id, f'Приветствую, {user_name}!'
                                                   f'Я бот, который поможет тебе узнать')
                print(message_text)
                mssg = tg_api.Message(user_id, 'Hi')
                await bot.send_message(mssg)
            new_offset = last_update_id + 1


if __name__ == '__main__':
    ioloop = asyncio.get_event_loop()
    logging.info('Got event loop')
    proxy = ioloop.run_until_complete(find_proxy())
    ioloop.run_until_complete(logic(proxy))
    ioloop.close()
