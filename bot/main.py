#!/usr/bin/python3.8
import asyncio
import aiogram
import proxy_helper
from plotter import Plotter
import logging
from os import name, stat, environ
from random import shuffle
from datetime import datetime, timedelta
from io import IOBase

# path = "C:\\Projects\\tg-bot\\bot\\"  # DEBUG
path = '/code/'

logging.basicConfig(filename=f'{path}bot.log',
                    format='%(asctime)s    %(levelname)s: %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S',
                    level=logging.INFO)
logging.info('Program started')

ADMIN_ID = environ.get("ADMIN_IDs", "").split(",")
BOT_TOKEN = environ.get('BotToken', '1258153191:AAGosyTwZfoGuBPpZ7RV6jSdwPvRyVtvyTI')


async def doWeNeedProxy() -> bool:
    results = await asyncio.gather(proxy_helper.check_site('http://example.org/'), 
                                   proxy_helper.check_site(f'https://api.telegram.org/bot{BOT_TOKEN}/getMe'))
    logging.info(f'Internet test results:' 
                 f'example.org: {results[0]}, '
                 f'telegram: {results[1]}')
    if not results[0]:  # internet connection test
        raise OSError("No internet")
    elif results[0] and not results[1]:
        return True
    elif results[0] and results[1]:
        return False


KB_START = aiogram.types.ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)
KB_START.add("/now", "/graph", "/raw", "/help")
KB_START2 = aiogram.types.ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)
KB_START2.add("/now"); KB_START2.row(); KB_START2.add("/graph", "/raw")
KB_ADMIN = aiogram.types.ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True, row_width=2)
KB_ADMIN.add("/log", "/clear_log", "/back")

bt_month = aiogram.types.InlineKeyboardButton('Месяц', callback_data='+month')
bt_day = aiogram.types.InlineKeyboardButton('День', callback_data='+day')
bt_3h = aiogram.types.InlineKeyboardButton('3 часа', callback_data='+180')
bt_1h = aiogram.types.InlineKeyboardButton('1 час', callback_data='+60')
bt_30min = aiogram.types.InlineKeyboardButton('Полчаса', callback_data='+30')
bt_15min = aiogram.types.InlineKeyboardButton('15 минут', callback_data='+15')
KB_CHOOSE_TIME = aiogram.types.InlineKeyboardMarkup()
KB_CHOOSE_TIME.add(bt_15min, bt_30min, bt_1h, bt_3h, bt_day); KB_CHOOSE_TIME.row(); KB_CHOOSE_TIME.add(bt_month)

loop = asyncio.get_event_loop()
isProxyNeeded = loop.run_until_complete(doWeNeedProxy())
if isProxyNeeded:
    proxyFinder = proxy_helper.ProxyGrabber(timeout=3,
                                        filename=f'{path}proxy.dat',
                                        site_to_test=f'https://api.telegram.org/bot{BOT_TOKEN}/getMe')
    PROXY = loop.run_until_complete(proxyFinder.grab())

# graphics = Plotter(data_path='C:\\Projects\\tg-bot\\bot\\data\\')  # DEBUG
graphics = Plotter(data_path='/meteo_data')


if isProxyNeeded:
    BOT = aiogram.Bot(token=BOT_TOKEN, proxy=PROXY)
else:
    BOT = aiogram.Bot(token=BOT_TOKEN)
dp = aiogram.Dispatcher(BOT)


@dp.message_handler(commands=['start'])
async def send_welcome(message: aiogram.types.Message):
    asyncio.ensure_future(message.answer(f'Приветствую, {message.from_user.first_name}! \n'
                                         f'Я бот, который поможет тебе '
                                         f'узнать метеоданные в Троицке!', 
                                         reply_markup=KB_START))

@dp.message_handler(commands=['help'])
async def send_help(message: aiogram.types.Message):
    asyncio.ensure_future(message.answer('Все чрезвычайно просто:\n'
                                         '• для просмотра текущего состояния напиши /now\n'
                                         '• для построения графика напиши /graph\n'
                                         '• для просмотра сырого файла напиши /raw\n\n'
                                         'Интересуют подробности отображаемых измерений?\n'
                                         'Напиши /info',
                                         reply_markup=KB_START2))

@dp.message_handler(commands=["info"])
async def send_info(message: aiogram.types.Message):
    asyncio.ensure_future(message.answer('Где производится замер?\n'
                                         'Метеостанция располгается по адресу: '
                                         'г.Москва, г.Троицк, '
                                         'Сиреневый бульвар, д.1, снаружи "Точки Кипения"\n\n'
                                         'Как определяется время суток на графике дня?\n'
                                         '4:00-10:00 - утро\n'
                                         '10:00-16:00 - день\n'
                                         '16:00-22:00 - вечер\n'
                                         '22:00-4:00 - ночь\n\n'
                                         'Что такое частицы PM2.5 и PM10?\n'
                                         'Это мелкодисперсные частицы пыли, которые, '
                                         'буквально, "витают в воздухе". '
                                         'Из-за их малых размеров '
                                         '(2.5 мкм и 10 мкм соответсвенно) '
                                         'и веса они практически не осядают, '
                                         'таким образом загрязняя'
                                         ' воздух, которым мы дышим.\n'
                                         'Согласно ВОЗ, среднесуточный уровень этих частиц '
                                         'не должен быть больше 25 мкгр/м³\n'
                                         'Подробнее можно прочитать, например, здесь:\n'
                                         'https://habr.com/ru/company/tion/blog/396111/',
                                         reply_markup=KB_START2))

@dp.message_handler(commands=["graph"])
async def send_graph_kb(message: aiogram.types.Message):
    asyncio.ensure_future(message.answer('Выберите временной промежуток:',
                                         reply_markup=KB_CHOOSE_TIME))

@dp.callback_query_handler(lambda c: (c.data and c.data.startswith("+month") and c.data.rfind("=") != -1))
async def plot_graph_month(callback_query: aiogram.types.CallbackQuery):
    code = callback_query.data[1::].split("=")
    parameter, code = code[1], code[0]
    photo = graphics.plot_month(graphics.read_month(parameter), parameter)
    if photo:
        param_str = graphics.parameter_to_str(parameter).capitalize()
        asyncio.ensure_future(callback_query.message.answer_photo(photo,
                                                                    caption=f'{param_str} за последний месяц'))
        asyncio.ensure_future(callback_query.answer())
    else:
        asyncio.ensure_future(callback_query.answer(text='За этот период нет данных :pensive:',
                                                    show_alert=True))
    
@dp.callback_query_handler(lambda c: (c.data and c.data.startswith("+day") and c.data.rfind("=") != -1))
async def plot_graph_day(callback_query: aiogram.types.CallbackQuery):  # TODO: period of time chooser
    code = callback_query.data[1::].split("=")
    parameter, code = code[1], code[0]
    date = code.split("+")
    code, date = date[0], date[1]
    date = [int(i) for i in date.split("-")]
    plot_data = graphics.read_csv_timedelta(parameter, 
                                            datetime(date[2], date[1], date[0], 0, 0, 0), 
                                            datetime(date[2], date[1], date[0], 23, 59, 59))
    if plot_data:
        photo = graphics.plot_day(plot_data, parameter)
        if photo:
            param_str = graphics.parameter_to_str(parameter).capitalize()
            asyncio.ensure_future(callback_query.message.answer_photo(photo,
                                                                      caption=f'{param_str} за: '
                                                                              f'{date[0]}.{date[1]}.{date[2]}')
                                    )
            asyncio.ensure_future(callback_query.answer())
        else:
            asyncio.ensure_future(callback_query.answer(text='За этот период нет данных :pensive:',
                                                        show_alert=True))
    else:
        asyncio.ensure_future(callback_query.answer(text='За этот период нет данных :pensive:',
                                                    show_alert=True))

@dp.callback_query_handler(lambda c: (c.data and c.data.startswith("+") and c.data.rfind("=") != -1 and not c.data.startswith("+month") and not c.data.startswith("+day")))
async def plot_graph_minutes(callback_query: aiogram.types.CallbackQuery):
    code = callback_query.data[1::].split("=")
    parameter, code = code[1], code[0]
    plot_data = graphics.read_csv_timedelta(parameter, datetime.now(),
                                            datetime.now() - timedelta(minutes=int(code)))
    if plot_data:
        photo = graphics.plot_minutes(plot_data, parameter)
        if photo:
            param_str = graphics.parameter_to_str(parameter).capitalize()
            asyncio.ensure_future(callback_query.message.answer_photo(photo,
                                                                        caption=f'{param_str} за '
                                                                                f'{graphics.time_to_str(code)}'))
            asyncio.ensure_future(callback_query.answer())
        else:
            asyncio.ensure_future(callback_query.answer(text='За этот период нет данных :pensive:',
                                                        show_alert=True))
    else:
        asyncio.ensure_future(callback_query.answer(text='За этот период нет данных :pensive:',
                                                    show_alert=True))

@dp.callback_query_handler(lambda c: (c.data and c.data.startswith("+") and c.data != "+day"))
async def add_parameter(callback_query: aiogram.types.CallbackQuery):
    if callback_query.data == "+month" and not graphics.dates():
        asyncio.ensure_future(callback_query.answer(text='За этот период нет данных :pensive:',
                                                    show_alert=True))
        return
    bt_pm25      = aiogram.types.InlineKeyboardButton('Частицы PM2.5', callback_data=callback_query.data+'=PM2.5')
    bt_pm10      = aiogram.types.InlineKeyboardButton('Частицы PM10',  callback_data=callback_query.data+'=PM10')
    bt_temp      = aiogram.types.InlineKeyboardButton('Температура',   callback_data=callback_query.data+'=Temp')
    bt_pres      = aiogram.types.InlineKeyboardButton('Давление',      callback_data=callback_query.data+'=Pres')
    bt_humidity  = aiogram.types.InlineKeyboardButton('Влажность',     callback_data=callback_query.data+'=Humidity')
    KB_PARAMETER = aiogram.types.InlineKeyboardMarkup()
    KB_PARAMETER.row(bt_pm25, bt_pm10)
    KB_PARAMETER.row(bt_temp)
    KB_PARAMETER.row(bt_pres, bt_humidity)
    asyncio.ensure_future(callback_query.message.edit_text(text='Выберите параметр:', reply_markup=KB_PARAMETER))

@dp.callback_query_handler(lambda c: (c.data and c.data == '+day'))
async def select_day(callback_query: aiogram.types.CallbackQuery):
    KB_DATES = aiogram.types.InlineKeyboardMarkup()
    dates = graphics.dates()
    if dates:
        for date in dates:
            pretty_date = date.replace('-', '.')
            BT_temp = aiogram.types.InlineKeyboardButton(pretty_date, callback_data='+day+' + date)
            KB_DATES.add(BT_temp)
        asyncio.ensure_future(callback_query.message.edit_text(text='Выберите дату:', reply_markup=KB_DATES))
    else:
        asyncio.ensure_future(callback_query.answer(text='За этот период нет данных :pensive:',
                                                    show_alert=True))


@dp.message_handler(lambda msg: (str(msg.from_user.id) in ADMIN_ID), commands=["admin", "log", "clear_log", "back"])
async def admin_commands(message: aiogram.types.Message):
    if message.get_command() == "/admin":
        asyncio.ensure_future(message.answer(f'Наконец то мой дорогой админ {message.from_user.first_name} '
                                             f'добрался до раздела админских возможностей!\n\n'
                                             f'• Напишите /log для получения файла логов,'
                                             f' /clear_log для того чтобы его отчистить\n'
                                             f'• Напишите /back для '
                                             f'возврашения стандартной клавиатуры',
                                             reply_markup=KB_ADMIN))
    elif message.get_command() == "/log":
        await BOT.send_chat_action(message.chat.id, aiogram.types.ChatActions.UPLOAD_DOCUMENT)
        f = open(f'{path}bot.log', 'rb')
        doc = aiogram.types.InputFile(f, filename='log.txt')
        await message.answer_document(doc)
        f.close()
    elif message.get_command() == "/clear_log":
        with open(path + 'bot.log', 'w'):  # log clearing
            pass
        logging.info('Cleared log')
        asyncio.ensure_future(message.answer('Лог был отчищен!'))
    elif message.get_command() == "/back":
        asyncio.ensure_future(message.answer('Возвращаю нормальную клавиатуру :wink:', reply_markup=KB_START2))

if __name__ == '__main__':
    aiogram.executor.start_polling(dp, skip_updates=True)
