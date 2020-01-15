import requests

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

def ProxyConnectGetMe(api_url):
    proxy_temp = requests.get("http://pubproxy.com/api/proxy?limit=5&https=true&last_check=60&format=txt")
    proxy_temp = proxy_temp.content.decode().split("\n")
    print(proxy_temp)
    for i in proxy_temp:
        proxy = {"http": "http://{}/".format(i),"https": "https://{}/".format(i)}
        print(proxy)
        try:
            response = requests.get(api_url+'getMe', timeout = 20, proxies = proxy)
        except requests.exceptions.ConnectionError:
            print("Pass")
            continue
        else:
            return proxy
    ProxyConnectGetMe(api_url)

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
