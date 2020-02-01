import asyncio
import aiohttp
import logging
from aiohttp import FormData
import restart
import json


class BotHandler:

    def __init__(self, token, session, proxy=None, timeout=25):
        self.token = token
        self.session = session
        self.proxy = proxy
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.tg_timeout = timeout-10
        self.api_url = f"https://api.telegram.org/bot{token}/"

    async def get_updates(self, offset=None):
        params = {'timeout': self.tg_timeout, 'offset': offset}
        logging.debug('Getting updates...')
        try:
            async with self.session.get(
                    f'https://api.telegram.org/bot{self.token}/getUpdates',
                    data=params, proxy=self.proxy) as resp:
                assert resp.status == 200
                result = await resp.json()
                result = result['result']
        except Exception as err:
            logging.error(f"Pull error: {type(err)}:{err}")
            return None
        else:
            return result

    async def send_message(self, message):
        try:
            async with self.session.post(
                    f'https://api.telegram.org/bot{self.token}/sendMessage',
                    data=message, proxy=self.proxy) as resp:
                assert resp.status == 200
        except AssertionError:
            logging.warning('Assertion error, will try again in 5 seconds')
            await asyncio.sleep(5)
            return self.send_message(message)
        except Exception as err:
            logging.error(f"Send error: {type(err)}:{err}")
            return restart.program(0)
        else:
            return None

    async def send_photo(self, chat_id, photo_path):
        with open(photo_path, 'rb') as f:
            read = f.read()
        parametrs = dict(chat_id=chat_id, photo=read)
        try:
            async with self.session.post(
                    f'https://api.telegram.org/bot{self.token}/sendPhoto',
                    data=parametrs, proxy=self.proxy) as resp:
                assert resp.status == 200
        except AssertionError:
            logging.warning('Assertion error!!')
        except Exception as err:
            logging.error(f"Send photo error: {type(err)}:{err}")
            return restart.program(1)
        else:
            return None

    async def get_last_update(self):
        get_result = await self.get_updates()
        if get_result is None:
            return await self.get_last_update()
        else:
            if len(get_result) > 0:
                last_update = get_result[-1]
            else:
                last_update = None
            return last_update
