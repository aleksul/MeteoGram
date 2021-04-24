from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import CallbackQuery
from aiogram.types import ChatActions, InputFile

from os import remove


DP: Dispatcher

# KEYBOARDS

KB_START = ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True, row_width=2).\
    add("/now", "/graph", "/help")
KB_START2 = ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True).\
    add("/now", "/graph")
KB_ADMIN = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2).\
    add("/log")


class Messages:
    def __init__(self, bot: Bot) -> None:
        global DP
        DP = Dispatcher(bot)
        self.dp = DP

    @staticmethod
    def isValueCorrect(value: str) -> bool:
        return value.lower() in [
            "температура",
            "давление",
            "влажность",
            "pm25",
            "pm2.5",
            "pm10"
        ]

    @staticmethod
    def translateParameter(value: str) -> str:
        translation = {
            "температура": "temperature",
            "давление": "pressure",
            "влажность": "humidity",
            "pm25": "pm25",
            "pm2.5": "pm25",
            "pm10": "pm10"
        }
        return translation.get(value)

    @DP.message_handler(commands=["start"])
    async def send_welcome(message: Message):
        await message.answer(
            f"Приветствую, {message.from_user.first_name}! \n"
            f"Я бот, который поможет тебе "
            f"узнать метеоданные в Троицке!\n\n"
            f"Для вывода подсказки напиши /help",
            reply_markup=KB_START
        )

    @DP.message_handler(commands=["help"])
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

    @DP.message_handler(commands=["info"])
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

    @DP.message_handler(commands=["now"])
    async def send_now(message: Message):
        now = await db.getLastData()
        await message.answer(f'Данные собраны в {now["time"].strftime("%H:%M:%S")}\n\n'
                            f'Температура: {now["temperature"]} °C\n'
                            f'Давление: {now["pressure"]} мм/рт.ст.\n'
                            f'Влажность: {now["humidity"]} %\n'
                            f'Частицы PM2.5: {now["pm25"]} мкгр/м³\n'
                            f'Частицы PM10: {now["pm10"]} мкгр/м³')

    @DP.message_handler(commands=["raw"])
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

    @DP.callback_query_handler(lambda c: (c.data and c.data.startswith("=raw")))
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

    async def answer_month(message: Message, data: list):
        global loop
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
            photo: bytes
            with concurrent.futures.ProcessPoolExecutor() as pool:
                photo = await loop.run_in_executor(
                    pool, functools.partial(graphics.plot_month, month_data, parameter))
        except Exception as e:
            logging.warning(f"Plotting month graph error: {type(e)}: {e}")
            await message.answer("Невозможно построить график 😔")
        else:
            await BOT.send_chat_action(message.chat.id, ChatActions.UPLOAD_PHOTO)
            await message.answer_photo(photo,
                                       caption=f"{graphics.valueToStr(parameter)} за последний месяц")

    @DP.message_handler(commands=["graph"])
    async def send_graph_kb(message: Message):
        data = message.text[6:].split(",")
        data = [i.strip() for i in data if bool(i.strip())]
        if not data:
            await message.answer("После команды укажите временной промежуток"
                                "и параметр через запятую.\n\n Пример 1: "
                                "/graph час назад, сейчас, температура\n"
                                "Пример 2: /graph день, 25.05.21, влажность\n"
                                "Пример 3: /graph месяц, pm2.5")
        elif data[0] == "месяц":
            await answer_month(message, data)
        elif data[0] == "день":
            pass
        else:
            pass

    @DP.message_handler(lambda msg: (str(msg.from_user.id) in ADMIN_ID), commands=["log"])
    async def send_log(message: Message):
        """Sends log file (only to admins)

        Args:
            message (aiogram.types.Message)
        """
        await BOT.send_chat_action(message.chat.id, ChatActions.UPLOAD_DOCUMENT)
        with open(DIRECTORY + LOG_FILENAME, "rb") as f:
            doc = InputFile(f, filename="log.txt")
            await message.answer_document(doc)
