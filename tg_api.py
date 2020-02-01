import requests
import json
import asyncio
import aiohttp

ReplyKeyboardRemove = '{"remove_keyboard": true, "selective": false}'


def KeyboardButtonBuilder(button: str, request_contact=False, request_location=False):
    button = dict(button=button, request_contact=request_contact, request_location=request_location)
    return button


def KeyboardBuilder(keyboard: list, resize_keyboard=True, one_time_keyboard=True, selective=False):
    # EXAMPLES
    # a = KeyboardBuilder([['HI','Wassup?'],['BYE']], resize_keyboard=True, one_time_keyboard=True, selective=False)
    # a = KeyboardBuilder([[{'text': 'Give me contact!', 'request_contact': True}],
    # [{'text': 'Give me location!', 'request_location': True}]])
    markup = {"keyboard": keyboard, "resize_keyboard": resize_keyboard,
              "one_time_keyboard": one_time_keyboard, "selective": selective}
    return json.dumps(markup)


def InlineButtonBuilder(text: str, url=None, callback_data=None, pay=None):
    button = dict(text=text)
    if url:
        button.update(url=url)
    if callback_data:
        button.update(callback_data=callback_data)
    if pay:
        button.update(pay=pay)
    return button


def InlineMarkupBuilder(keyboard):
    markup = {"inline_keyboard": keyboard}
    return json.dumps(markup)


def Message(chat_id: str or int,
            text: str,
            parse_mode='Markdown',  # can be "HTML"
            disable_notification=None,  # boolean
            reply_to_message_id=None,  # integer
            reply_markup=None):  # InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply
    dictionary = dict(chat_id=chat_id, text=text)
    if parse_mode != 'Markdown':
        dictionary.update(parse_mode=parse_mode)
    if disable_notification:
        dictionary.update(disable_notification=disable_notification)
    if reply_to_message_id:
        dictionary.update(reply_to_message_id=reply_to_message_id)
    if reply_markup:
        dictionary.update(reply_markup=reply_markup)
    return dictionary
