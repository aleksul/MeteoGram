import asyncio
import aiohttp
from concurrent import futures
from time import clock
from os import path, stat, remove
from proxybroker import Broker
import logging


class Proxy:
    def __init__(self, site_to_test='https://telegram.org', timeout=3, filename='/home/pi/bot/proxy.txt'):
        self.site_to_test = site_to_test
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.filename = filename

    async def test1(self):
        try:
            async with aiohttp.request('GET',
                                       'http://example.org/', timeout=self.timeout) as resp:
                assert resp.status == 200
                logging.info(f"Internet seems to be connected. Response from example.org: {resp.status}")
        except Exception as err:
            logging.critical(f"Voila, the exception: {type(err)}:{err}")
            return False
        else:
            return True

    async def test2(self):
        try:
            async with aiohttp.request('GET',
                                       self.site_to_test, timeout=self.timeout) as resp:
                assert resp.status == 200
                logging.info(f"Internet seems to be connected. Response from {self.site_to_test}: {resp.status}")
        except Exception as err:
            logging.warning(f"Site {self.site_to_test} doesn't work: {type(err)}:{err}")
            return False
        else:
            return True

    async def broker_find(self):
        try:
            proxies_num = 10
            proxies = asyncio.Queue()
            broker = Broker(queue=proxies)
            await broker.find(types=['HTTPS'], limit=proxies_num)  # finds 10(==proxies_num) https proxies
            proxy_temp = []
            for i in range(proxies_num):
                proxy_temp.append(await proxies.get())  # write proxies to the list as soon as possible
        except Exception as err:  # something might go wrong
            logging.error(f"Can't find a proxy with proxy broker: {type(err)}: {err}")
            return None
        else:
            # ProxyBroker returns a string with a lot of info, but we need only proxy
            proxy_temp = [str(i)[1:-1:].split()[4] for i in proxy_temp]
            logging.info(f'Find proxies with ProxyBroker: {proxy_temp}')
            return await self.saver(proxy_temp)

    async def pub_find(self):
        try:
            async with aiohttp.request('GET',
                                       'http://pubproxy.com/api/proxy?limit=5&https=true&last_check=60&format=txt',
                                       timeout=self.timeout) as resp:
                assert resp.status == 200
                proxy_temp = await resp.text()
        except AssertionError:
            logging.warning('Probably, limit has expired')
            return None
        else:
            proxy_temp = proxy_temp.split("\n")
            logging.info(f'Find 5 proxy: {proxy_temp}')
            return await self.saver(proxy_temp)

    async def check(self, proxy: str, session):  # simply tests access to the site via proxy
        site = self.site_to_test
        proxy = "http://" + proxy
        ping = clock()
        try:
            async with session.get(site, proxy=proxy, timeout=self.timeout) as resp:
                assert resp.status == 200
        except futures._base.TimeoutError:
            logging.debug(f"Too slow proxy: {proxy}")
            return None
        except aiohttp.client_exceptions.ClientHttpProxyError:
            logging.debug(f"Bad proxy: {proxy}")
            return None
        except Exception as err:
            logging.debug(f"This proxy ({proxy}) doesn't work, exception: {type(err)}:{err}")
            return None
        else:
            ping = clock() - ping
            logging.debug(f"This one seems to be good! Proxy: {proxy} Ping: {ping}")
            proxy = {"proxy": proxy, "ping": ping}
            return proxy

    async def saver(self, proxies_to_check: list):
        async with aiohttp.ClientSession() as session:  # it's better to use one session per all requests
            # check all the proxies in parallel mode
            checked_proxies = await asyncio.wait([self.check(i, session) for i in proxies_to_check])
        # checker will return None if proxy is bad, now we need to leave only good results
        proxies_to_save = [i.result() for i in checked_proxies[0] if i.result()]
        if proxies_to_save:  # for the case, when all proxies are bad
            proxies_to_save = sorted(proxies_to_save, key=lambda m: m['ping'])  # sorts proxies to find the fastest...
            # ...and after we don't need ping argument anymore... and http:// prefix too
            proxies_to_save = [i.get('proxy')[7::] for i in proxies_to_save]
            with open(self.filename, 'a+') as f:  # write proxies to the file
                read = set(f.readlines())
                proxies_to_save = list(set(proxies_to_save) - read)  # double-write protection
                for proxy in proxies_to_save:
                    assert f.write(proxy + "\n")
                logging.info(f'Saved proxies to the file: {proxies_to_save}')
                return proxies_to_save[0]
        else:
            return None

    async def loader(self):  # almost same as saver, but it doesn't append file with new proxies
        if not path.exists(self.filename):  # Firstly, check if we have a file
            logging.warning("We don't have a file!")
            return None
        elif stat(self.filename).st_size == 0:  # Secondly, if it is not empty
            logging.warning("The file is empty!")
            return None
        with open(self.filename, "r") as f:  # Read the file and close it
            read_proxies = f.readlines()
        logging.info('Everything is ok, opened the file...')
        read_proxies = [i[:-1:] for i in read_proxies]  # delete \n
        async with aiohttp.ClientSession() as session:  # it's better to use one session per all requests
            # check all the proxies in parallel mode
            # use gather instead of wait because we need results in given order
            checked_proxies = await asyncio.gather(*[(self.check(i, session)) for i in read_proxies])
        checked_proxies = [i for i in checked_proxies if i]  # delete all None's
        if checked_proxies:  # for the case, when all proxies are bad
            checked_proxies = sorted(checked_proxies, key=lambda m: m['ping'])  # sorts proxies to find the fastest
            logging.info(f'Found fastest {checked_proxies[0]}')
            # ...and after we don't need ping argument anymore... and http:// prefix too
            checked_proxies = [i.get('proxy')[7::] for i in checked_proxies]
            with open(self.filename, "w") as f:  # open file as "writable" to delete all the content first
                for i in checked_proxies:
                    f.write(i + '\n')
            logging.debug(f'Wrote in file this list of proxies: {checked_proxies}')
            return checked_proxies[0]
        else:
            logging.warning('No working proxy in the file!')
            remove(self.filename)
            return None
