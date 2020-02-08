import aiohttp
import logging
import restart


class BotHandler:

    def __init__(self, token, session, proxy=None, timeout=20):
        self.token = token
        self.session = session
        self.proxy = proxy
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.tg_timeout = timeout
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.offset = None

    async def get_updates(self):
        params = {'timeout': self.tg_timeout}
        if self.offset:
            params.update(offset=self.offset)
        try:
            async with self.session.get(
                    f'https://api.telegram.org/bot{self.token}/getUpdates',
                    params=params, proxy=self.proxy) as resp:
                assert resp.status == 200
                result = await resp.json()
                result = result['result']
        except Exception as err:
            logging.error(f"Pull error: {type(err)}:{err}")
            return None
        else:
            self.offset = int(result[0]['update_id'])+1
            return result[0]

    async def send_message(self,
                           chat_id: str or int,
                           text: str,
                           parse_mode='Markdown',  # can be "HTML"
                           disable_notification=None,  # boolean
                           reply_to_message_id=None,  # integer
                           reply_markup=None):
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
        except Exception as err:
            logging.error(f"Send error: {type(err)}:{err}")
            return restart.program(1)
        else:
            return None

    async def send_photo(self, chat_id, read):
        '''
        with open(photo_path, 'rb') as f:
            read = f.read()
        '''
        params = dict(chat_id=chat_id, photo=read)
        try:
            async with self.session.post(
                    f'https://api.telegram.org/bot{self.token}/sendPhoto',
                    data=params, proxy=self.proxy) as resp:
                assert resp.status == 200
        except AssertionError:
            logging.warning('Assertion error!')
        except Exception as err:
            logging.error(f"Send photo error: {type(err)}:{err}")
            return restart.program(1)
        else:
            return None

    async def send_file(self, chat_id, file_path):
        with open(file_path, 'rb') as f:
            read = f.read()
        params = dict(chat_id=chat_id, document=read)
        try:
            async with self.session.post(
                    f'https://api.telegram.org/bot{self.token}/sendDocument',
                    data=params, proxy=self.proxy) as resp:
                assert resp.status == 200
        except AssertionError:
            logging.warning('Assertion error!')
        except Exception as err:
            logging.error(f"Send photo error: {type(err)}:{err}")
            return restart.program(1)
        else:
            return None
