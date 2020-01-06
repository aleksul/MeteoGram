import requests
from time import sleep

class ReplyKeyboardMarkup:
    keyboard: list
    resize_keyboard=True
    one_time_keyboard=True
    seletcive=False

class KeyboardButton:
    text: str
    request_contact=False
    request_location=False


    

    
class BotHandler:

    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def get_updates(self, offset=None, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text):
        #params = {'chat_id': chat_id, 'text': text, "reply_markup":'{"inline_keyboard": [[{"text": "Последние операции","callback_data": "\/last"},{"text": "Баланс","callback_data": "\/balance"}]]}'}
        #params = {"chat_id": chat_id, "text": text, "reply_markup": {"keyboard": [[{"text": "Start tour"}]]} }
        #params = {'chat_id': chat_id, 'text': text, 'reply_markup': greet_kb }
        #params = {'chat_id': chat_id, 'text': text}
        #params = {'chat_id': chat_id, 'text': text, 'disable_notification': False, 'reply_markup': str(markup) }
        #params = {'chat_id': chat_id, 'text': text, 'disable_notification': False, 'reply_markup': '{"keyboard": [["Start new tour"], ["Done"]], "resize_keyboard": true, "one_time_keyboard": true, "selective": false}'} #робит блэт
        #params = {'chat_id': chat_id, 'text': text, 'reply_markup': '{"keyboard": [[{"text":"Start new tour"}]], "resize_keyboard": true, "one_time_keyboard": true, "selective": false}'}
        #params = {'chat_id': chat_id, 'text': text, 'reply_markup': None}
        method = 'sendMessage'
        print(params)
        resp = requests.post(self.api_url + method, params)
        print(resp)
        return resp
        
    def get_last_update(self):
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[-1]
        else:
            last_update = None

        return last_update

    def KeyboardBuilder(self, texts, request_contact=False,request_location=False): #example a = KeyboardBuilder([['HI','Wassup?']['BYE']])
        for i in texts:
            for j in i:
                
        
token1 = "1012565455:AAGctwGzz0LRlucqZiiEIvchtLhJjd1Fqdw"
greet_bot = BotHandler(token1)  



def main():  
    new_offset = None
    print('Start')
    while True:        
        greet_bot.get_updates(new_offset)

        last_update = greet_bot.get_last_update()
        if last_update is None:
            continue
        
        last_update_id = last_update['update_id']
        last_chat_text = last_update['message']['text']
        last_chat_id = last_update['message']['chat']['id']
        last_chat_name = last_update['message']['chat']['first_name']

        
        if last_chat_text.lower()=='/start':
            greet_bot.send_message(last_chat_id, '''Приветствую, {}.
Я - бот-помощник компании EOS Tour. Помогу Вам забронировать тур не сделав ни единого звонка!
Сейчас я еще в разработке, но совсем скоро я смогу многое!
                                   '''.format(last_chat_name))
        new_offset = last_update_id + 1

        
if __name__ == '__main__':
    main()
