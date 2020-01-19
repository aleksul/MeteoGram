import requests
import proxy_finder
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
        logging.info("Trying request without proxy")
        try:
            response = requests.get(self.api_url+'getMe', timeout = 15, proxies = proxy)
        except requests.exceptions.ConnectionError:
            logging.warning("Connection error...")
            if proxy_finder.InternetConnection():
                logging.info("OK, we have interet but also telegram doesn't work")
                logging.info("Let's find a proxy in local file")
                proxy = proxy_finder.ProxyLoader(self.api_url)
                if proxy == False:
                    logging.info("No proxy in local file or they don't work anymore")
                    proxy = proxy_finder.ProxyConnectGetMe(self.api_url)
                    if proxy == False:
                        sleep(5)
                        restart.program()
                        #ProxyBroker will be here
        else:
            logging.info("Works fine with proxy = {}".format(proxy))

    def get_updates(self, offset=None, timeout=30):
        global proxy
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        logging.info('Getting updates...')
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
            else:
                last_update = None

            return last_update
