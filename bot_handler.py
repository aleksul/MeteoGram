import requests
import logging
import restart
from time import sleep

proxy = None

class BotHandler:
    global proxy

    def __init__(self, token):
        global proxy
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)


    def get_updates(self, offset=None, timeout=30):
        global proxy
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        logging.debug('Getting updates...')
        try:
            resp = requests.get(self.api_url + method, params, proxies = proxy, timeout = 60)
        except Exception as err:
            logging.error("Pull error: {}".format(type(err)))
            sleep(5)
            restart.program()
        else:
            result_json = resp.json()['result']
            return result_json

    def send_message(self, chat_id, text, markup = None):
        global proxy
        params = {'chat_id': chat_id, 'text': text, 'reply_markup': markup}
        method = 'sendMessage'
        try:
            resp = requests.post(self.api_url + method, params, proxies = proxy, timeout = 60)
        except Exception as err:
            logging.error("Send error: {}".format(type(err)))
            sleep(5)
            restart.program()
        else:
            return resp

    def get_last_update(self):
        get_result = self.get_updates()
        if get_result is None:
            return self.get_last_update()
        else:
            if len(get_result) > 0:
                last_update = get_result[-1]
                logging.info("Last update: {}".format(last_update))
            else:
                last_update = None

            return last_update
