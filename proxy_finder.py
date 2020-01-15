import requests
import logging
import restart

def InternetConnection():
    response = None
    try:
        response = requests.get("http://example.org")
    except Exception as err:
        logging.critical("Here is the exception: {}. And here is the response: {}".format(type(err),response))
        restart.program()
        
def ProxyConnectGetMe(api_url):
    
    try:
        proxy_temp = requests.get("http://pubproxy.com/api/proxy?limit=5&https=true&last_check=60&format=txt")
    except requests.exceptions.ConnectionError:
        logging.critical("Holy shit, I can't even connect internet!... gona check it twice")
        InternetConnection()
    else:
        proxy_temp = proxy_temp.content.decode().split("\n")
        logging.info('Find 5 proxy: {}'.format(proxy_temp))
        for i in proxy_temp:
            proxy = {"http": "http://{}/".format(i),"https": "https://{}/".format(i)}
            logging.info("Proxy: {}".format(i))
            try:
                response = requests.get(api_url+'getMe', timeout = 20, proxies = proxy)
            except requests.exceptions.ConnectionError:
                logging.info("This one doesn't work")
                continue
            else:
                logging.info("This one is good!.. I hope")
                return proxy
        logging.warning("Found nothing... uhhh, let's try again")
        ProxyConnectGetMe(api_url)


#Never gona use this shit but here it is anyway
"""

def ProxyConnect():
    proxy_temp = requests.get("http://pubproxy.com/api/proxy?limit=5&https=true&last_check=60&format=txt")
    proxy_temp = proxy_temp.content.decode().split("\n")
    for i in proxy_temp:
        proxy = {"http": "http://{}/".format(i),"https": "https://{}/".format(i)}
        try:
            response = requests.get("http://telegram.org", timeout = 20, proxies = proxy)
        except requests.exceptions.ConnectionError:    
            continue
        else:
            return proxy
    ProxyConnect()

def ProxyConnectSocks():
    proxy_temp = requests.get("http://pubproxy.com/api/proxy?type=socks5&limit=5&last_check=60&format=txt")
    proxy_temp = proxy_temp.content.decode().split("\n")
    for i in proxy_temp:
        proxy = {"http": "socks5://{}/".format(i),"https": "socks5://{}/".format(i)}
        try:
            response = requests.get("http://telegram.org", timeout = 20, proxies = proxy)
        except requests.exceptions.ConnectionError:    
            continue
        else:
            return proxy
    ProxyConnectSocks()
"""
