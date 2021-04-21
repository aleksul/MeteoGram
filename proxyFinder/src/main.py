
if loop.run_until_complete(doWeNeedProxy()):
    proxyFinder = ProxyGrabber(
        timeout=3,
        filename=f"{DIRECTORY}proxy.dat",
        site_to_test=f"https://api.telegram.org/bot{BOT_TOKEN}/getMe",
    )
    BOT = aiogram_bot(token=BOT_TOKEN, proxy=loop.run_until_complete(proxyFinder.grab()))
else:
    pass

async def doWeNeedProxy() -> bool:
    # internet connection test
    results = await gather(
        check_site("http://example.org/"),
        check_site(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"),
    )
    logging.info(f"Internet test results:" f"example.org: {results[0]}, " f"telegram: {results[1]}")
    if not results[0]:  # we dont have internet access
        raise OSError("No internet")
    elif (results[0] and not results[1]):  # we have internet access but no access to telegram
        return True
    elif results[0] and results[1]:  # we have access to telegram without proxy!
        return False