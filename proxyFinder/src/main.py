import asyncio
from os import environ
from icmplib import multiping
from proxylib import ProxyGrabber

DIRECTORY = environ.get("PROXY_DIR", default="./")


def doWeNeedProxy() -> bool:
    # internet connection test
    results: list = multiping(["example.org", "google.com", "api.telegram.org"])
    assert results[2].address == "api.telegram.org"
    if results[2].is_alive:  # telegram works without proxy!
        return False
    elif results[0].is_alive or results[1].is_alive:  # we need proxy :sad:
        return True
    else:  # no internet access
        raise ConnectionError("No internet connection")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if doWeNeedProxy():
        proxyFinder = ProxyGrabber(
            timeout=3,
            filename=f"{DIRECTORY}proxy.dat",
            site_to_test=f"https://api.telegram.org"
        )
        proxy = loop.run_until_complete(proxyFinder.grab())
