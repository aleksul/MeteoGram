import asyncio
import aiohttp
import logging

from aiohttp import FormData

from restart import SendError, GetUpdatesError


class BotHandler:
    def __init__(self, token, session, proxy=None, timeout=20):
        self.token = token
        self.session = session
        self.proxy = proxy
        self.timeout = aiohttp.ClientTimeout(total=timeout+3)
        self.tg_timeout = timeout
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.offset = None

    async def get_updates(self, bad_updates=0):
        params = {'timeout': self.tg_timeout}
        if self.offset:
            params.update(offset=self.offset)
        try:
            async with self.session.get(
                    f'https://api.telegram.org/bot{self.token}/getUpdates',
                    params=params, proxy=self.proxy, timeout=self.timeout) as resp:
                assert resp.status == 200
                result = await resp.json()
                result = result['result']
        except Exception as err:
            logging.error(f"Pull error: {type(err)}:{err}")
            if bad_updates >= 5:
                logging.critical('Too many bad updates!')
                raise GetUpdatesError
            else:
                bad_updates += 1
                return await self.get_updates(bad_updates=bad_updates)
        else:
            if result:
                self.offset = int(result[0]['update_id'])+1
                return result[0]
            else:
                return None

    async def send_message(self,
                           chat_id: str or int,
                           text: str,
                           parse_mode='Markdown',  # can be "HTML"
                           disable_notification=None,  # boolean
                           reply_to_message_id=None,  # integer
                           reply_markup=None,
                           bad_asserts=0):
        dictionary = dict(chat_id=chat_id, text=text)
        if parse_mode != 'Markdown':
            dictionary.update(parse_mode=parse_mode)
        if disable_notification:
            dictionary.update(disable_notification=disable_notification)
        if reply_to_message_id:
            dictionary.update(reply_to_message_id=reply_to_message_id)
        if reply_markup:
            dictionary.update(reply_markup=reply_markup)
        try:
            async with self.session.post(
                    f'https://api.telegram.org/bot{self.token}/sendMessage',
                    data=dictionary, proxy=self.proxy) as resp:
                assert resp.status == 200
        except AssertionError:
            logging.warning('Assertion error!')
            if bad_asserts >= 3:
                logging.critical('Too many bad asserts (send message)!')
                raise SendError
            else:
                bad_asserts += 1
                await asyncio.sleep(1)
                return await self.send_message(chat_id, text, parse_mode=parse_mode,
                                               disable_notification=disable_notification,
                                               reply_to_message_id=reply_to_message_id,
                                               reply_markup=reply_markup,
                                               bad_asserts=bad_asserts)
        except Exception as err:
            logging.critical(f"Send error: {type(err)}:{err}")
            raise SendError
        else:
            return None

    async def send_photo(self, chat_id, read, caption=None, reply_markup=None, bad_asserts=0):
        params = dict(chat_id=chat_id)
        if reply_markup:
            params.update(reply_markup=reply_markup)
        if caption:
            params.update(caption=caption)
        data = FormData()
        data.add_field('photo',
                       read)
        try:
            async with self.session.post(
                    f'https://api.telegram.org/bot{self.token}/sendPhoto',
                    params=params, data=data,
                    proxy=self.proxy) as resp:
                assert resp.status == 200
        except AssertionError:
            logging.warning('Assertion error!')
            if bad_asserts >= 3:
                logging.critical('Too many bad asserts (send photo)!')
                raise SendError
            else:
                bad_asserts += 1
                await asyncio.sleep(1)
                return await self.send_photo(chat_id, read, reply_markup=reply_markup, bad_asserts=bad_asserts)
        except Exception as err:
            logging.critical(f"Send photo error: {type(err)}:{err}")
            raise SendError
        else:
            return None

    async def send_file(self, chat_id, file_path, filename, reply_markup=None, bad_asserts=0):
        with open(file_path, 'rb') as f:
            read = f.read()
        params = dict(chat_id=chat_id)
        if reply_markup:
            params.update(reply_markup=reply_markup)
        data = FormData()
        data.add_field('document',
                       read,
                       filename=filename)
        try:
            async with self.session.post(
                    f'https://api.telegram.org/bot{self.token}/sendDocument',
                    params=params, data=data,
                    proxy=self.proxy) as resp:
                assert resp.status == 200
        except AssertionError:
            logging.warning('Assertion error!')
            if bad_asserts >= 3:
                logging.critical('Too many bad asserts (send file)!')
                raise SendError
            else:
                bad_asserts += 1
                await asyncio.sleep(1)
                return await self.send_file(chat_id, file_path, filename,
                                            reply_markup=reply_markup, bad_asserts=bad_asserts)
        except Exception as err:
            logging.critical(f"Send file error: {type(err)}:{err}")
            raise SendError
        else:
            return None
