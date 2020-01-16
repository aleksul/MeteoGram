#!/usr/bin/env python

from bot_handler import *
from telegram_api_for_python import *
import logging

logging.basicConfig(filename='bot.log',
                    format='%(asctime)s    %(levelname)s: %(message)s',
                    datefmt='%d/%m/%Y %I:%M:%S',
                    level=logging.INFO)

logging.info("""Program started""")
token1 = "1012565455:AAGctwGzz0LRlucqZiiEIvchtLhJjd1Fqdw"
eos_bot = BotHandler(token1)
logging.info("Bot init complete!") #why it has been called several times?

key1 = KeyboardBuilder([['HI','Wassup?'],['BYE']])
key1 = key1.build()
markup1 = ReplyKeyboardMarkupBuilder(key1)
markup1 = markup1.build()

but1 = InlineButtonBuilder('кнопка 1', callback_data = '/1')
but1 = but1.build()
but2 = InlineButtonBuilder('trashbox', url = 'http://trashbox.ru')
but2 = but2.build()
but3 = InlineButtonBuilder('pay 2000р', callback_data ='pay', pay = True)
but3 = but3.build()
markup2 = InlineMarkupBuilder([[but1],[but2, but3]])
markup2 = markup2.build()

def main():  
    new_offset = None
    logging.info("Main started!")
    while True:        
        eos_bot.get_updates(new_offset)

        last_update = eos_bot.get_last_update()
        if last_update is None:
            continue
        last_update_id = last_update['update_id']
        if 'message' in last_update.keys():
            last_chat_text = last_update['message']['text']
            last_chat_id = last_update['message']['chat']['id']
            last_chat_name = last_update['message']['chat']['first_name']
        elif 'callback_query' in last_update.keys():
            last_chat_text = last_update['callback_query']['data']
            last_chat_id = last_update['callback_query']['message']['chat']['id']
            last_chat_name = last_update['callback_query']['message']['chat']['first_name']
            
        if last_chat_text.lower()=='/start':
            eos_bot.send_message(last_chat_id, 'Приветствую, {}.'.format(last_chat_name), markup = ReplyKeyboardRemove)
        elif last_chat_text.lower()=='/new':
            eos_bot.send_message(last_chat_id, 'New, {}.'.format(last_chat_name), markup = markup2)
        elif last_chat_text.lower()=='/kb':
            eos_bot.send_message(last_chat_id, 'New, {}.'.format(last_chat_name), markup = markup1)
        new_offset = last_update_id + 1

        
if __name__ == '__main__':
    main()
