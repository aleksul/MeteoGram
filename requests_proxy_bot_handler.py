import requests

#proxy = {"http": "socks5://{}/".format('92.38.44.232:37430'),"https": "socks5://{}/".format('92.38.44.232:37430')}
proxy = None

def ProxyConnect(api_url):
    global proxy
    proxy_temp = requests.get("http://pubproxy.com/api/proxy?type=socks5&limit=5&https=true&last_check=60&format=txt")
    proxy_temp = proxy_temp.content.decode().split("\n")
    print(proxy_temp)
    for i in proxy_temp:
        proxy = {"http": "socks5://{}/".format(i),"https": "socks5://{}/".format(i)}
        try:
            response2 = requests.get("http://telegram.org", proxies = proxy, timeout = 10)
        except requests.exceptions.ConnectionError:
            print("pass 1")
            continue
        else:
            try:
                response = requests.get(api_url+'getMe', timeout = 20, proxies = proxy)
            except requests.exceptions.ConnectionError:
                print("pass 2")
                continue
            else:
                return True
    ProxyConnect(api_url)    
    
class BotHandler:
    global proxy

    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)
        try:
            response = requests.get(self.api_url+'getMe', timeout = 10, proxies = proxy)
        except requests.exceptions.ConnectionError:
            print("None proxy is bad")
            ProxyConnect(self.api_url)
                    
    def get_updates(self, offset=None, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params, proxies = proxy)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text, markup = None):
        params = {'chat_id': chat_id, 'text': text, 'reply_markup': markup}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params, proxies = proxy)
        return resp
        
    def get_last_update(self):
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[-1]
        else:
            last_update = None

        return last_update


