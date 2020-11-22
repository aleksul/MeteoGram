#!/usr/bin/python3.8
from asyncio import new_event_loop, set_event_loop, gather

from aiogram import Bot as aiogram_bot, Dispatcher, executor as aiogram_executor
from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import Message, CallbackQuery
from aiogram.types import ChatActions, InputFile

from proxy_helper import ProxyGrabber, check_site
from plotter import Plotter, DatabaseHandler
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
assert BOT_TOKEN is None, "Bot token was NOT set"

KB_START = ReplyKeyboardMarkup(one_time_keyboard=False,
                               resize_keyboard=True,
                               row_width=2)
KB_START.add("/now", "/graph", "/help")
KB_START2 = ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)
KB_START2.add("/now", "/graph")
KB_ADMIN = ReplyKeyboardMarkup(one_time_keyboard=False,
                               resize_keyboard=True,
                               row_width=2)
KB_ADMIN.add("/log", "/clear_log", "/back")

bt_month = InlineKeyboardButton("Месяц", callback_data="mon")  # month
bt_day = InlineKeyboardButton("День", callback_data="day")  # day
bt_3h = InlineKeyboardButton("3 часа", callback_data="180")  # 3 hours
bt_1h = InlineKeyboardButton("1 час", callback_data="060")  # 1 hour
bt_30min = InlineKeyboardButton("Полчаса", callback_data="030")  # 30 minutes
bt_15min = InlineKeyboardButton("15 минут", callback_data="015")  # 15 minutes
KB_CHOOSE_TIME = InlineKeyboardMarkup()
KB_CHOOSE_TIME.row(bt_15min, bt_30min, bt_1h)
KB_CHOOSE_TIME.row(bt_3h, bt_day)
KB_CHOOSE_TIME.row(bt_month)


async def doWeNeedProxy() -> bool:
    # internet connection test
    results = await gather(
        check_site("http://example.org/"),
        check_site(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"),
    )
    logging.info(f"Internet test results:"
                 f"example.org: {results[0]}, "
                 f"telegram: {results[1]}")
    if not results[0]:  # we dont have internet access
        raise OSError("No internet")
    elif (results[0] and
          not results[1]):  # we have internet access but no access to telegram
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
    BOT = aiogram_bot(token=BOT_TOKEN,
                      proxy=loop.run_until_complete(proxyFinder.grab()))
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
    await message.answer(
        f'Данные собраны в {now["time"].strftime("%H:%M:%S")}\n\n'
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
    for day in dates:
        BT_day = InlineKeyboardButton(day.strftime("%d.%m.%Y"),
                                      callback_data="=raw+" +
                                      day.strftime("%d-%m-%Y"))
        KB_DATES.insert(BT_day)
    await message.answer("> Просмотр исходного файла\n Выберите дату:",
                         reply_markup=KB_DATES)


@dp.callback_query_handler(lambda c: (c.data and c.data.startswith("=raw")))
async def send_raw_file(callback_query: CallbackQuery):
    await BOT.send_chat_action(callback_query.message.chat.id,
                               ChatActions.UPLOAD_DOCUMENT)
    strDate = callback_query.data.split("+")[1]
    day = datetime.strptime(strDate, "%d-%m-%Y").date()
    fi = await db.getRawDataByDay(day)
    with open(fi.name, "rb") as f:
        doc = InputFile(f, filename=strDate + ".csv")
        await callback_query.message.answer_document(doc)
    remove(fi.name)
    await callback_query.answer()


@dp.message_handler(commands=["graph"])
async def send_graph_kb(message: Message):
    await message.answer(
        "> Построение графика\n Выберите временной промежуток:",
        reply_markup=KB_CHOOSE_TIME,
    )


@dp.callback_query_handler(lambda c: (c.data and c.data.startswith("=mon")))
async def plot_graph_month(callback_query: CallbackQuery):
    code = callback_query.data[1::].split("+")
    code, parameter = code[0], code[1]
    photo: bytes
    try:
        photo = graphics.plot_month(await db.getMonthData(parameter), parameter)
    except Exception as e:
        logging.warning(f"Catched error while tring to plot month graph: "
                        f"{type(e)}: {e}")
        await callback_query.answer(text="За этот период нет данных 😔",
                                    show_alert=True)
    else:
        await callback_query.answer()
        await BOT.send_chat_action(callback_query.message.chat.id,
                                   ChatActions.UPLOAD_PHOTO)
        await callback_query.message.answer_photo(
            photo,
            caption=f"{graphics.valueToStr(parameter)} за последний месяц")


@dp.callback_query_handler(lambda c: (c.data and c.data.startswith("=day")))
# TODO: period of time chooser
async def plot_graph_day(callback_query: CallbackQuery):
    code = callback_query.data[1::].split("+")
    code, day, parameter = code[0], code[1], code[2]
    day = datetime.strptime(day, "%d-%m-%Y").date()
    try:
        photo = graphics.plot_day(await db.getDataByDay(day, parameter),
                                  parameter)
    except Exception as e:
        logging.warning(f"Catched error while tring to plot day graph: "
                        f"{type(e)}: {e}")
        await callback_query.answer(text="За этот период нет данных 😔",
                                    show_alert=True)
    else:
        await callback_query.answer()
        await BOT.send_chat_action(callback_query.message.chat.id,
                                   ChatActions.UPLOAD_PHOTO)
        await callback_query.message.answer_photo(
            photo,
            caption=f"{graphics.valueToStr(parameter)} за "
            f'{day.strftime("%d.%m.%Y")}',
        )


@dp.callback_query_handler(
    lambda c: (c.data and c.data[0:4] in ["=015", "=030", "=060", "=180"]))
async def plot_graph_minutes(callback_query: CallbackQuery):
    code = callback_query.data[1::].split("+")
    parameter, code = code[1], code[0]
    try:
        photo = graphics.plot_minutes(
            await db.getDataByTimedelta(datetime.now(),
                                        timedelta(minutes=-1 * int(code)),
                                        parameter),
            parameter,
        )
    except Exception as e:
        logging.warning(f"Catched error while tring to plot minutes graph: "
                        f"{type(e)}: {e}")
        await callback_query.answer(text="За этот период нет данных 😔",
                                    show_alert=True)
    else:
        await callback_query.answer()
        await BOT.send_chat_action(callback_query.message.chat.id,
                                   ChatActions.UPLOAD_PHOTO)
        await callback_query.message.answer_photo(
            photo,
            caption=f"{graphics.valueToStr(parameter)} за "
            f"{graphics.timeToStr(code)}",
        )


@dp.callback_query_handler(
    lambda c: (c.data and (c.data in ["015", "030", "060", "180", "mon"]
                           or c.data.startswith("day+")
                           )
               )
    )
async def add_parameter(callback_query: CallbackQuery):
    if callback_query.data == "mon" and not await db.getAllDates():
        await callback_query.answer(text="За этот период нет данных 😔",
                                    show_alert=True)
        return
    bt_pm25 = InlineKeyboardButton("Частицы PM2.5",
                                   callback_data="=" + callback_query.data +
                                   "+pm25")
    bt_pm10 = InlineKeyboardButton("Частицы PM10",
                                   callback_data="=" + callback_query.data +
                                   "+pm10")
    bt_temp = InlineKeyboardButton("Температура",
                                   callback_data="=" + callback_query.data +
                                   "+temperature")
    bt_pres = InlineKeyboardButton("Давление",
                                   callback_data="=" + callback_query.data +
                                   "+pressure")
    bt_humidity = InlineKeyboardButton("Влажность",
                                       callback_data="=" + callback_query.data +
                                       "+humidity")
    KB_PARAMETER = InlineKeyboardMarkup()
    KB_PARAMETER.row(bt_pm25, bt_pm10)
    KB_PARAMETER.row(bt_temp)
    KB_PARAMETER.row(bt_pres, bt_humidity)
    time: str
    if callback_query.data.startswith("day"):
        time = callback_query.data.split("+")[1].replace("-", ".")
    else:
        time = graphics.timeToStr(callback_query.data)
    await callback_query.message.edit_text(
        text=f"> Построение графика\n> За {time}\nВыберите параметр:",
        reply_markup=KB_PARAMETER,
    )


@dp.callback_query_handler(lambda c: (c.data and c.data == "day"))
async def select_day(callback_query: CallbackQuery):  # choose date
    KB_DATES = InlineKeyboardMarkup()
    dates = await db.getAllDates()
    if not dates:
        await callback_query.answer(text="За этот период нет данных 😔",
                                    show_alert=True)
        return
    for day in dates:
        BT_temp = InlineKeyboardButton(day.strftime("%d.%m.%Y"),
                                       callback_data="day+" +
                                       day.strftime("%d-%m-%Y"))
        KB_DATES.insert(BT_temp)
    await callback_query.message.edit_text(
        text="> Построение графика\n> За день\nВыберите дату:",
        reply_markup=KB_DATES,
    )


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
    elif message.get_command(
    ) == "/back":  # gives back standart keyboard layout
        await message.answer("Возвращаю нормальную клавиатуру 😉",
                             reply_markup=KB_START2)


if __name__ == "__main__":
    aiogram_executor.start_polling(dp, skip_updates=True)
