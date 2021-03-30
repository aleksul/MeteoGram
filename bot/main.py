#!/usr/bin/python3.8
from asyncio import new_event_loop, set_event_loop, gather

from aiogram import Bot as aiogram_bot, Dispatcher, executor as aiogram_executor
from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import Message, CallbackQuery
from aiogram.types import ChatActions, InputFile

from proxy_helper import ProxyGrabber, check_site
from plotter import Plotter
from database import DatabaseHandler
import logging
from os import environ, remove
from datetime import datetime, timedelta

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

KB_START = ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True, row_width=2)
KB_START.add("/now", "/graph", "/help")
KB_START2 = ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)
KB_START2.add("/now", "/graph")
KB_ADMIN = ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True, row_width=2)
KB_ADMIN.add("/log", "/clear_log", "/back")


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


db = DatabaseHandler(db_path="sqlite:///meteo_data/data.db")
graphics = Plotter()

loop = new_event_loop()
set_event_loop(loop)

BOT: aiogram_bot
if loop.run_until_complete(doWeNeedProxy()):
    proxyFinder = ProxyGrabber(
        timeout=3,
        filename=f"{DIRECTORY}proxy.dat",
        site_to_test=f"https://api.telegram.org/bot{BOT_TOKEN}/getMe",
    )
    BOT = aiogram_bot(token=BOT_TOKEN, proxy=loop.run_until_complete(proxyFinder.grab()))
else:
    BOT = aiogram_bot(token=BOT_TOKEN)
dp = Dispatcher(BOT)


@dp.message_handler(commands=["start"])
async def send_welcome(message: Message):
    await message.answer(
        f"Приветствую, {message.from_user.first_name}! \n"
        f"Я бот, который поможет тебе "
        f"узнать метеоданные в Троицке!\n\n"
        f"Для вывода подсказки напиши /help",
        reply_markup=KB_START,
    )


@dp.message_handler(commands=["help"])
async def send_help(message: Message):
    await message.answer(
        "Все чрезвычайно просто:\n"
        "• для просмотра текущего состояния напиши /now\n"
        "• для построения графика напиши /graph\n"
        "• для просмотра сырого файла напиши /raw\n\n"
        "Интересуют подробности отображаемых измерений?\n"
        "Напиши /info",
        reply_markup=KB_START2,
    )


@dp.message_handler(commands=["info"])
async def send_info(message: Message):
    await message.answer(
        "Где производится замер?\n"
        "Метеостанция располгается по адресу: "
        "г.Москва, г.Троицк, "
        'Сиреневый бульвар, д.1, снаружи "Точки Кипения"\n\n'
        "Как определяется время суток на графике дня?\n"
        "4:00-10:00 - утро\n"
        "10:00-16:00 - день\n"
        "16:00-22:00 - вечер\n"
        "22:00-4:00 - ночь\n\n"
        "Что такое частицы PM2.5 и PM10?\n"
        "Это мелкодисперсные частицы пыли, которые, "
        'буквально, "витают в воздухе". '
        "Из-за их малых размеров "
        "(2.5 мкм и 10 мкм соответсвенно) "
        "и веса они практически не осядают, "
        "таким образом загрязняя"
        " воздух, которым мы дышим.\n"
        "Согласно ВОЗ, среднесуточный уровень этих частиц "
        "не должен быть больше 25 мкгр/м³\n"
        "Подробнее можно прочитать, например, здесь:\n"
        "https://habr.com/ru/company/tion/blog/396111/",
        reply_markup=KB_START2,
    )


@dp.message_handler(commands=["now"])
async def send_now(message: Message):
    now = await db.getLastData()
    await message.answer(f'Данные собраны в {now["time"].strftime("%H:%M:%S")}\n\n'
                         f'Температура: {now["temperature"]} °C\n'
                         f'Давление: {now["pressure"]} мм/рт.ст.\n'
                         f'Влажность: {now["humidity"]} %\n'
                         f'Частицы PM2.5: {now["pm25"]} мкгр/м³\n'
                         f'Частицы PM10: {now["pm10"]} мкгр/м³')


@dp.message_handler(commands=["raw"])
async def send_raw_kb(message: Message):
    KB_DATES = InlineKeyboardMarkup(row_width=3)
    dates = await db.getAllDates(includeToday=True)
    if len(dates) > 30:
        dates = dates[0:30]
    dates.reverse()
    for day in dates:
        BT_day = InlineKeyboardButton(day.strftime("%d.%m.%Y"),
                                      callback_data="=raw+" + day.strftime("%d-%m-%Y"))
        KB_DATES.insert(BT_day)
    await message.answer("> Просмотр исходного файла\nВыберите дату:", reply_markup=KB_DATES)


@dp.callback_query_handler(lambda c: (c.data and c.data.startswith("=raw")))
async def send_raw_file(callback_query: CallbackQuery):
    await BOT.send_chat_action(callback_query.message.chat.id, ChatActions.UPLOAD_DOCUMENT)
    strDate = callback_query.data.split("+")[1]
    day = datetime.strptime(strDate, "%d-%m-%Y").date()
    fi = await db.getRawDataByDay(day)
    with open(fi.name, "rb") as f:
        doc = InputFile(f, filename=strDate + ".csv")
        await callback_query.message.answer_document(doc)
    remove(fi.name)
    await callback_query.answer()


def isValueCorrect(value: str) -> bool:
    return value.lower() in [
        "температура",
        "давление",
        "влажность",
        "pm25",
        "pm2.5",
        "pm10",
    ]


def translateParameter(value: str) -> str:
    translation = {
        "температура": "temperature",
        "давление": "pressure",
        "влажность": "humidity",
        "pm25": "pm25",
        "pm2.5": "pm25",
        "pm10": "pm10",
    }
    return translation.get(value)


@dp.message_handler(commands=["graph"])
async def send_graph_kb(message: Message):
    data = message.text[6:].split(",")
    data = [i.strip() for i in data if i.strip()]
    if not data:
        await message.answer("После команды укажите временной промежуток"
                             "и параметр через запятую.\n\n Пример 1: "
                             "/graph час назад, сейчас, температура\n"
                             "Пример 2: /graph день, 25.05.21, влажность\n"
                             "Пример 3: /graph месяц, pm2.5")
    elif data[0] == "месяц":
        photo: bytes
        try:
            # checks
            if len(data) != 2:
                await message.answer("Запрос составлен неверно!")
                return
            if not isValueCorrect(data[1]):
                await message.answer("Значение указано неверно!\n"
                                     "Возможные варианты: температура, давление"
                                     ", влажность, pm2.5, pm10")
                return
            # graph building
            parameter = translateParameter(data[1])
            month_data = await db.getMonthData(parameter)
            photo = graphics.plot_month(month_data, parameter)
        except Exception as e:
            logging.warning(f"Plotting month graph error: {type(e)}: {e}")
            await message.answer("Невозможно построить график 😔")
        else:
            await BOT.send_chat_action(message.chat.id, ChatActions.UPLOAD_PHOTO)
            await message.answer_photo(
                photo, caption=f"{graphics.valueToStr(parameter)} за последний месяц")
    elif data[0] == "день":
        pass
    else:
        pass


@dp.message_handler(
    lambda msg: (str(msg.from_user.id) in ADMIN_ID),
    commands=["admin", "log", "clear_log", "back"],
)
async def admin_commands(message: Message):
    # handels only messages from admins, only special commands

    if message.get_command() == "/admin":
        await message.answer(
            f"Наконец то мой дорогой админ "
            f"{message.from_user.first_name} "
            f"добрался до раздела админских возможностей!\n\n"
            f"• Напишите /log для получения файла логов,"
            f" /clear_log для того чтобы его отчистить\n"
            f"• Напишите /back для "
            f"возврашения стандартной клавиатуры",
            reply_markup=KB_ADMIN,
        )
    elif message.get_command() == "/log":
        # sends log file
        await BOT.send_chat_action(message.chat.id, ChatActions.UPLOAD_DOCUMENT)
        with open(DIRECTORY + LOG_FILENAME, "rb") as f:
            doc = InputFile(f, filename="log.txt")
            await message.answer_document(doc)
    elif message.get_command() == "/clear_log":
        with open(DIRECTORY + LOG_FILENAME, "w"):  # log clearing
            pass
        logging.info("Cleared log")
        await message.answer("Лог был отчищен!")
    elif message.get_command() == "/back":  # gives back standart keyboard layout
        await message.answer("Возвращаю нормальную клавиатуру 😉", reply_markup=KB_START2)


if __name__ == "__main__":
    aiogram_executor.start_polling(dp, skip_updates=True)
