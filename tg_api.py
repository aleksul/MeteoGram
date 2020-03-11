import json

ReplyKeyboardRemove = '{"remove_keyboard": true, "selective": false}'
Force_Reply = '{"force_reply": true, "selective": false}'


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
    if url is None and callback_data is None and pay is None:
        raise Exception
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
