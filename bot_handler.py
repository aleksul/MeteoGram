import requests
import proxy_finder

proxy = None
    
class BotHandler:
    global proxy

    def __init__(self, token):
        global proxy
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)
        try:
            response = requests.get(self.api_url+'getMe', timeout = 15, proxies = proxy)
        except requests.exceptions.ConnectionError:
            print("None proxy is bad")
            proxy = proxy_finder.ProxyConnectGetMe(self.api_url)
                    
    def get_updates(self, offset=None, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        try:
            resp = requests.get(self.api_url + method, params, proxies = proxy)
        except Exception as err:
            print("Pull err:",err)
            restart_program()
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text, markup = None):
        params = {'chat_id': chat_id, 'text': text, 'reply_markup': markup}
        method = 'sendMessage'
        try:
            resp = requests.post(self.api_url + method, params, proxies = proxy)
        except Exception as err:
            print("Send err:",err)
            restart_program()
        return resp
        
    def get_last_update(self):
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[-1]
        else:
            last_update = None

        return last_update


