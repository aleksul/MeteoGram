#!/usr/bin/python3.8
from asyncio import new_event_loop, set_event_loop
import concurrent.futures
import functools

from aiogram import Bot as aiogram_bot, executor as aiogram_executor


from plotter import Plotter
from database import DatabaseHandler

import logging
from os import environ


DIRECTORY = "/code/"
LOG_FILENAME = "bot.log"
logging.basicConfig(
    filename=DIRECTORY + LOG_FILENAME,
    format="%(asctime)s    %(levelname)s: %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    level=logging.INFO,
)
logging.info("Program started")

ADMIN_ID = environ.get("ADMIN_IDs", "").split(",")
BOT_TOKEN = environ.get("BotToken")
assert BOT_TOKEN is not None, "Bot token was NOT set"

db = DatabaseHandler(db_path="sqlite:///meteo_data/data.db")
graphics = Plotter()

loop = new_event_loop()
set_event_loop(loop)

BOT = aiogram_bot(token=BOT_TOKEN)

async def main(loop):
    pass



if __name__ == "__main__":
    aiogram_executor.start_polling(dp, skip_updates=True)
