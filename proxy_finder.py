import requests
import logging
import restart
from os import path, stat, remove

def InternetConnection():
    response = None
    try:
        response = requests.get("http://example.org")
    except Exception as err:
        logging.critical("Voila, the exception: {}.".format(type(err)))
        restart.program()
    else:
        logging.info("Internet seems to be connected")
        logging.info("Here is the response from example.org: {}".format(response.status_code))
        return True
        
def ProxyConnectGetMe(api_url):
    try:
        proxy_temp = requests.get("http://pubproxy.com/api/proxy?limit=5&https=true&last_check=60&format=txt")
    except requests.exceptions.ConnectionError:
        logging.critical("Holy shit, I can't even connect internet!... gona check it twice")
        InternetConnection()
    else:
        if proxy_temp.status_code != 200:
            logging.error("Response: {}".format(proxy_temp.status_code))
            return False
        logging.info("We have almost found a proxy! Here is the response from pubproxy: {}".format(proxy_temp.status_code))
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
                ProxySaver(i)
                return proxy
        logging.warning("Found nothing... uhhh, let's try again")
        return ProxyConnectGetMe(api_url)

            
def ProxySaver(proxy):
    with open('proxy.txt', 'a+') as f:
        read = f.readlines()
        for i in read:
            i = i[:-1:]
            if i == proxy:
                logging.warning("We already have this proxy in list")
                return False
        if f.write(proxy+"\n"):
            logging.info("Succesfully written")
            f.close()
            return True
    
def ProxyLoader(api_url):
    if not path.exists("proxy.txt"):
        logging.warning("We don't have a file!")
        return False
    elif stat("proxy.txt").st_size == 0:
        logging.warning("The file is empty!")
        return False

    proxy_to_delete = []
    
    with open("proxy.txt", "r") as f:
        read = f.readlines()
        for i in read:
            i = i[:-1:]
            proxy = {"http": "http://{}/".format(i),"https": "https://{}/".format(i)}
            logging.info("Proxy from local file: {}".format(i))
            try:
                response = requests.get(api_url+'getMe', timeout = 20, proxies = proxy)
            except requests.exceptions.ConnectionError:
                logging.warning("This one doesn't work... Let's delete it in the end")
                proxy_to_delete.append(i+"\n")
                continue
            else:
                logging.info("This one works!")
                f.close()
                if proxy_to_delete:
                    logging.info("Proxies to delete: {}".format(proxy_to_delete))
                    for i in proxy_to_delete:
                        read.remove(i)
                    logging.info("New proxy list: {}".format(read))
                    remove("proxy.txt")
                    logging.info("Old file deleted")
                    with open('proxy.txt', 'a+') as f:
                        for i in read:
                            f.write(i)
                        f.close()
                    logging.info("New file ready")
                return proxy
        f.close()    
    logging.warning("No working proxy in local file... Delete it!")
    remove("proxy.txt")
    return False


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
